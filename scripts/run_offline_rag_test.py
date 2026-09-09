import os
import sys
import json
import time
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag.ingest import KnowledgeIngestionEngine
from backend.rag.retriever import RAGRetriever
from backend.rag.embeddings import OllamaEmbedder
from backend.rag.vector_store import LocalVectorStore
from backend.llm.ollama_provider import OllamaLLMProvider
from backend.models.schemas import LLMGenerateRequest
from backend.services.network_monitor import network_monitor

RESULTS_DIR = os.path.join(os.getcwd(), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

async def main():
    print("=" * 60)
    print("PHASE 7: RAG OFFLINE VERIFICATION")
    print("=" * 60)

    # 1. Initialize local embedder with nomic-embed-text
    embedding_model = "nomic-embed-text:latest"
    print(f"[1] Initializing Local Embedder: {embedding_model} via Ollama...")
    embedder = OllamaEmbedder(model_name="nomic-embed-text")

    # 2. Local vector database
    vector_store_path = os.path.join(os.getcwd(), "outputs", "storage", "vector_store.json")
    print(f"[2] Initializing Local Vector Database: {vector_store_path}")
    store = LocalVectorStore(persistence_path=vector_store_path)

    # 3. Ensure knowledge base is ingested locally
    ingestion_engine = KnowledgeIngestionEngine(store=store, embedder=embedder)
    for kb_dir_name in ["knowledge_base", "demo_data/knowledge_base"]:
        kb_path = os.path.join(os.getcwd(), kb_dir_name)
        if os.path.exists(kb_path):
            res = ingestion_engine.ingest_directory(kb_path, force_reindex=False)
            print(f"    Knowledge Directory '{kb_dir_name}': {res.get('documents_indexed', 0)} docs indexed.")

    print(f"    Total Chunks in Local Vector Database: {store.count()}")
    assert store.count() > 0, "Vector store is empty! Check knowledge_base directory."

    # 4. Execute real RAG retrieval
    query = "What is the recommended inspection and maintenance procedure for a centrifugal pump showing elevated vibration according to ISO 10816?"
    print(f"\n[3] Executing Offline Query: '{query}'")
    retriever = RAGRetriever(store=store, embedder=embedder)
    
    t0 = time.time()
    retrieved_chunks = retriever.retrieve(query=query, top_k=3)
    retrieval_ms = round((time.time() - t0) * 1000, 2)
    print(f"    Retrieved {len(retrieved_chunks)} documents in {retrieval_ms}ms")

    retrieved_docs_meta = []
    for c in retrieved_chunks:
        doc_info = {
            "id": c.get("id"),
            "document": c.get("document"),
            "page": c.get("page", 1),
            "score": round(float(c.get("score", 0.0)), 4),
            "snippet": c.get("content", "")[:200]
        }
        retrieved_docs_meta.append(doc_info)
        print(f"      - [{doc_info['score']}] {doc_info['document']} (Page {doc_info['page']})")

    assert len(retrieved_chunks) > 0, "No documents retrieved!"

    # 5. Local Llama LLM synthesis
    llm_model = "llama3:latest"
    print(f"\n[4] Generating answer with local Llama ({llm_model})...")
    context_text = "\n\n".join([f"Source [{c.get('document')}]:\n{c.get('content')}" for c in retrieved_chunks])
    rag_prompt = (
        f"You are an industrial machinery reliability engineer.\n"
        f"Answer the user question using ONLY the retrieved standard operating procedures and manuals below.\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        f"QUESTION:\n{query}\n\n"
        f"Provide a concise, direct answer citing the retrieved document and standard."
    )

    ollama = OllamaLLMProvider()
    req = LLMGenerateRequest(
        prompt=rag_prompt,
        model=llm_model,
        temperature=0.1,
        max_tokens=500
    )

    t_gen_start = time.time()
    gen_resp = await ollama.generate(req)
    gen_duration = round(time.time() - t_gen_start, 2)
    answer_text = gen_resp.text.strip()
    print(f"    Llama3 answered in {gen_duration}s:\n")
    print(f"--- ANSWER --- \n{answer_text}\n--------------")

    # 6. Check network status
    telemetry = network_monitor.get_telemetry()
    net_status = "LOCAL_ONLY" if telemetry.air_gap_compliant else "NON_LOCAL_DETECTED"
    passed = (
        len(retrieved_chunks) > 0 and
        len(answer_text) > 30 and
        telemetry.air_gap_compliant
    )

    # 7. Record result
    result_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query,
        "embedding_model": embedding_model,
        "vector_database": "LocalVectorStore (JSON / outputs/storage/vector_store.json)",
        "llm_model": llm_model,
        "retrieved_documents": retrieved_docs_meta,
        "answer": answer_text,
        "latencies": {
            "retrieval_ms": retrieval_ms,
            "generation_seconds": gen_duration
        },
        "network_status": net_status,
        "external_network_calls": telemetry.external_ai_calls,
        "pass/fail": "PASS" if passed else "FAIL"
    }

    out_path = os.path.join(RESULTS_DIR, "offline_rag_test.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result_record, f, indent=2)

    print(f"\n[5] Saved offline RAG test record to: {out_path}")
    print(f"    Verdict: {result_record['pass/fail']}")
    assert passed, f"RAG offline test failed: {result_record}"

if __name__ == "__main__":
    asyncio.run(main())
