import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.documents.pid_preprocessor import pid_preprocessor
from backend.documents.ocr import ocr_engine, normalize_engineering_tag
from backend.documents.pid_symbol_detector import pid_symbol_detector
from backend.documents.pid_topology import pid_topology_extractor
from backend.documents.pid_pipeline import pid_hybrid_pipeline
from backend.agents.schemas import FactVerificationStatus


# pid.png comes from the Eng_Diagrams dataset, which has no licence, so it is not
# shipped. Point CONFIGIQ_RESEARCH_PID at a local copy to run these tests.
PID_IMAGE_PATH = os.path.abspath(os.getenv("CONFIGIQ_RESEARCH_PID", "demo_data/pid/pid.png"))
requires_research_pid = pytest.mark.skipif(
    not os.path.exists(PID_IMAGE_PATH),
    reason="Research-only P&ID (Eng_Diagrams, no licence) not present; set CONFIGIQ_RESEARCH_PID",
)


@requires_research_pid
def test_pid_preprocessor_multiscale_and_tiling():
    """Verify preprocessing produces all required representations and coordinate-preserving tiles."""
    assert os.path.exists(PID_IMAGE_PATH)
    res = pid_preprocessor.preprocess(PID_IMAGE_PATH)

    assert "original" in res
    assert "resized" in res
    assert "grayscale" in res
    assert "contrast_enhanced" in res
    assert "thresholded" in res
    assert "ocr_friendly" in res
    assert "metadata" in res

    meta = res["metadata"]
    assert meta["width"] == 2104
    assert meta["height"] == 1132
    assert meta["channels"] == 3

    # Tiling
    tiles = pid_preprocessor.generate_tiles(res["original"], tile_size=512, overlap_ratio=0.20)
    assert len(tiles) >= 12
    for t in tiles:
        assert "tile_id" in t
        assert "x" in t and "y" in t
        assert "width" in t and "height" in t
        assert t["width"] <= 512
        assert t["height"] <= 512
        assert t["image"].shape[0] == t["height"]
        assert t["image"].shape[1] == t["width"]


def test_ocr_engineering_tag_normalization():
    """Verify tolerant ISA tag normalization logic."""
    assert normalize_engineering_tag("P101") == "P-101"
    assert normalize_engineering_tag("CV101") == "CV-101"
    assert normalize_engineering_tag("PT 1027") == "PT-1027"
    assert normalize_engineering_tag("FO-1035") == "FO-1035"
    assert normalize_engineering_tag("SPG 4002") == "SPG-4002"
    assert normalize_engineering_tag("V-101") == "V-101"
    assert normalize_engineering_tag("random word") is None


@requires_research_pid
def test_ocr_extract_engineering_tags():
    """Verify OCR extracts real tags with bounding boxes from high-resolution P&ID."""
    tags = ocr_engine.extract_engineering_tags(PID_IMAGE_PATH)
    assert len(tags) >= 5

    tag_texts = [t["text"] for t in tags]
    assert any("1027" in t or "4002" in t or "1035" in t or "NOTE" in t for t in tag_texts)

    for t in tags:
        assert "text" in t
        assert "confidence" in t
        assert t["confidence"] >= 0.50
        assert "bbox" in t
        assert len(t["bbox"]) == 4
        assert t["source"] == "ocr"


@requires_research_pid
def test_symbol_detector_classification_and_unknown():
    """Verify deterministic symbol classifier recognizes canonical symbols and returns UNKNOWN for noise."""
    # Blank/noise image -> should be UNKNOWN or confidence < threshold
    blank = np.zeros((100, 100), dtype=np.uint8)
    res_blank = pid_symbol_detector.classify_isolated_symbol(blank)
    assert res_blank["class"] == "UNKNOWN" or res_blank["is_known"] is False

    # Diagram detection
    symbols = pid_symbol_detector.detect_symbols_in_diagram(PID_IMAGE_PATH)
    assert len(symbols) >= 10
    categories = [s["category"] for s in symbols]
    assert "valve" in categories or "instrument_bubble" in categories or "component" in categories


@requires_research_pid
def test_topology_line_and_connectivity_extraction():
    """Verify topological extraction of process lines, dashed lines, and graph nodes/edges."""
    tags = ocr_engine.extract_engineering_tags(PID_IMAGE_PATH)
    symbols = pid_symbol_detector.detect_symbols_in_diagram(PID_IMAGE_PATH)
    topology = pid_topology_extractor.extract_topology(PID_IMAGE_PATH, detected_tags=tags, detected_symbols=symbols)

    assert "nodes" in topology
    assert "edges" in topology
    assert "statistics" in topology
    assert len(topology["nodes"]) >= 10
    assert len(topology["edges"]) >= 5
    assert topology["intersections_count"] > 0
    assert topology["process_segments_count"] > 0
    assert topology["has_dashed_lines"] is True


@requires_research_pid
@pytest.mark.asyncio
async def test_pid_hybrid_pipeline_end_to_end():
    """Verify full hybrid pipeline generates complete structured P&ID context."""
    ctx = await pid_hybrid_pipeline.analyze(PID_IMAGE_PATH, query="What valves and instrument tags exist?")

    assert "equipment" in ctx
    assert "valves" in ctx
    assert "instruments" in ctx
    assert "connections" in ctx
    assert "ocr_tags" in ctx
    assert "detected_symbols" in ctx
    assert "uncertain_items" in ctx
    assert "pipeline_latency_sec" in ctx
    assert ctx["pipeline_latency_sec"] < 15.0

    assert len(ctx["valves"]) > 0
    assert len(ctx["ocr_tags"]) > 0
    assert len(ctx["connections"]) > 0


def test_granular_verification_statuses():
    """Verify granular 6 verification statuses and backward compatibility."""
    assert FactVerificationStatus.SUPPORTED == FactVerificationStatus.SUPPORTED_BY_IMAGE
    assert FactVerificationStatus.SUPPORTED == FactVerificationStatus.SUPPORTED_BY_OCR
    assert FactVerificationStatus.SUPPORTED == FactVerificationStatus.SUPPORTED_BY_RAG
    assert FactVerificationStatus.UNSUPPORTED != FactVerificationStatus.SUPPORTED
