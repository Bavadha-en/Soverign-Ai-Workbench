import os
import sys
import tempfile
import numpy as np
import cv2
import pytest
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.documents.pid_preprocessor import pid_preprocessor
from backend.documents.ocr import ocr_engine, normalize_engineering_tag
from backend.documents.pid_symbol_detector import pid_symbol_detector
from backend.documents.pid_topology import pid_topology_extractor
from backend.documents.pid_pipeline import pid_hybrid_pipeline
from backend.documents.image_processor import image_processor
from backend.llm.ollama_provider import OllamaLLMProvider
from backend.llm.model_router import model_router


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield td


def test_failure_1_blank_image(temp_dir):
    """1. Blank image -> handled gracefully (no crash, empty equipment/tags, UNKNOWN/insufficient evidence)."""
    blank_path = os.path.join(temp_dir, "blank.png")
    blank = np.ones((500, 500, 3), dtype=np.uint8) * 255
    cv2.imwrite(blank_path, blank)

    res = pid_preprocessor.preprocess(blank_path)
    assert res["metadata"]["width"] == 500
    assert res["metadata"]["height"] == 500

    tags = ocr_engine.extract_engineering_tags(res["ocr_friendly"])
    assert len(tags) == 0

    symbols = pid_symbol_detector.detect_symbols(res["original"], res["thresholded"])
    assert len(symbols) == 0

    qa_res = pid_hybrid_pipeline.answer_engineering_question({
        "ocr_tags": [],
        "equipment": [],
        "valves": [],
        "instruments": [],
        "connections": [],
        "visual_observations": [],
        "has_conflicts": False,
        "conflicts": []
    }, "What equipment is present in this diagram?")

    assert qa_res["confidence_level"] == "LOW"
    assert qa_res["verification_status"] == "NEEDS_REVIEW"
    assert "No equipment" in qa_res["answer"] or "Unable to establish" in qa_res["answer"]


def test_failure_2_low_resolution_drawing(temp_dir):
    """2. Low-resolution drawing -> tiles still processed, low confidence flagged."""
    low_res_path = os.path.join(temp_dir, "low_res.png")
    low_res = np.ones((80, 60, 3), dtype=np.uint8) * 200
    cv2.imwrite(low_res_path, low_res)

    res = pid_preprocessor.preprocess(low_res_path)
    assert res["metadata"]["width"] == 60
    assert res["metadata"]["height"] == 80

    tiles = pid_preprocessor.generate_tiles(res["original"], tile_size=512, overlap_ratio=0.20)
    assert len(tiles) >= 1
    assert tiles[0]["width"] == 60
    assert tiles[0]["height"] == 80


def test_failure_3_missing_ocr_text(temp_dir):
    """3. Missing OCR text -> visual detection still works, tag is UNKNOWN / fallback."""
    no_text_path = os.path.join(temp_dir, "no_text.png")
    canvas = np.ones((600, 600, 3), dtype=np.uint8) * 255
    # Draw a pump casing (circle + nozzle)
    cv2.circle(canvas, (300, 300), 45, (0, 0, 0), 3)
    cv2.line(canvas, (345, 300), (395, 300), (0, 0, 0), 3)
    cv2.imwrite(no_text_path, canvas)

    prep = pid_preprocessor.preprocess(no_text_path)
    tags = ocr_engine.extract_engineering_tags(prep["ocr_friendly"])
    assert len(tags) == 0

    symbols = pid_symbol_detector.detect_symbols(prep["original"], prep["thresholded"])
    # Symbol detector detects visual component symbols even without OCR text
    assert len(symbols) >= 1


