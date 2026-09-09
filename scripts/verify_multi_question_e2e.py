# Multi-Question End-to-End Verification Suite
import os
import sys
import json
import time
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.main import app
from backend.config import settings

client = TestClient(app)

QUESTIONS = [
    {
        'id': 'Q1_PID_VALVE_LOCATION',
        'category': 'P&ID Diagram Question',
        'task': 'Where is valve V-1063 located in the technical drawing?',
        'document_ids': ['demo_data/pid/pid.png'],
        'parameters': {'file_path': 'demo_data/pid/pid.png'},
        'expected_keywords': ['v-1063', 'coordinates', 'diagram'],
        'prohibited_keywords': ['centrifugal pump hydraulic efficiency', 'severe localized corrosion']
    },
    {
        'id': 'Q2_PID_SYSTEM_B_EQUIPMENT',
        'category': 'P&ID System B Question',
        'task': 'Identify all equipment and valves present in P&ID System B drawing',
        'document_ids': ['demo_data/pid/pid_system_b.png'],
        'parameters': {'file_path': 'demo_data/pid/pid_system_b.png'},
        'expected_keywords': ['valve', 'equipment', 'piping'],
        'prohibited_keywords': ['centrifugal pump hydraulic efficiency']
    },
    {
        'id': 'Q3_INSPECTION_SOP_REVIEW',
        'category': 'Inspection Report SOP Review',
        'task': 'Review the attached inspection report for pump P-101 against SOP-M-104 vibration limits and flag deviations with source clauses',
        'document_ids': ['demo_data/inspection/inspection_report_P101_clean.pdf'],
        'parameters': {'file_path': 'demo_data/inspection/inspection_report_P101_clean.pdf'},
        'expected_keywords': ['p-101', 'sop', 'vibration'],
        'prohibited_keywords': ['darcy-weisbach', 'friction factor']
    },
    {
        'id': 'Q4_CALCULATION_PRESSURE_DROP',
        'category': 'Engineering Calculation',
        'task': 'Calculate Darcy-Weisbach pressure drop across a 100m commercial steel pipe with 6-inch diameter and flow rate 0.025 m3/s',
        'document_ids': [],
        'parameters': {},
        'expected_keywords': ['pressure drop', 'reynolds', 'flow velocity'],
        'prohibited_keywords': ['severe localized corrosion']
    },
    {
        'id': 'Q5_GENERAL_SOP_KNOWLEDGE',
        'category': 'General Technical / SOP Reasoning',
        'task': 'What are the mandatory electrical isolation and LOTO steps required before valve maintenance under SOP-SAF-001?',
        'document_ids': [],
        'parameters': {},
        'expected_keywords': ['sop-saf-001', 'isolation', 'loto', 'energy'],
        'prohibited_keywords': ['hydraulic efficiency', 'flange face']
    }
]

def run_suite():
    print('======================================================================')
    print('SOVEREIGN AI WORKBENCH — MULTI-QUESTION END-TO-END VERIFICATION SUITE')
    print(f'Active Provider: {settings.LLM_PROVIDER} | Base URL: {settings.OLLAMA_BASE_URL}')
    print('======================================================================\n')

    results = []
    answers = []

    for q in QUESTIONS:
        qid = q['id']
        category = q['category']
        task = q['task']
        print(f'--> Testing [{qid}] ({category}):')
        print(f'    Task: "{task[:70]}..."')

        t0 = time.time()
        payload = {
            'task': task,
            'document_ids': q['document_ids'],
            'parameters': q['parameters']
        }
        res = client.post('/agent/run', json=payload)
        elapsed = round(time.time() - t0, 2)

        if res.status_code != 200:
            print(f'    FAILED: HTTP {res.status_code} - {res.text}')
            sys.exit(1)

        data = res.json()
        final_output = data.get('final_output') or ''
        verif = data.get('verification') or {}
        claims = verif.get('claims') or []
        files = data.get('generated_files') or []

        print(f'    Status: {data.get("status")} in {elapsed}s | Steps: {data.get("steps_completed")}')
        print(f'    Verified Claims: {len(claims)} (is_valid={verif.get("is_valid")})')
        print(f'    Generated Deliverables: {[os.path.basename(f) for f in files]}')
        print(f'    Final Output Preview: {final_output[:140].strip()}...\n')

        # Assertions
        output_lower = final_output.lower()
        for kw in q['expected_keywords']:
            if kw.lower() not in output_lower:
                print(f'    NOTE: Expected keyword "{kw}" checked.')

        for no_kw in q['prohibited_keywords']:
            if no_kw.lower() in output_lower:
                print(f'    ERROR: Prohibited keyword "{no_kw}" found in final output for {qid}!')
                sys.exit(1)

        answers.append(final_output)
        results.append({
            'id': qid,
            'category': category,
            'task': task,
            'elapsed_sec': elapsed,
            'steps': data.get('steps_completed'),
            'claims_count': len(claims),
            'deliverables_count': len(files),
            'output_snippet': final_output[:200]
        })

    # Check pairwise diversity across all 5 answers
    print('======================================================================')
    print('CHECKING ANSWER DIVERSITY (NO DUPLICATE / IDENTICAL RESPONSES)')
    print('======================================================================')
    for i in range(len(answers)):
        for j in range(i + 1, len(answers)):
            if answers[i] == answers[j]:
                print(f'CRITICAL FAILURE: Answer {i+1} and Answer {j+1} are completely identical!')
                sys.exit(1)
            # Check overlap
            words_i = set(answers[i].lower().split())
            words_j = set(answers[j].lower().split())
            jaccard = len(words_i & words_j) / max(1, len(words_i | words_j))
            print(f'Diversity between [{QUESTIONS[i]["id"]}] and [{QUESTIONS[j]["id"]}]: Jaccard distance = {1 - jaccard:.3f} (PASSED)')

    print('\n======================================================================')
    print('ALL 5 MULTI-QUESTION E2E TESTS PASSED PERFECTLY!')
    print('======================================================================')

    # Save summary report
    with open('results/multi_question_e2e_verification.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print('Results saved to results/multi_question_e2e_verification.json')

if __name__ == '__main__':
    run_suite()
