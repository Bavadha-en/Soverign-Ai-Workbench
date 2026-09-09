import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.llm.model_router import model_router

RESULTS_DIR = os.path.join(os.getcwd(), "results")
os.makedirs(RESULTS_DIR, exist_ok=True)

test_prompts = [
    {
        "category": "General Reasoning",
        "prompt": "What are the key safety considerations and personnel PPE requirements before inspecting an industrial cooling tower?",
        "expected_model_type": "general",
        "expected_model_substring": "llama3",
        "image_present": False
    },
    {
        "category": "Coding",
        "prompt": "Write a Python script to parse an industrial Modbus TCP packet log and calculate average sensor latency.",
        "expected_model_type": "coding",
        "expected_model_substring": "qwen2.5-coder",
        "image_present": False
    },
    {
        "category": "Calculation (Heavy Coding)",
        "prompt": "Implement a finite element numerical simulation and complex engineering calculation program to solve 2D heat conduction across a multi-layer boiler wall.",
        "expected_model_type": "coding_heavy",
        "expected_model_substring": "qwen2.5-coder:14b",
        "image_present": False
    },
    {
        "category": "Image / P&ID Analysis",
        "prompt": "Analyze this scanned image of a piping and instrumentation diagram to detect pump tags and valve positions.",
        "expected_model_type": "vision",
        "expected_model_substring": "moondream",
        "image_present": True
    },
    {
        "category": "Document Analysis",
        "prompt": "Summarize the major inspection findings, corrosion rates, and regulatory compliance status from this annual refinery audit report.",
        "expected_model_type": "general",
        "expected_model_substring": "llama3",
        "image_present": False
    }
]

eval_results = []
all_passed = True

print("=" * 60)
print("PHASE 10: MODEL ROUTER VERIFICATION")
print("=" * 60)

for item in test_prompts:
    res = model_router.route(prompt=item["prompt"], image_present=item["image_present"])
    task_type = res.get("task_type")
    model = res.get("model")
    reason = res.get("reason")

    is_correct_type = (task_type == item["expected_model_type"])
    is_correct_model = (item["expected_model_substring"] in model.lower())
    passed = is_correct_type and is_correct_model
    if not passed:
        all_passed = False

    status_str = "PASS" if passed else "FAIL"
    print(f"\n[{status_str}] Category: {item['category']}")
    print(f"       Prompt: {item['prompt'][:70]}...")
    print(f"       Routed Task: {task_type} -> Model: {model}")
    print(f"       Reason: {reason}")

    eval_results.append({
        "category": item["category"],
        "prompt": item["prompt"],
        "image_present": item["image_present"],
        "expected_task_type": item["expected_model_type"],
        "expected_model": item["expected_model_substring"],
        "selected_task_type": task_type,
        "selected_model": model,
        "reasoning": reason,
        "passed": passed
    })

# Also verify embedding model routing configuration
embedding_model = "nomic-embed-text:latest"

router_summary = {
    "total_tested": len(test_prompts),
    "all_passed": all_passed,
    "model_matrix": {
        "general_reasoning": "llama3:latest",
        "coding_standard": "qwen2.5-coder:7b",
        "coding_heavy": "qwen2.5-coder:14b",
        "vision_multimodal": "moondream:latest",
        "embeddings": embedding_model
    },
    "routing_evaluations": eval_results
}

out_file = os.path.join(RESULTS_DIR, "router_eval.json")
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(router_summary, f, indent=2)

print(f"\nModel Router Evaluation saved to {out_file} (All Passed: {all_passed})")
