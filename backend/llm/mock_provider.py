import re
import time
from typing import Any, Dict, List
from backend.llm.interface import LLMProvider
from backend.models.schemas import LLMGenerateRequest, LLMGenerateResponse


class MockLLMProvider(LLMProvider):
    """
    Mock LLM Provider for offline development, testing, and GPU-free demos.
    Returns realistic industrial domain responses dynamically tailored to each task type.
    """

    def __init__(self, model_name: str = "mock-open-weight-industrial-v1"):
        self.model_name = model_name

    async def generate(self, request: LLMGenerateRequest) -> LLMGenerateResponse:
        start_time = time.time()
        prompt_lower = request.prompt.lower()

        is_calc = (
            any(kw in prompt_lower for kw in [
                "calculate", "computation", "pump efficiency", "pressure drop", "thermal stress",
                "darcy", "reynolds", "pipe friction"
            ]) or (
                any(kw in prompt_lower for kw in ["python", "script", "equation", "formula", "write code"])
                and not any(kw in prompt_lower for kw in ["sop", "clause", "deviation", "compliance", "inspection review", "flag deviation", "standard"])
            )
        )

        if getattr(request, "images", None):
            text = self._vision_response(request.prompt)
        elif any(kw in prompt_lower for kw in ["classify", "categories:", "vision, coding"]):
            text = self._classify_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["verdict", "fact-verification", "supported"]):
            text = self._verification_response(prompt_lower)
        elif "approval note" in prompt_lower or "approval request" in prompt_lower:
            text = self._approval_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["summarize", "summary", "synthesize", "format engineering"]):
            text = self._summary_response(prompt_lower)
        elif is_calc:
            text = self._coding_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["sop", "procedure", "maintenance", "standard operating", "clause", "standard"]):
            text = self._sop_response(prompt_lower)
        elif any(kw in prompt_lower for kw in ["inspection", "report", "analyze", "findings", "corrosion", "defect", "deviation", "review"]):
            text = self._inspection_response(prompt_lower)
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
        prompt_lower = prompt.lower()
        if any(kw in prompt_lower for kw in ["pid", "p&id", "drawing", "diagram", "schematic", "flowsheet", "symbol", "piping"]):
            tags = re.findall(r"\b([A-Z]{1,3}-\d{2,5}[A-Z]?)\b", prompt)
            tag_str = f" including {', '.join(tags[:4])}" if tags else ""
            return (
                f"1. P&ID engineering schematic verified with legible instrumentation tags and equipment identifiers{tag_str}.\n"
                "2. Piping connections and line tracing identify distinct process, utility, and instrument signal lines per ISA-5.1.\n"
                "3. In-line isolation valves, control elements, and check valves are mapped to their respective piping runs.\n"
                "4. Equipment boundaries, suction/discharge paths, and nozzle connectivity match design flowsheets.\n"
                "5. No ungrounded line discontinuities or conflicting tag identifiers detected across the drawing."
            )
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
        prompt_lower = prompt.lower()
        tags = re.findall(r"\b([A-Z]{1,3}-\d{2,5}[A-Z]?)\b", prompt)
        eq_mention = f" ({', '.join(tags[:3])})" if tags else ""

        if any(kw in prompt_lower for kw in ["sop", "clause", "deviation", "compliance", "standard"]):
            tag_item = tags[0] if tags else "CV-102"
            return (
                f"Based on the technical documentation & SOP deviation review:\n"
                f"1. Critical Finding: Corroded main control valve {tag_item} showing 32.4% wall thickness loss, "
                f"exceeding the 30% replacement threshold per SOP-M-402 Section 3.\n"
                f"2. Critical Finding: Isolation boundary deviation detected per SOP-M-402 Section 2 "
                f"(Double Block and Bleed required on process line{eq_mention}).\n"
                f"3. Secondary Finding: Adjacent piping spool shows 31.4% wall loss requiring ASME B31.3 Para 304 evaluation.\n"
                f"4. Secondary Finding: Gasket reuse prohibited; Class 600 RTJ spiral wound gasket required per SOP-M-402 Section 3.\n"
                f"Risk Assessment: HIGH (Category A — Immediate Action Required)\n"
                f"Recommendation: Immediate isolation of {tag_item} loop and scheduled replacement per SOP-M-402.\n"
                f"Applicable Standards: ASME B31.3, API 570, SOP-M-402, SOP-M-104"
            )
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
        prompt_lower = prompt.lower()
        tag_match = re.search(r"\b([A-Z]{1,3}-\d{2,5}[A-Z]?)\b", prompt)
        if tag_match and any(w in prompt_lower for w in ["where", "locate", "location", "find", "coordinate", "position"]):
            tag = tag_match.group(1)
            return (
                f"**Equipment Location**: '{tag}' is identified in the engineering documentation and diagram. "
                f"Its symbol and alphanumeric tag are confirmed on the designated process piping line per ISA-5.1."
            )

        if any(w in prompt_lower for w in ["valve", "corrod", "sop-m-402"]):
            return (
                "### Standard Operating Procedure: Corroded Control Valve Replacement (SOP-M-402)\n\n"
                "**1. Scope & Pre-Job Hazard Analysis**\n"
                "Governs the isolation, removal, and replacement of severely corroded high-pressure control valves in refinery service.\n\n"
                "**2. Isolation & Lockout/Tagout (LOTO)**\n"
                "- Execute Double Block and Bleed (DBB) isolation on upstream and downstream process valves.\n"
                "- Apply physical locks and danger tags per SOP-SAF-001.\n"
                "- Verify zero residual pressure using calibrated local dial pressure gauges.\n"
                "- Allow complete cooldown of the line to ambient temperature (< 40°C) before loosening flange bolts.\n\n"
                "**3. Thickness Verification & Disassembly**\n"
                "- Conduct Ultrasonic Testing (UT) on mating flanges and adjacent pipe spools.\n"
                "- If remaining wall thickness is under 70% nominal (> 30% wall loss), flag adjacent spool for mandatory replacement per ASME B31.3.\n"
                "- Loosen bolts in star pattern; carefully support valve weight using approved overhead rigging.\n\n"
                "**4. Valve Installation & Gasket Protocol**\n"
                "- Discard old gaskets; NEVER reuse metallic or spiral wound gaskets.\n"
                "- Install certified 316L Stainless Steel Class 600 RTJ replacement valve.\n"
                "- Fit new ASME B16.20 316L/graphite spiral wound gasket with inner/outer retaining rings.\n"
                "- Torque bolts in 4-stage star pattern up to final specification (220 Nm for 3/4\" B7 studs).\n\n"
                "**5. Pressure Testing & Commissioning**\n"
                "- Perform hydrostatic leak test at 1.5x MAOP (63 bar) for 30 minutes with zero allowable pressure drop.\n"
                "- Verify valve stroke and actuator calibration (4-20 mA loop check) prior to process handover."
            )

        if any(w in prompt_lower for w in ["lock", "loto", "tagout", "electrical isolation"]):
            return (
                "### Standard Operating Procedure: Lockout/Tagout & Electrical Isolation (SOP-SAF-001)\n\n"
                "**Step 1: Preparation & Notification**\n"
                "Notify all affected operating personnel and control room operators of the scheduled equipment shutdown and maintenance scope.\n\n"
                "**Step 2: Equipment Shutdown**\n"
                "Execute controlled sequence shutdown using the local emergency stop or DCS console to bring rotating equipment to a complete standstill.\n\n"
                "**Step 3: Energy Source Isolation**\n"
                "Rack out circuit breakers in the Motor Control Center (MCC), open line disconnect switches, and close pneumatic/hydraulic isolation valves.\n\n"
                "**Step 4: Lock & Tag Application**\n"
                "Each technician must place their personal safety padlock and standardized Danger Tag directly onto the breaker lockout hasp.\n\n"
                "**Step 5: Stored Energy Dissipation**\n"
                "Discharge power capacitors, bleed residual hydraulic accumulators, and depressurize piping systems to zero gauge pressure.\n\n"
                "**Step 6: Zero Energy Verification (Live-Dead-Live Test)**\n"
                "Verify zero electrical energy using a calibrated multimeter/proximity tester: test against known live source, test target circuit (confirm 0V), and re-test live source."
            )

        if any(w in prompt_lower for w in ["threshold", "thickness", "wall", "trigger", "pipe replacement"]):
            return (
                "### Pipe & Component Replacement Thresholds (ASME B31.3 & SOP-M-402)\n\n"
                "**1. 30% Wall Loss Retirement Criterion**\n"
                "Per ASME B31.3 Section 304 and internal SOP-M-402, any piping component or valve body that exhibits greater than **30% wall thickness reduction** from nominal design thickness must be retired and replaced immediately.\n\n"
                "**2. Minimum Required Wall Thickness (t_min)**\n"
                "Formula: `t_min = (P * D) / (2 * (S * E + P * Y)) + C`\n"
                "Where P = design pressure, D = outside diameter, S = allowable stress, E = joint efficiency, Y = material factor, and C = corrosion allowance.\n"
                "If actual measured wall thickness `t_actual < t_min`, immediate derating or spool replacement is legally required.\n\n"
                "**3. Localized Pitting Tolerance**\n"
                "Isolated pitting pits exceeding 3.0 mm depth or localized wall thinning over an area greater than 100 mm in axial length requires adjacent spool replacement.\n\n"
                "**4. Mandatory Flange Integrity Review**\n"
                "Flange gasket seating surfaces with radial scores or corrosion exceeding 0.5 mm depth cannot be remachined on-site and must be replaced."
            )

        if any(w in prompt_lower for w in ["exchanger", "tube", "plug"]):
            return (
                "### Shell-and-Tube Heat Exchanger Tube Plugging Guidelines (TEMA / ASME Sec VIII)\n\n"
                "**1. Individual Tube Plugging Criteria**\n"
                "Tubes must be isolated and plugged whenever:\n"
                "- Non-Destructive Testing (Eddy Current / IRIS) detects wall thinning exceeding **40% of nominal wall thickness**.\n"
                "- Through-wall cracks or pinhole leaks are detected during tube-bundle helium leak or shell-side hydrostatic testing.\n"
                "- Pitting depth exceeds 0.8 mm on the process or cooling water interface.\n\n"
                "**2. Maximum Permissible Plugging Ratio (10% Rule)**\n"
                "- Up to **10% of total tubes** in a bundle may be plugged while maintaining acceptable process heat transfer margins.\n"
                "- Exceeding 10% plugged tubes severely reduces heat transfer surface area, increases tubeside pressure drop, and requires complete bundle replacement or re-tubing.\n\n"
                "**3. Plug Installation Requirements**\n"
                "- Tapered mechanical or ring-expandable plugs must match tube material metallurgy to eliminate galvanic corrosion.\n"
                "- Plugs must be seated and torque-driven or seal-welded per ASME Section VIII Div 1 Appendix A."
            )

        # Parse retrieved SOP context if present in prompt
        if "retrieved" in prompt_lower or "sop" in prompt_lower:
            return (
                "### Sovereign Engineering Assessment & Guidance\n\n"
                f"**Assessment of Objective**: {prompt.strip()[:150]}\n\n"
                "**Key Technical Findings & Standards**:\n"
                "1. **Governing Codes**: Work must comply strictly with ASME B31.3 (Process Piping), API 570 (Piping Inspection), and plant SOPs.\n"
                "2. **Safety & Isolation**: Mandatory Double Block and Bleed (DBB) isolation and full LOTO verification before opening process boundaries.\n"
                "3. **Material Specifications**: All replacement components must match or exceed design pressure/temperature classes (Class 600 RTJ, 316L SS for sour/corrosive service).\n"
                "4. **Quality Verification**: Mandatory 100% NDT inspection and hydrostatic pressure testing at 1.5x MAOP for minimum 30 minutes prior to sign-off."
            )

        return (
            "### Sovereign Technical Assessment & Answer\n\n"
            f"**Query**: {prompt.strip()[:150]}\n\n"
            "**Engineering Assessment**:\n"
            "1. **Technical Principles**: Evaluated against standard industrial engineering design codes and maintenance guidelines.\n"
            "2. **Operating Parameters**: Equipment must operate within verified design limits for temperature, pressure, and flow rates.\n"
            "3. **Integrity Management**: Component degradation must be monitored via scheduled ultrasonic testing, vibration analysis, and visual inspection.\n"
            "4. **Compliance & Verification**: All maintenance interventions must be documented with engineering sign-off and hydrotest verification under local plant procedures."
        )

    async def chat(
        self,
        messages: list,
        model: Any = None,
        **kwargs
    ) -> LLMGenerateResponse:
        """Mock chat response dynamically tailored to conversational input."""
        last_user = ""
        for m in reversed(messages):
            if isinstance(m, dict) and m.get("role") == "user":
                last_user = str(m.get("content", ""))
                break
        req = LLMGenerateRequest(prompt=last_user or "Engineering assistance", model=model or self.model_name)
        return await self.generate(req)

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
