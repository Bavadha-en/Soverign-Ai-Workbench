import time
from typing import Any, Dict, List
from backend.llm.interface import LLMProvider
from backend.models.schemas import LLMGenerateRequest, LLMGenerateResponse


class MockLLMProvider(LLMProvider):
    """
    Mock LLM Provider for offline development, testing, and GPU-free demos.
    Returns realistic industrial domain responses for each task type.
    """

    def __init__(self, model_name: str = "mock-open-weight-industrial-v1"):
        self.model_name = model_name

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        start_time = time.time()
        prompt_lower = request.prompt.lower()

        if getattr(request, "images", None):
            text = self._vision_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["classify", "categories:", "vision, coding"]):
            text = self._classify_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["verdict", "fact-verification", "supported"]):
            text = self._verification_response(prompt_lower)
        elif "approval note" in prompt_lower or "approval request" in prompt_lower:
            text = self._approval_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["summarize", "summary", "synthesize", "format engineering"]):
            text = self._summary_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["calculate", "python", "code", "script", "equation", "pump efficiency", "pressure drop", "thermal stress"]):
            text = self._coding_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["inspection", "report", "analyze", "findings", "corrosion", "defect"]):
            text = self._inspection_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["sop", "procedure", "maintenance", "standard operating"]):
            text = self._sop_response(prompt_lower)
        else:
            text = self._general_response(prompt_lower)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        return LLMGenerateResponse(
            text=text,
            model=self.model_name,
            usage={
                "prompt_tokens": len(request.prompt.split()),
                "completion_tokens": len(text.split()),
                "total_tokens": len(request.prompt.split()) + len(text.split()),
            },
            duration_ms=duration_ms,
        )

    def _vision_response(self, prompt: str) -> str:
        return (
            "1. Severe localized corrosion detected on the lower quadrant of the flange face, with approximately 40% wall thickness reduction. "
            "Pitting depth estimated at 3.2mm based on surface texture analysis.\n"
            "2. Gasket seating surface shows circumferential scoring and erosion marks consistent with high-velocity fluid impingement, "
            "indicating potential seal failure risk under operating pressure.\n"
            "3. Bolt holes #3 and #7 exhibit thread galling and rust deposits suggesting improper torque application or moisture ingress.\n"
            "4. No visible crack propagation along weld heat-affected zones. Weld bead geometry appears uniform.\n"
            "5. Surface discoloration pattern (blue-brown oxide) near the process-side face indicates prior thermal excursion above 300C."
        )

    def _classify_response(self, prompt: str) -> str:
        if "image" in prompt or "visual" in prompt or "inspect" in prompt:
            return "vision"
        if "complex" in prompt or "simulation" in prompt or "finite element" in prompt:
            return "coding_heavy"
        if "code" in prompt or "python" in prompt or "calculate" in prompt or "script" in prompt:
            return "coding"
        return "general"

    def _verification_response(self, prompt: str) -> str:
        return '{"verdict": "SUPPORTED", "confidence": 0.89, "evidence": "SOP-M-402 Section 3 confirms wall loss exceeding 30% requires adjacent spool piece replacement per ASME B31.3 standards."}'

    def _inspection_response(self, prompt: str) -> str:
        return (
            "Based on the inspection report analysis:\n"
            "1. Critical Finding: Corroded main control valve CV-102 showing 32.4% wall thickness loss. "
            "Ultrasonic thickness measurement recorded 4.8mm remaining wall vs. 7.1mm nominal. "
            "This exceeds the 30% replacement threshold per SOP-M-402 Section 3.\n"
            "2. Critical Finding: Adjacent pipe spool SP-102-D shows 31.4% wall loss at 6 o'clock position. "
            "Minimum remaining thickness: 5.9mm vs. 8.6mm nominal. "
            "Requires replacement per ASME B31.3 integrity assessment.\n"
            "3. Secondary Finding: Pump P-401 mechanical seal leakage at 8 drops/minute, "
            "exceeding the 5 drops/minute threshold per SOP-M-104 Section 2.3. Seal face replacement required.\n"
            "4. Secondary Finding: Spiral wound gasket on CV-102 inlet flange shows compression set and partial blowout. "
            "Gasket must not be reused per SOP-M-402 Section 3.\n"
            "Risk Assessment: HIGH (Category A — Immediate Action Required)\n"
            "Recommendation: Immediate isolation of CV-102 loop, emergency procurement of 316L SS Class 600 RTJ "
            "replacement valve, and scheduled shutdown within 72 hours.\n"
            "Applicable Standards: ASME B31.3, API 570, SOP-M-402, SOP-M-104"
        )

    def _sop_response(self, prompt: str) -> str:
        return (
            "## Applicable Standard Operating Procedures\n\n"
            "### SOP-M-402: High Pressure Control Valve Replacement\n"
            "**Scope**: Covers isolation, removal, and replacement of corroded high-pressure control valves in refinery service.\n\n"
            "**Key Requirements**:\n"
            "1. Complete line depressurization and cool-down to ambient temperature before any mechanical work\n"
            "2. Double Block and Bleed (DBB) isolation on upstream and downstream isolation valves\n"
            "3. Zero residual pressure verification using calibrated pressure gauges\n"
            "4. Mandatory PPE: chemical splash goggles, heat-resistant gloves, full protective coveralls\n"
            "5. Wall thickness measurement on adjacent flanges using ultrasonic testing (UT)\n"
            "6. If wall loss exceeds 30%, replace adjacent spool pieces per ASME B31.3\n"
            "7. Install certified 316L SS replacement valve with Class 600 RTJ flanges\n"
            "8. Torque bolts in cross-pattern star sequence to 220 Nm\n"
            "9. Hydrostatic test at 1.5x MAOP for 30 minutes with zero detectable pressure drop\n\n"
            "### SOP-SAF-001: Electrical Isolation & Lockout/Tagout (LOTO)\n"
            "**Applicability**: Required before any mechanical work on valve actuators or instrumentation\n"
            "**Key Steps**: Identify energy sources → Notify operations → Shut down → Isolate → "
            "Apply locks/tags → Verify zero energy (Live-Dead-Live test)\n"
        )

    def _approval_response(self, prompt: str) -> str:
        return (
            "## Approval Note: Emergency Valve Replacement & Corrosion Remediation\n\n"
            "**Reference**: Inspection Report IR-2024-CV102-REV-A\n"
            "**Date**: Generated by ConfigIQ Sovereign Workbench\n"
            "**Priority**: URGENT — Category A (Immediate Action)\n\n"
            "### 1. Subject\n"
            "Request for emergency approval of corroded high-pressure control valve CV-102 replacement, "
            "including adjacent spool piece SP-102-D, based on inspection findings exceeding SOP-M-402 "
            "replacement thresholds.\n\n"
            "### 2. Background\n"
            "Routine ultrasonic thickness survey identified 32.4% wall loss on CV-102 downstream flange "
            "and 31.4% wall loss on adjacent spool SP-102-D. Both exceed the 30% replacement threshold "
            "mandated by ASME B31.3 and SOP-M-402 Section 3.\n\n"
            "### 3. Technical Justification\n"
            "- Remaining wall thickness (4.8mm) approaches minimum required thickness for design pressure "
            "of 42 bar per ASME B31.3 calculation\n"
            "- Active pitting indicates ongoing corrosion mechanism (estimated rate: 0.4mm/year)\n"
            "- Gasket failure evidence suggests prior seal leakage and potential process fluid exposure\n\n"
            "### 4. Recommended Action\n"
            "APPROVED WITH MANDATORY CONDITIONS:\n"
            "- Procure 316L SS Class 600 RTJ replacement valve (est. cost: INR 4,50,000)\n"
            "- Schedule 24-hour maintenance window within 72 hours\n"
            "- Execute under SOP-M-402 with LOTO per SOP-SAF-001\n"
            "- Post-replacement hydrostatic test at 63 bar (1.5x MAOP) for 30 minutes\n\n"
            "### 5. Verification Status\n"
            "All claims in this note have been verified against local SOP knowledge base. "
            "3/3 critical claims SUPPORTED by retrieved SOP documentation.\n"
        )

    def _coding_response(self, prompt: str) -> str:
        if "pressure drop" in prompt:
            return (
                "Mock LLM Response (Coding Specialist):\n"
                "```python\n"
                "import math\n\n"
                "# Darcy-Weisbach Pressure Drop Calculation\n"
                "pipe_diameter_m = 0.1524  # 6-inch schedule 40\n"
                "pipe_length_m = 100.0\n"
                "flow_rate_m3s = 0.025\n"
                "density = 998.0  # water at 20C\n"
                "viscosity = 1.002e-3\n"
                "roughness = 0.000045  # commercial steel\n\n"
                "area = math.pi * (pipe_diameter_m / 2) ** 2\n"
                "velocity = flow_rate_m3s / area\n"
                "reynolds = density * velocity * pipe_diameter_m / viscosity\n\n"
                "# Colebrook-White (iterative)\n"
                "f = 0.02\n"
                "for _ in range(50):\n"
                "    rhs = -2.0 * math.log10(roughness / (3.7 * pipe_diameter_m) + 2.51 / (reynolds * math.sqrt(f)))\n"
                "    f = 1.0 / rhs ** 2\n\n"
                "delta_p = f * (pipe_length_m / pipe_diameter_m) * 0.5 * density * velocity ** 2\n"
                "delta_p_bar = delta_p / 1e5\n\n"
                "print(f'Flow Velocity: {velocity:.3f} m/s')\n"
                "print(f'Reynolds Number: {reynolds:.0f}')\n"
                "print(f'Friction Factor: {f:.6f}')\n"
                "print(f'Pressure Drop: {delta_p:.1f} Pa ({delta_p_bar:.4f} bar)')\n"
                "```"
            )
        if "thermal stress" in prompt:
            return (
                "Mock LLM Response (Coding Specialist):\n"
                "```python\n"
                "# Thermal Stress Under Cyclic Loading (ASME Sec VIII Div 2)\n"
                "E_modulus = 200e9  # Pa, carbon steel\n"
                "alpha = 12e-6     # 1/K, thermal expansion coefficient\n"
                "delta_T = 150.0   # K, temperature swing per cycle\n"
                "poisson = 0.3\n"
                "n_cycles = 10000\n\n"
                "# Thermal stress (fully restrained)\n"
                "sigma_thermal = E_modulus * alpha * delta_T / (1 - poisson)\n"
                "sigma_mpa = sigma_thermal / 1e6\n\n"
                "# Fatigue life estimate (simplified S-N approach)\n"
                "import math\n"
                "S_ult = 450  # MPa, ultimate tensile strength\n"
                "S_endurance = 0.5 * S_ult  # Approximate endurance limit\n"
                "if sigma_mpa > S_endurance:\n"
                "    N_f = (S_ult / sigma_mpa) ** 5 * 1e6\n"
                "    print(f'WARNING: Thermal stress ({sigma_mpa:.1f} MPa) exceeds endurance limit ({S_endurance:.0f} MPa)')\n"
                "else:\n"
                "    N_f = float('inf')\n"
                "    print(f'Thermal stress ({sigma_mpa:.1f} MPa) is within endurance limit ({S_endurance:.0f} MPa)')\n\n"
                "print(f'Thermal Stress: {sigma_mpa:.2f} MPa')\n"
                "print(f'Design Cycles: {n_cycles}')\n"
                "print(f'Estimated Fatigue Life: {N_f:.0f} cycles')\n"
                "safety_factor = N_f / n_cycles if N_f != float('inf') else 999\n"
                "print(f'Safety Factor: {safety_factor:.1f}')\n"
                "```"
            )
        return (
            "Mock LLM Response (Coding Specialist):\n"
            "```python\n"
            "# Centrifugal Pump Hydraulic Efficiency Calculation\n"
            "# Input Parameters\n"
            "flow_rate_m3_s = 50.0 / 3600.0  # Convert 50 m3/h to m3/s\n"
            "head_m = 60.0\n"
            "density = 1000.0  # kg/m3\n"
            "gravity = 9.81    # m/s2\n"
            "hydraulic_power_w = density * gravity * flow_rate_m3_s * head_m\n"
            "hydraulic_power_kw = hydraulic_power_w / 1000.0\n"
            "power_in_kw = 11.0\n"
            "efficiency_pct = (hydraulic_power_kw / power_in_kw) * 100.0\n\n"
            "# Specific speed (diagnostic parameter)\n"
            "import math\n"
            "rpm = 2950  # typical 2-pole motor at 50Hz\n"
            "Ns = rpm * math.sqrt(flow_rate_m3_s) / (head_m ** 0.75)\n\n"
            "print(f'=== Pump Performance Analysis ===')\n"
            "print(f'Flow Rate: 50.0 m3/h ({flow_rate_m3_s:.5f} m3/s)')\n"
            "print(f'Total Head: {head_m:.1f} m')\n"
            "print(f'Hydraulic Power Output: {hydraulic_power_kw:.3f} kW')\n"
            "print(f'Electrical Power Input: {power_in_kw:.2f} kW')\n"
            "print(f'Pump Hydraulic Efficiency: {efficiency_pct:.2f}%')\n"
            "print(f'Specific Speed (Ns): {Ns:.2f}')\n\n"
            "if efficiency_pct < 60:\n"
            "    print('WARNING: Efficiency below 60% — inspect impeller wear and suction conditions')\n"
            "elif efficiency_pct > 90:\n"
            "    print('NOTE: Efficiency exceeds typical range — verify input parameters')\n"
            "else:\n"
            "    print('STATUS: Efficiency within acceptable operating range (60-90%)')\n"
            "```"
        )

    def _summary_response(self, prompt: str) -> str:
        return (
            "## Engineering Analysis Summary\n\n"
            "The analysis has been completed successfully using the ConfigIQ sovereign computation pipeline. "
            "All calculations were executed in an isolated local sandbox with network access blocked.\n\n"
            "### Key Results\n"
            "- All computed values fall within expected physical bounds\n"
            "- Calculation methodology follows applicable ASME/API standards\n"
            "- Results have been verified against analytical benchmarks\n"
            "- No external API calls were made during computation (verified via network telemetry)\n\n"
            "### Deliverables Generated\n"
            "- Engineering Calculation Workbook (.xlsx) with Input, Calculation, Verification, and Sources sheets\n"
            "- All intermediate values preserved for audit trail\n\n"
            "### Verification Status\n"
            "Sandbox execution completed with exit code 0. All numerical outputs are within valid physical ranges. "
            "No NaN, Infinity, or division-by-zero conditions detected."
        )

    def _general_response(self, prompt: str) -> str:
        return (
            "Based on analysis of the local knowledge base and retrieved SOP documentation:\n\n"
            "The query has been processed using the ConfigIQ sovereign reasoning pipeline. "
            "All relevant engineering standards and internal procedures from the local vector store "
            "have been consulted.\n\n"
            "Key points:\n"
            "1. The analysis is grounded in locally stored SOP documents and inspection guidelines\n"
            "2. All referenced standards (ASME, API, internal SOPs) are available in the on-premise knowledge base\n"
            "3. No external data sources were accessed during this analysis\n\n"
            "For more specific results, please provide the relevant inspection report, "
            "engineering calculation parameters, or reference the specific SOP section you need analyzed."
        )

    async def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "success",
            "findings": [
                "Corroded control valve CV-102 with 32.4% wall loss exceeding 30% replacement threshold",
                "Pump P-401 mechanical seal leakage at 8 drops/min exceeding 5 drops/min SOP limit",
                "Adjacent spool SP-102-D showing 31.4% wall loss requiring ASME B31.3 assessment",
            ],
            "risk_level": "HIGH",
            "recommended_action": "Immediate isolation and emergency replacement of CV-102 per SOP-M-402",
            "applicable_standards": ["ASME B31.3", "API 570", "SOP-M-402", "SOP-M-104"],
            "verification_status": "3/3 claims SUPPORTED",
        }

    async def health_check(self) -> bool:
        return True

    async def list_available_models(self) -> list:
        return ["mock-sovereign-industrial-v1"]
