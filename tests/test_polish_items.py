import os
import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.rag.ingest import ingestion_engine
from backend.rag.retriever import retriever

client = TestClient(app)


def test_sample_knowledge_base_documents_exist():
    """Verify all 6 SOP knowledge base documents exist on disk."""
    kb_dir = os.path.join(os.getcwd(), "knowledge_base")
    expected_sops = [
        "sop_valve_replacement.md",
        "inspection_guidelines.md",
        "sop_centrifugal_pump_maintenance.md",
        "sop_pressure_vessel_inspection.md",
        "sop_heat_exchanger_tube_inspection.md",
        "sop_electrical_isolation_loto.md",
    ]
    for sop in expected_sops:
        path = os.path.join(kb_dir, sop)
        assert os.path.exists(path), f"Expected SOP file missing: {sop}"
        assert os.path.getsize(path) > 100, f"SOP file appears empty: {sop}"


def test_sample_images_exist():
    """Verify the sample folder and its README exist. Images are optional: the old
    MVTec/FUNSD samples were non-commercial and have been removed."""
    sample_dir = os.path.join(os.getcwd(), "datasets", "sample_images")
    assert os.path.exists(os.path.join(sample_dir, "README.md")), "datasets/sample_images/README.md missing"
    for name in os.listdir(sample_dir):
        assert os.path.getsize(os.path.join(sample_dir, name)) > 0, f"Sample asset empty: {name}"


def test_api_list_sample_documents():
    """Verify GET /documents/samples/list returns only samples that exist on disk."""
    response = client.get("/documents/samples/list")
    assert response.status_code == 200
    data = response.json()
    assert "samples" in data
    sample_dir = os.path.join(os.getcwd(), "datasets", "sample_images")
    for s in data["samples"]:
        assert os.path.exists(os.path.join(sample_dir, s["filename"]))


def test_api_load_sample_document():
    """Verify POST /documents/samples/load/{filename} registers sample image into active documents."""
    samples = client.get("/documents/samples/list").json()["samples"]
    if not samples:
        pytest.skip("No licensed sample images in datasets/sample_images yet")
    filename = samples[0]["filename"]
    response = client.post(f"/documents/samples/load/{filename}")
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == filename
    assert data["document_id"].startswith("sample_")
    assert data["file_size"] > 0
    assert data["source"] == "sample_dataset"
    assert os.path.exists(data["storage_path"])


def test_api_load_missing_sample_returns_404():
    """Verify loading a sample that is not on disk returns 404."""
    response = client.post("/documents/samples/load/not_a_real_sample.png")
    assert response.status_code == 404


def test_rag_retrieval_with_new_sops():
    """Verify RAG engine can index and retrieve specific clauses from the new SOPs."""
    ingest_res = ingestion_engine.ingest_directory("knowledge_base", force_reindex=True)
    assert ingest_res["status"] == "success"
    assert ingest_res["documents_indexed"] >= 6

    # Test Pump Vibration SOP Retrieval
    pump_results = retriever.retrieve("pump vibration limits ISO 10816 overhaul", top_k=3)
    assert len(pump_results) > 0
    pump_docs = [r["metadata"].get("document", "") for r in pump_results]
    assert any("sop_centrifugal_pump_maintenance" in d for d in pump_docs)

    # Test Pressure Vessel Wall Thickness SOP Retrieval
    pv_results = retriever.retrieve("pressure vessel minimum required wall thickness ASME", top_k=3)
    assert len(pv_results) > 0
    pv_docs = [r["metadata"].get("document", "") for r in pv_results]
    assert any("sop_pressure_vessel_inspection" in d for d in pv_docs)

    # Test Electrical LOTO SOP Retrieval
    loto_results = retriever.retrieve("electrical lockout tagout arc flash category", top_k=3)
    assert len(loto_results) > 0
    loto_docs = [r["metadata"].get("document", "") for r in loto_results]
    assert any("sop_electrical_isolation_loto" in d for d in loto_docs)
