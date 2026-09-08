import io
import os
import sys
import pytest
from PIL import Image
from fastapi.testclient import TestClient

# Ensure ConfigIQ root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from backend.documents.image_processor import ImageProcessor, image_processor
from backend.documents.pdf_processor import PDFProcessor, pdf_processor
from backend.documents.ocr import OCREngine, ocr_engine
from backend.rag.chunker import TextChunker, chunker
from backend.rag.embeddings import LocalFallbackEmbedder, OllamaEmbedder, get_embedder
from backend.rag.vector_store import LocalVectorStore, cosine_similarity
from backend.rag.ingest import KnowledgeIngestionEngine
from backend.rag.retriever import RAGRetriever
from backend.models.schemas import LLMGenerateRequest

client = TestClient(app)


# 1. Image Processor Tests
def test_image_processor_metadata_and_base64():
    """Verify local image processor metadata extraction and base64 serialization."""
    img = Image.new("RGB", (320, 240), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    raw_bytes = buf.getvalue()

    metadata = image_processor.process_image(raw_bytes)
    assert metadata["width"] == 320
    assert metadata["height"] == 240
    assert metadata["format"] == "PNG"
    assert metadata["aspect_ratio"] == round(320 / 240, 3)

    b64_str = image_processor.image_to_base64(raw_bytes)
    assert isinstance(b64_str, str)
    assert len(b64_str) > 50

    enhanced = image_processor.enhance_for_inspection(raw_bytes, contrast_factor=1.8)
    assert len(enhanced) > 0


# 2. PDF Processor Tests
def test_pdf_processor_text_extraction():
    """Verify PDF processor extracts pages and text."""
    # Create simple valid PDF in memory using pypdf
    import pypdf
    writer = pypdf.PdfWriter()
    writer.add_blank_page(width=300, height=300)
    buf = io.BytesIO()
    writer.write(buf)
    pdf_bytes = buf.getvalue()

    res = pdf_processor.process_pdf(pdf_bytes)
    assert res["pages"] == 1
    assert "total_chars" in res
    assert len(res["pages_data"]) == 1


# 3. OCR Engine Tests
def test_ocr_engine_processing():
    """Verify OCR engine gracefully handles images and returns inspection details."""
    img = Image.new("RGB", (200, 100), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    text = ocr_engine.perform_ocr(buf.getvalue())
    assert isinstance(text, str)
    assert len(text) > 0


# 4. Text Chunker Tests
def test_text_chunker_sliding_window():
    """Verify text chunker splits text with metadata and overlap."""
    sample_text = (
        "Industrial pipeline inspection showed severe cavitation on control valve CV-102. "
        "The wall thickness measured 3.2mm versus nominal 5.0mm. "
        "Replacement per SOP-M-402 is urgently recommended before high pressure testing."
    )
    chunks = chunker.chunk_text(sample_text, document_name="valve_report.pdf", page=1)
    assert len(chunks) >= 1
    first_chunk = chunks[0]
    assert "id" in first_chunk
    assert first_chunk["metadata"]["document"] == "valve_report.pdf"
    assert first_chunk["metadata"]["page"] == 1
    assert "CV-102" in first_chunk["content"]


# 5. Local Vector Store & Cosine Similarity
def test_cosine_similarity_and_vector_store():
    """Verify vector math and top-k semantic retrieval."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]

    assert round(cosine_similarity(v1, v2), 4) == 1.0
    assert round(cosine_similarity(v1, v3), 4) == 0.0

    test_store_path = os.path.join("outputs", "storage", "test_vector_store.json")
    store = LocalVectorStore(persistence_path=test_store_path)
    store.clear()

    docs = [
        {"id": "doc1", "content": "Control valve replacement procedure", "metadata": {"document": "sop1.pdf", "page": 1}},
        {"id": "doc2", "content": "Pump electrical motor wiring diagram", "metadata": {"document": "sop2.pdf", "page": 2}},
    ]
    embeddings = [
        [1.0, 0.2, 0.0],
        [0.1, 0.9, 0.8],
    ]

    added = store.add_documents(docs, embeddings)
    assert added == 2
    assert store.count() == 2

    # Query matching doc1
    results = store.search(query_embedding=[0.9, 0.1, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0]["id"] == "doc1"
    assert results[0]["score"] > 0.8

    # Clean up test store
    store.clear()


# 6. Local Embedder Tests
def test_local_embedders():
    """Verify local embedder vector generation."""
    embedder = LocalFallbackEmbedder(dimension=128)
    v1 = embedder.embed_query("corroded valve inspection")
    assert len(v1) == 128
    # Test normalization
    norm = sum(x * x for x in v1)
    assert abs(norm - 1.0) < 1e-4

    texts = ["Pipe maintenance", "Turbine overhaul"]
    vecs = embedder.embed_texts(texts)
    assert len(vecs) == 2
    assert len(vecs[0]) == 128


# 7. Knowledge Ingest and Search API Endpoints
def test_knowledge_api_ingest_and_search():
    """Verify /knowledge/ingest and /knowledge/search endpoints."""
    ingest_resp = client.post("/knowledge/ingest", json={
        "directory_path": "knowledge_base",
        "force_reindex": True
    })
    assert ingest_resp.status_code == 200
    data = ingest_resp.json()
    assert data["status"] == "success"
    assert data["documents_indexed"] >= 1

    search_resp = client.post("/knowledge/search", json={
        "query": "corroded control valve CV-102 replacement procedure",
        "top_k": 2
    })
    assert search_resp.status_code == 200
    s_data = search_resp.json()
    assert s_data["query"] == "corroded control valve CV-102 replacement procedure"
    assert len(s_data["results"]) > 0
    top_hit = s_data["results"][0]
    assert "CV-102" in top_hit["content"] or "valve" in top_hit["content"].lower()


# 8. Multimodal Schema Support
def test_multimodal_request_schema():
    """Verify LLMGenerateRequest accepts images payload for multimodal VLM tasks."""
    req = LLMGenerateRequest(
        prompt="Inspect the gauge reading in this image.",
        model="moondream",
        images=["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="]
    )
    assert len(req.images) == 1
