import os
import sys
import json
import time
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.documents.pid_pipeline import pid_hybrid_pipeline
from backend.rag.retriever import retriever
from backend.rag.vector_store import LocalVectorStore
from backend.rag.embeddings import OllamaEmbedder
from backend.llm.ollama_provider import OllamaLLMProvider
from backend.models.schemas import LLMGenerateRequest
from backend.agents.verifier import verifier
from backend.services.network_monitor import network_monitor

RESULTS_DIR = os.path.join(os.getcwd(), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

async def main():
    print("=" * 60)
    print("PHASE 8: REAL P&ID OFFLINE PIPELINE EXECUTION")
    print("=" * 60)

    pid_path = os.path.abspath("demo_data/pid/pid.png")
    assert os.path.exists(pid_path), f"P&ID image not found at {pid_path}"

    query = "Analyze the piping connections and instrument tags between the inlet flow orifice FO-1035 and pressure indicator PI-1027."
    print(f"\n[1] P&ID Image: {pid_path}")
    print(f"    Target Query: {query}")

    # 1. Real Hybrid Pipeline: preprocessing -> tiling -> RapidOCR -> symbol detection -> topology -> Moondream
    print("\n[2] Executing P&ID Hybrid Pipeline (Preprocessing -> Tiling -> RapidOCR -> Symbols -> Topology -> Moondream)...")
    start_pipe = time.time()
    pid_context = await pid_hybrid_pipeline.analyze(
        image_source=pid_path,
        query=query,
        use_vlm_disambiguation=True
    )
    pipe_duration = round(time.time() - start_pipe, 2)

    print(f"    Completed in {pipe_duration}s")
    print(f"    - Extracted OCR Tags ({len(pid_context['ocr_tags'])}): {[t['text'] for t in pid_context['ocr_tags'][:8]]}")
    print(f"    - Detected Symbols ({len(pid_context['detected_symbols'])}): {[s.get('symbol_type', s.get('category', 'symbol')) for s in pid_context['detected_symbols'][:6]]}")
    print(f"    - Topology Nodes: {len(pid_context['equipment']) + len(pid_context['valves']) + len(pid_context['instruments'])}")
    print(f"    - Connections (Edges): {len(pid_context['connections'])}")
    print(f"    - Targeted VLM Observations: {len(pid_context['visual_observations'])}")

    # 2. Local RAG retrieval
    print("\n[3] Retrieving Governing Standards from Local RAG Vector Store...")
    start_rag = time.time()
    rag_chunks = retriever.retrieve("ISA-5.1 instrument tags, orifice plates, pressure indicators, and piping connectivity", top_k=3)
    rag_duration = round(time.time() - start_rag, 2)
    print(f"    Retrieved {len(rag_chunks)} chunks in {rag_duration}s:")
    for c in rag_chunks:
        print(f"      - {c.get('document')} (Page {c.get('page', 1)})")

    rag_sources = [
        {"document": c.get("document"), "page": c.get("page", 1), "snippet": c.get("content", "")[:200]}
        for c in rag_chunks
    ]

    # 3. Local Llama Reasoning with Tripartite Grounding
    print("\n[4] Performing Tripartite Grounded Synthesis using Local Llama3...")
    structured_context_str = json.dumps({
        "ocr_tags": [t["text"] for t in pid_context["ocr_tags"]],
        "valves": [v["label"] for v in pid_context["valves"]],
        "instruments": [i["label"] for i in pid_context["instruments"]],
        "equipment": [e["label"] for e in pid_context["equipment"]],
        "connections_sample": pid_context["connections"][:10],
        "vlm_observations": pid_context["visual_observations"]
    }, indent=2)

    rag_context_str = "\n\n".join([f"[{c.get('document')}]:\n{c.get('content')}" for c in rag_chunks])

    llama_prompt = f"""You are a certified piping and instrumentation engineer.
Analyze the provided P&ID diagram context and standards using STRICT tripartite grounding.

=== STRUCTURED P&ID EVIDENCE (CV, OCR, VLM) ===
{structured_context_str}

=== GOVERNING STANDARDS EVIDENCE (LOCAL RAG) ===
{rag_context_str}

USER QUERY:
{query}

Format your response in EXACTLY these three sections:
#### 1. VISUAL EVIDENCE
(Detail the tags, instruments, valves, and connections identified by deterministic CV/OCR/VLM)

#### 2. DOCUMENT EVIDENCE
(Detail the relevant ISA-5.1 symbology and ASME piping principles retrieved from local manuals)

#### 3. MODEL INFERENCE & TECHNICAL ASSESSMENT
(Synthesize the operational relationship and state explicit limitations)
"""

    ollama = OllamaLLMProvider()
    llama_req = LLMGenerateRequest(
        prompt=llama_prompt,
        model="llama3:latest",
        temperature=0.1,
        max_tokens=700
    )

    start_llama = time.time()
    llama_resp = await ollama.generate(llama_req)
    llama_duration = round(time.time() - start_llama, 2)
    final_answer = llama_resp.text.strip()
    print(f"    Llama3 completed in {llama_duration}s.")

    # 4. Verifier Fact-Checking
    print("\n[5] Verifying answer against structured P&ID ground facts...")
    claim_verification = verifier.verify_facts(
        claims=[final_answer[:500]],
        retrieved_context=rag_chunks,
        document_text=structured_context_str
    )
    print(f"    Verification Status: {'VALID' if claim_verification.is_valid else 'NEEDS_REVIEW'}")
    print(f"    Supported Claims: {claim_verification.supported_claims}/{claim_verification.total_claims}")

    # 5. Network telemetry check
    telemetry = network_monitor.get_telemetry()
    print(f"\n[6] Network Telemetry:")
    print(f"    Status: {telemetry.status}")
    print(f"    External AI Calls: {telemetry.external_ai_calls}")
    print(f"    WAN Egress Blocked: {telemetry.wan_egress_blocked}")
    print(f"    Air Gap Compliant: {telemetry.air_gap_compliant}")

    pid_test_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "diagram": os.path.basename(pid_path),
        "query": query,
        "ocr_result": {
            "tags_detected_count": len(pid_context["ocr_tags"]),
            "tags": [t["text"] for t in pid_context["ocr_tags"]],
            "sample_details": pid_context["ocr_tags"][:10]
        },
        "symbols": {
            "detected_count": len(pid_context["detected_symbols"]),
            "symbols_sample": pid_context["detected_symbols"][:10]
        },
        "connections": {
            "count": len(pid_context["connections"]),
            "connections_sample": pid_context["connections"][:15]
        },
        "vlm_observations": pid_context["visual_observations"],
        "rag_sources": rag_sources,
        "final_answer": final_answer,
        "verification": claim_verification.model_dump(),
        "latencies": {
            "hybrid_pipeline_seconds": pipe_duration,
            "rag_retrieval_seconds": rag_duration,
            "llama_synthesis_seconds": llama_duration,
            "total_seconds": round(pipe_duration + rag_duration + llama_duration, 2)
        },
        "network_calls": {
            "external_ai_calls": telemetry.external_ai_calls,
            "external_connections": telemetry.external_connections,
            "wan_egress_blocked": telemetry.wan_egress_blocked,
            "air_gap_compliant": telemetry.air_gap_compliant,
            "integrity_seal": telemetry.integrity_hash
        },
        "verdict": "PASS" if (len(pid_context["ocr_tags"]) > 0 and len(final_answer) > 50 and telemetry.air_gap_compliant) else "FAIL"
    }

    out_file = os.path.join(RESULTS_DIR, "offline_pid_test.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(pid_test_record, f, indent=2)

    print(f"\n[7] Saved real offline P&ID test result to: {out_file}")
    print(f"    Verdict: {pid_test_record['verdict']}")
    assert pid_test_record["verdict"] == "PASS", "P&ID offline test failed!"

if __name__ == "__main__":
    asyncio.run(main())
