import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.documents.pid_pipeline import pid_hybrid_pipeline

# pid.png comes from the Eng_Diagrams dataset, which has no licence, so it is not
# shipped. Point CONFIGIQ_RESEARCH_PID at a local copy to run this eval set.
PID_PATH = os.path.abspath(os.getenv("CONFIGIQ_RESEARCH_PID", "demo_data/pid/pid.png"))

pytestmark = pytest.mark.skipif(
    not os.path.exists(PID_PATH),
    reason="Research-only P&ID (Eng_Diagrams, no licence) not present; set CONFIGIQ_RESEARCH_PID",
)


@pytest.fixture(scope="module")
def pid_context():
    """Run extraction pipeline once for the evaluation suite."""
    assert os.path.exists(PID_PATH), f"P&ID file not found at {PID_PATH}"
    import asyncio
    return asyncio.run(pid_hybrid_pipeline.analyze(PID_PATH))


def test_eval_1_equipment_present(pid_context):
    """Q1: What equipment is present in this P&ID diagram?"""
    ans = pid_hybrid_pipeline.answer_engineering_question(
        pid_context, "What equipment is present in this P&ID diagram?"
    )
    assert ans["confidence_level"] == "HIGH"
    assert ans["verification_status"] == "SUPPORTED"
    assert "Valves" in ans["answer"] or "equipment" in ans["answer"].lower()
    assert len(ans["evidence"]) >= 1


def test_eval_2_tag_location(pid_context):
    """Q2: Where is valve V-1063 located in the drawing?"""
    ans = pid_hybrid_pipeline.answer_engineering_question(
        pid_context, "Where is valve V-1063 located in the drawing?"
    )
    assert ans["confidence_level"] == "HIGH"
    assert ans["verification_status"] == "SUPPORTED_BY_OCR"
    assert "V-1063" in ans["answer"]
    assert "coordinates" in ans["answer"] or "bbox" in str(ans["evidence"])


def test_eval_3_specific_tag_extraction(pid_context):
    """Q3: Extract all pressure transmitter and indicator tags from the diagram."""
    tags = [t["text"] for t in pid_context["ocr_tags"]]
    pt_tags = [t for t in tags if t.startswith("PT-") or t.startswith("PI-")]
    assert len(pt_tags) >= 1
    assert "PI-1027" in pt_tags or "PT-1027" in pt_tags


def test_eval_4_connections(pid_context):
    """Q4: What is connected to tag V-1063?"""
    ans = pid_hybrid_pipeline.answer_engineering_question(
        pid_context, "What is connected to tag V-1063?"
    )
    assert ans["confidence"] > 0.0
    assert "V-1063" in ans["answer"] or "connected" in ans["answer"].lower() or len(ans["evidence"]) >= 1


def test_eval_5_associated_instruments(pid_context):
    """Q5: What instruments are present in the diagram?"""
    ans = pid_hybrid_pipeline.answer_engineering_question(
        pid_context, "What instruments are present in this diagram?"
    )
    assert "Instrumentation" in ans["answer"] or len(pid_context["instruments"]) >= 1
    inst_labels = [i["label"] for i in pid_context["instruments"]]
    assert any("1027" in lbl for lbl in inst_labels)


def test_eval_6_connecting_lines(pid_context):
    """Q6: What process lines or signal connections exist in the diagram?"""
    conns = pid_context["connections"]
    assert len(conns) > 10
    # Line types must be either process or instrument_dashed
    line_types = {c.get("line_type") for c in conns}
    assert "process" in line_types
    for c in conns:
        assert "evidence" in c
        assert "status" in c


def test_eval_7_valves_detected(pid_context):
    """Q7: What valves are detected in the diagram?"""
    valves = pid_context["valves"]
    assert len(valves) >= 5
    valve_types = [v["label"] for v in valves]
    assert any("Valve" in vt or "V-" in vt for vt in valve_types)


def test_eval_8_instrument_loop(pid_context):
    """Q8: What instruments are associated with PT-1027?"""
    ans = pid_hybrid_pipeline.answer_engineering_question(
        pid_context, "What instruments are associated with PT-1027?"
    )
    assert ans["verification_status"] in ("SUPPORTED_BY_TOPOLOGY", "NEEDS_REVIEW", "SUPPORTED")
    assert len(ans["evidence"]) >= 1


def test_eval_9_standard_explanation(pid_context):
    """Q9: What does standard ISA-5.1 say about instrumentation tags?"""
    ans = pid_hybrid_pipeline.answer_engineering_question(
        pid_context, "What does standard ISA-5.1 say about instrumentation identification and symbols?"
    )
    assert ans["verification_status"] in ("SUPPORTED_BY_RAG", "SUPPORTED")
    assert ans["confidence"] >= 0.50
    assert len(ans["sources"]) >= 1


def test_eval_10_negative_unsupported_rejection(pid_context):
    """Q10: Where is reactor R-901 located? (Negative hallucination check)"""
    ans = pid_hybrid_pipeline.answer_engineering_question(
        pid_context, "Where is reactor R-901 located?"
    )
    # Must explicitly state not found and never hallucinate coordinates
    assert ans["verification_status"] == "NEEDS_REVIEW"
    assert ans["confidence_level"] == "UNKNOWN"
    assert "Unable to locate" in ans["answer"] or "not found" in ans["answer"].lower()
    assert "R-901" in ans["answer"]