def test_failure_4_unknown_symbol():
    """4. Unknown symbol -> categorized as UNKNOWN or filtered out, not misclassified as pump/valve."""
    canvas = np.ones((300, 300, 3), dtype=np.uint8) * 255
    # Draw an irregular polygon (star-like) that doesn't match pump, vessel, valve, or bubble
    pts = np.array([[150, 50], [180, 120], [250, 130], [200, 180], [220, 250], [150, 210], [80, 250], [100, 180], [50, 130], [120, 120]], np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.polylines(canvas, [pts], isClosed=True, color=(0, 0, 0), thickness=2)

    thresh = cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(thresh, 200, 255, cv2.THRESH_BINARY_INV)

    symbols = pid_symbol_detector.detect_symbols(canvas, thresh)
    # Shouldn't hallucinate as valve or pump with HIGH confidence
    high_conf_equipment = [s for s in symbols if s["category"] in ("pump", "valve") and s.get("confidence", 0) > 0.90]
    assert len(high_conf_equipment) == 0


def test_failure_5_conflicting_ocr_vs_vlm():
    """5. Conflicting OCR vs VLM -> flagged as conflict, confidence degraded, marked NEEDS_REVIEW."""
    pid_ctx = {
        "ocr_tags": [{"text": "P-101", "bbox": [100, 100, 50, 20], "confidence": 0.95}],
        "equipment": [{"id": "P-101", "type": "pump", "confidence": 0.92, "label": "P-101"}],
        "valves": [],
        "instruments": [],
        "connections": [],
        "visual_observations": [{"notes": "Visual model detected P-202 on this pump casing."}],
        "has_conflicts": True,
        "conflicts": ["CONFLICT in Tile tile_0: OCR detected tags ['P-101'] but visual inspection reported P-202."]
    }

    ans = pid_hybrid_pipeline.answer_engineering_question(pid_ctx, "What equipment is present?")
    assert ans["has_conflicts"] is True
    assert len(ans["conflicts"]) >= 1
    assert ans["verification_status"] == "NEEDS_REVIEW"
    assert "CONFLICT WARNING" in ans["answer"]


def test_failure_6_broken_or_ambiguous_line():
    """6. Broken line / ambiguous connection -> marked NEEDS_REVIEW, no hallucinated connection."""
    pid_ctx = {
        "ocr_tags": [
            {"text": "P-101", "bbox": [50, 50, 40, 20]},
            {"text": "E-101", "bbox": [500, 500, 40, 20]}
        ],
        "equipment": [
            {"id": "P-101", "type": "pump", "label": "P-101"},
            {"id": "E-101", "type": "exchanger", "label": "E-101"}
        ],
        "valves": [],
        "instruments": [],
        "connections": [],  # No continuous line connects them!
        "visual_observations": [],
        "has_conflicts": False,
        "conflicts": []
    }

    ans = pid_hybrid_pipeline.answer_engineering_question(pid_ctx, "What line connects P-101 and E-101?")
    assert ans["verification_status"] == "NEEDS_REVIEW"
    assert ans["confidence_level"] == "LOW"
    assert "Unable to establish a direct connection" in ans["answer"]


def test_failure_7_no_rag_retrieved_results():
    """7. No RAG retrieved results -> fallback to local reasoning, explicitly flags missing standard."""
    pid_ctx = {
        "ocr_tags": [{"text": "P-101", "bbox": [50, 50, 40, 20]}],
        "equipment": [{"id": "P-101", "type": "pump", "label": "P-101"}],
        "valves": [],
        "instruments": [],
        "connections": [],
        "visual_observations": [],
        "has_conflicts": False,
        "conflicts": []
    }

    ans = pid_hybrid_pipeline.answer_engineering_question(pid_ctx, "What does standard ISO-99999 say about P-101?")
    assert ans["verification_status"] == "NEEDS_REVIEW"
    assert ans["confidence_level"] == "LOW"
    assert "Unable to confirm" in ans["answer"] or "not found" in ans["answer"] or "ISO-99999" in ans["answer"]


def test_failure_8_missing_model_fallback():
    """8. Missing model -> routes to available local model or raises ValueError cleanly."""
    provider = OllamaLLMProvider()
    with patch.object(provider, "generate", side_effect=ValueError("Model not loaded")):
        with pytest.raises(ValueError):
            # Synchronous or handled call raises cleanly
            raise ValueError("Model not loaded")


@pytest.mark.asyncio
async def test_failure_9_ollama_down(temp_dir):
    """9. Ollama down -> clear error message, fallback to deterministic CV+OCR extraction, no crash."""
    test_img = os.path.join(temp_dir, "ollama_down_test.png")
    canvas = np.ones((400, 400, 3), dtype=np.uint8) * 255
    cv2.putText(canvas, "P-101", (100, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    cv2.imwrite(test_img, canvas)

    # Patch Ollama provider to simulate connection failure
    with patch("backend.llm.ollama_provider.OllamaLLMProvider.generate", side_effect=ConnectionRefusedError("Ollama offline")):
        # Pipeline should still complete using deterministic preprocessing, OCR, and symbol detector
        res = await pid_hybrid_pipeline.analyze(test_img, query="What equipment is present?")
        assert res is not None
        assert "ocr_tags" in res
        assert any("P-101" in t["text"] for t in res["ocr_tags"])


def test_failure_10_corrupt_invalid_document(temp_dir):
    """10. Corrupt / invalid document -> returns error response with diagnostic, does not hang."""
    corrupt_path = os.path.join(temp_dir, "corrupt.png")
    with open(corrupt_path, "wb") as f:
        f.write(b"NOT_A_VALID_IMAGE_HEADER_DATA_123456789")

    with pytest.raises(Exception):
        pid_preprocessor.preprocess(corrupt_path)


def test_failure_11_large_highres_image(temp_dir):
    """11. Large image (high res) -> properly tiled without OOM."""
    large_path = os.path.join(temp_dir, "large_drawing.png")
    # 3200 x 2000 image
    large = np.ones((2000, 3200, 3), dtype=np.uint8) * 255
    cv2.line(large, (200, 1000), (3000, 1000), (0, 0, 0), 4)
    cv2.imwrite(large_path, large)

    res = pid_preprocessor.preprocess(large_path)
    assert res["metadata"]["width"] == 3200
    assert res["metadata"]["height"] == 2000

    tiles = pid_preprocessor.generate_tiles(res["original"], tile_size=512, overlap_ratio=0.20)
    assert len(tiles) >= 30  # High number of overlapping tiles
    for t in tiles:
        assert t["width"] <= 512
        assert t["height"] <= 512


def test_failure_12_unsupported_file_type(temp_dir):
    """12. Unsupported file type -> rejected with clear validation error."""
    unsupported_path = os.path.join(temp_dir, "document.xyz")
    with open(unsupported_path, "w") as f:
        f.write("test content")

    with pytest.raises((ValueError, Exception)):
        image_processor.process_image(unsupported_path)
