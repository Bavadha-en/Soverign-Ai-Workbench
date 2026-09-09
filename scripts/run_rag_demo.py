import os
import sys
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag.ingest import KnowledgeIngestionEngine
from backend.rag.retriever import RAGRetriever
from backend.rag.embeddings import OllamaEmbedder
from backend.rag.vector_store import LocalVectorStore

RESULTS_DIR = os.path.join(os.getcwd(), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

print("[PHASE 4] Initializing Sovereign RAG Ingestion & Verification...")

# Use real nomic-embed-text embedder
embedder = OllamaEmbedder(model_name="nomic-embed-text")
vector_store_path = os.path.join(os.getcwd(), "outputs", "storage", "vector_store.json")
store = LocalVectorStore(persistence_path=vector_store_path)

ingestion_engine = KnowledgeIngestionEngine(store=store, embedder=embedder)

# Ingest both knowledge_base and demo_data/knowledge_base
kb_dirs = ["knowledge_base", "demo_data/knowledge_base"]
ingest_stats = []

for d in kb_dirs:
    full_path = os.path.join(os.getcwd(), d)
    if os.path.exists(full_path):
        res = ingestion_engine.ingest_directory(full_path, force_reindex=False)
        ingest_stats.append({"directory": d, "result": res})
        print(f"Ingested {d}: {res['documents_indexed']} docs, {res['chunks_created']} chunks. Total store: {res['total_indexed_chunks']}")

# Now execute real query retrieval test
query = "What is the recommended inspection/maintenance procedure for a centrifugal pump showing elevated vibration?"
print(f"\nExecuting Retrieval Query: '{query}'")

retriever = RAGRetriever(store=store, embedder=embedder)
start_t = time.time()
retrieval_results = retriever.retrieve(query=query, top_k=5)
retrieval_duration_ms = round((time.time() - start_t) * 1000, 2)

formatted_results = []
for r in retrieval_results:
    formatted_results.append({
        "chunk_id": r.get("id"),
        "source_document": r.get("document"),
        "page": r.get("page", 1),
        "relevance_score": r.get("score"),
        "content_snippet": r.get("content", "")[:300] + "...",
        "full_content": r.get("content", "")
    })

print(f"\nRetrieved {len(formatted_results)} chunks in {retrieval_duration_ms}ms:")
for i, item in enumerate(formatted_results, 1):
    print(f"  [{i}] Doc: {item['source_document']} | Score: {item['relevance_score']} | Chunk: {item['chunk_id']}")

# Verification checks
has_pump_sop = any("pump" in item["source_document"].lower() for item in formatted_results)
has_iso_thresholds = any("10816" in item["full_content"] or "vibration" in item["full_content"].lower() for item in formatted_results)
has_valid_scores = all(item["relevance_score"] is not None and item["relevance_score"] > 0 for item in formatted_results)

rag_verification = {
    "status": "PASS" if (has_pump_sop and has_iso_thresholds and has_valid_scores) else "FAIL",
    "query": query,
    "embedder_model": "nomic-embed-text:latest via Ollama (100% localhost)",
    "vector_store_type": "LocalVectorStore (Cosine Similarity)",
    "total_indexed_chunks": store.count(),
    "retrieval_latency_ms": retrieval_duration_ms,
    "top_chunks": formatted_results,
    "grounding_checks": {
        "pump_sop_retrieved": has_pump_sop,
        "vibration_thresholds_present": has_iso_thresholds,
        "valid_positive_cosine_scores": has_valid_scores
    }
}

out_file = os.path.join(RESULTS_DIR, "rag_demo.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(rag_verification, f, indent=2)

print(f"\nRAG verification result saved to {out_file}. Status: {rag_verification['status']}")
