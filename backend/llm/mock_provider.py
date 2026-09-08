import time
from typing import Any, Dict
from backend.llm.interface import LLMProvider
from backend.models.schemas import LLMGenerateRequest, LLMGenerateResponse

class MockLLMProvider(LLMProvider):
    """
    Mock LLM Provider for offline development and testing.
    Allows complete workbench functionality before real local model server is connected.
    """

    def __init__(self, model_name: str = "mock-open-weight-industrial-v1"):
        self.model_name = model_name

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        start_time = time.time()

        prompt_lower = request.prompt.lower()
        if "inspection" in prompt_lower or "report" in prompt_lower:
            text = (
                "Based on the inspection report analysis:\n"
                "1. Critical Finding: Corroded main control valve CV-102 showing 35% wall thickness loss.\n"
                "2. Secondary Finding: Minor seal degradation on pump P-401.\n"
                "3. Recommendation: Immediate replacement of CV-102 per SOP-M-402 section 4.3."
            )
        elif "sop" in prompt_lower or "procedure" in prompt_lower:
            text = (
                "Relevant SOP Maintenance Procedure (SOP-M-402):\n"
                "Section 4.3: High-pressure valve replacement requires line depressurization, "
                "lockout-tagout (LOTO), certified replacement gasket installation, and hydrostatic testing up to 1.5x operating pressure."
            )
        elif "approval note" in prompt_lower:
            text = (
                "Approval Note generated successfully. Details:\n"
                "Subject: Urgent Approval Request for Corrosion Remediation & Valve Replacement\n"
                "Action Required: Approve procurement and work order for CV-102 replacement."
            )
        elif any(kw in prompt_lower for kw in ["calculate", "python", "code", "pump efficiency", "script", "equation"]):
            text = (
                "Mock LLM Response (Coding Specialist):\n"
                "```python\n"
                "# Engineering Calculation Script\n"
                "flow_rate_m3_s = 50.0 / 3600.0\n"
                "head_m = 60.0\n"
                "density = 1000.0\n"
                "gravity = 9.81\n"
                "hydraulic_power_w = density * gravity * flow_rate_m3_s * head_m\n"
                "hydraulic_power_kw = hydraulic_power_w / 1000.0\n"
                "power_in_kw = 11.0\n"
                "efficiency_pct = (hydraulic_power_kw / power_in_kw) * 100.0\n"
                "print(f'Hydraulic Power Output: {hydraulic_power_kw:.3f} kW')\n"
                "print(f'Electrical Power Input: {power_in_kw:.2f} kW')\n"
                "print(f'Pump Hydraulic Efficiency: {efficiency_pct:.2f}%')\n"
                "```"
            )
        else:
            text = f"Mock LLM Response: Analyzed input prompt '{request.prompt[:60]}...' successfully in offline mode."

        duration_ms = round((time.time() - start_time) * 1000, 2)
        return LLMGenerateResponse(
            text=text,
            model=self.model_name,
            usage={"prompt_tokens": len(request.prompt.split()), "completion_tokens": len(text.split())},
            duration_ms=duration_ms
        )

    async def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "findings": ["Corroded valve CV-102", "Pump P-401 seal degradation"],
            "recommended_action": "Replace valve CV-102 according to SOP-M-402",
            "mock": True
        }

    async def health_check(self) -> bool:
        return True
