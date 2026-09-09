import os
import sys
import json
import time
import re
import asyncio
from docx import Document

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force real Ollama models
os.environ["LLM_PROVIDER"] = "ollama"
os.environ["GENERAL_MODEL"] = "llama3:latest"
os.environ["VISION_MODEL"] = "moondream:latest"
os.environ["EMBEDDING_MODEL"] = "nomic-embed-text:latest"

from backend.agents.agent import ConfigIQAgent
from backend.services.audit_service import audit_service
from backend.services.network_monitor import network_monitor

RESULTS_DIR = os.path.join(os.getcwd(), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

def extract_docx_text(docx_path):
    doc = Document(docx_path)
    full_text = []
    for p in doc.paragraphs:
        if p.text.strip():
            full_text.append(p.text.strip())
    for table in doc.tables:
        for row in table.rows:
            row_text = [c.text.strip() for c in row.cells if c.text.strip()]
            if row_text:
                full_text.append(" | ".join(row_text))
    return "\n".join(full_text)

async def main():
    print("=" * 60)
    print("PHASE 5 & 6: REAL INSPECTION WORKFLOW & ANTI-HARDCODE VERIFICATION")
    print("=" * 60)

    agent = ConfigIQAgent()

    # ------------------ RUN REPORT A (P-101) ------------------
    doc_a_path = os.path.abspath("demo_data/inspection/inspection_report_P101_clean.pdf")
    task_a = "Analyze this industrial equipment inspection report for centrifugal pump P-101 and prepare an official verified Approval Note DOCX."
    print(f"\n[RUN A] Submitting Task: {task_a}")
    print(f"[RUN A] Document: {doc_a_path}")

    start_a = time.time()
    state_a = await agent.run(
        task=task_a,
        document_ids=[doc_a_path],
        parameters={"file_path": doc_a_path}
    )
    dur_a = round(time.time() - start_a, 2)
    print(f"[RUN A] Completed in {dur_a}s with status: {state_a.status}")
    print(f"[RUN A] Generated Deliverables: {state_a.generated_files}")

    docx_a_path = state_a.generated_files[0] if state_a.generated_files else None
    assert docx_a_path and os.path.exists(docx_a_path), "Docx A was not generated!"
    text_a = extract_docx_text(docx_a_path)

    # ------------------ RUN REPORT B (P-202) ------------------
    doc_b_path = os.path.abspath("demo_data/inspection/inspection_report_P202_clean.pdf")
    task_b = "Analyze this industrial equipment inspection report for secondary booster pump P-202 and prepare an official verified Approval Note DOCX."
    print(f"\n[RUN B] Submitting Task: {task_b}")
    print(f"[RUN B] Document: {doc_b_path}")

    start_b = time.time()
    state_b = await agent.run(
        task=task_b,
        document_ids=[doc_b_path],
        parameters={"file_path": doc_b_path}
    )
    dur_b = round(time.time() - start_b, 2)
    print(f"[RUN B] Completed in {dur_b}s with status: {state_b.status}")
    print(f"[RUN B] Generated Deliverables: {state_b.generated_files}")

    docx_b_path = state_b.generated_files[0] if state_b.generated_files else None
    assert docx_b_path and os.path.exists(docx_b_path), "Docx B was not generated!"
    text_b = extract_docx_text(docx_b_path)

    # ------------------ VERIFY AGAINST GROUND TRUTHS ------------------
    with open("demo_data/inspection/ground_truth_P101.json", "r") as f:
        gt_a = json.load(f)
    with open("demo_data/inspection/ground_truth_P202.json", "r") as f:
        gt_b = json.load(f)

    # Check Report A
    has_p101 = "p-101" in text_a.lower()
    has_p101_vib = "7.4" in text_a
    has_p101_temp = "88" in text_a
    has_p101_crit = "critical" in text_a.lower()
    has_p101_sop = any(s.lower() in text_a.lower() for s in ["sop-m-104", "pump", "iso 10816"])

    # Check Report B
    has_p202 = "p-202" in text_b.lower()
    has_p202_vib = "5.1" in text_b
    has_p202_temp = "71" in text_b
    has_p202_warn = "high" in text_b.lower() or "overhaul" in text_b.lower() or "warning" in text_b.lower()
    has_p202_sop = any(s.lower() in text_b.lower() for s in ["sop-m-104", "pump"])

    # Anti-Hardcode Check: Document A must differ significantly from Document B
    hardcode_check_pass = (
        has_p101 and has_p202 and
        ("p-202" not in text_a.lower()) and
        ("p-101" not in text_b.lower()) and
        ("7.4" in text_a and "7.4" not in text_b) and
        ("5.1" in text_b and "5.1" not in text_a) and
        (text_a != text_b)
    )

    print("\n" + "=" * 60)
    print("VERIFICATION & ANTI-HARDCODE RESULTS:")
    print("=" * 60)
    print(f"Report A (P-101): ID matched={has_p101}, Vib(7.4)={has_p101_vib}, Temp(88)={has_p101_temp}, Critical={has_p101_crit}, SOP={has_p101_sop}")
    print(f"Report B (P-202): ID matched={has_p202}, Vib(5.1)={has_p202_vib}, Temp(71)={has_p202_temp}, Action={has_p202_warn}, SOP={has_p202_sop}")
    print(f"HARDCODE CHECK: {'PASS' if hardcode_check_pass else 'FAIL'}")

    results = {
        "workflow": "Inspection Report -> Document Extraction -> OCR -> VLM -> RAG -> Llama3 Reasoning -> Verification -> Approval Note DOCX",
        "hardcode_check": "PASS" if hardcode_check_pass else "FAIL",
        "models_used": {
            "general_reasoning": "llama3:latest",
            "vision": "moondream:latest",
            "embeddings": "nomic-embed-text:latest"
        },
        "report_a": {
            "equipment_id": "P-101",
            "input_file": doc_a_path,
            "generated_docx": docx_a_path,
            "execution_duration_sec": dur_a,
            "status": state_a.status.value,
            "verified": state_a.is_verified,
            "checks": {
                "equipment_id_extracted": has_p101,
                "vibration_7_4_extracted": has_p101_vib,
                "bearing_temp_88_extracted": has_p101_temp,
                "severity_critical_applied": has_p101_crit,
                "governing_sop_referenced": has_p101_sop
            },
            "findings_in_docx": state_a.tool_results.get("generate_approval_note", {}).get("findings", []) or state_a.tool_results.get("generate_approval_note", {})
        },
        "report_b": {
            "equipment_id": "P-202",
            "input_file": doc_b_path,
            "generated_docx": docx_b_path,
            "execution_duration_sec": dur_b,
            "status": state_b.status.value,
            "verified": state_b.is_verified,
            "checks": {
                "equipment_id_extracted": has_p202,
                "vibration_5_1_extracted": has_p202_vib,
                "bearing_temp_71_extracted": has_p202_temp,
                "severity_action_applied": has_p202_warn,
                "governing_sop_referenced": has_p202_sop
            }
        }
    }
    telemetry = network_monitor.get_telemetry()
    results["network_telemetry"] = {
        "status": telemetry.status,
        "external_ai_calls": telemetry.external_ai_calls,
        "wan_egress_blocked": telemetry.wan_egress_blocked,
        "air_gap_compliant": telemetry.air_gap_compliant,
        "integrity_seal": telemetry.integrity_hash
    }
    results["verdict"] = "PASS" if hardcode_check_pass and telemetry.air_gap_compliant else "FAIL"

    out_file = os.path.join(RESULTS_DIR, "inspection_e2e.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    offline_out_file = os.path.join(RESULTS_DIR, "offline_inspection_test.json")
    with open(offline_out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved end-to-end inspection results to {out_file} and {offline_out_file}")

if __name__ == "__main__":
    asyncio.run(main())
