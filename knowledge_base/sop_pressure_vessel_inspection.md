# Standard Operating Procedure: In-Service Pressure Vessel Non-Destructive Inspection (SOP-INS-301)

## 1. Scope & Objective
This procedure governs in-service and out-of-service non-destructive testing (NDT), ultrasonic thickness measurement, and fitness-for-service evaluation for industrial pressure vessels, separators, and storage drums (PV-200 and PV-300 series) conforming to ASME Boiler & Pressure Vessel Code Section VIII and API 510.

## 2. Safety Precautions & Confined Space Entry
- Obtain Confined Space Entry Permit (CSEP) and Hot Work Permit before vessel opening.
- Execute positive physical isolation using slip blinds / spectacle flanges on all process inlet, outlet, and relief nozzle lines.
- Perform atmospheric testing: Oxygen (19.5% – 23.5%), LEL < 1%, H2S < 1 ppm, CO < 25 ppm.
- Continuous forced-air mechanical ventilation required throughout inspection.
- Personnel entering vessel must wear multi-gas detectors and full fall arrest harness if height > 1.8 m.

## 3. Ultrasonic Thickness (UT) Grid Scanning Protocol
- Mark a 100 mm x 100 mm grid across shell plates, ellipsoidal heads, bottom sumps, and liquid-vapor interface zones.
- Calibrate digital ultrasonic thickness gauge (A-scan/B-scan) with certified step wedge blocks matching vessel metallurgy (e.g., SA-516 Grade 70 carbon steel).
- Measure minimum remaining wall thickness ($t_{\text{act}}$) across all grid coordinates.
- Calculate required minimum wall thickness per ASME Section VIII Div 1:
  $$t_{\text{req}} = \frac{P \cdot R}{S \cdot E - 0.6 P}$$
  where:
  - $P$ = Maximum Allowable Working Pressure (MAWP, MPa)
  - $R$ = Inside radius of vessel shell (mm)
  - $S$ = Maximum allowable stress value (MPa)
  - $E$ = Joint efficiency factor (1.0 for 100% radiographic examination)

## 4. Defect Categorization & Fitness-for-Service (API 579-1 / ASME FFS-1)
- **LOW / MONITOR**: Remaining thickness $t_{\text{act}} \ge t_{\text{req}} + \text{Corrosion Allowance (CA)}$. Continue standard 5-year inspection cycle.
- **MEDIUM / REMEDIATE**: Remaining thickness $t_{\text{req}} < t_{\text{act}} < t_{\text{req}} + \text{CA}$. Calculate corrosion rate ($C_R$) and remaining life ($RL = \frac{t_{\text{act}} - t_{\text{req}}}{C_R}$). Schedule re-inspection within 12 months.
- **CRITICAL / IMMEDIATE ACTION**: Remaining thickness $t_{\text{act}} < t_{\text{req}}$ (or wall thinning $> 35\%$). Vessel must be immediately depressurized, isolated, and derated or repaired via ASME code-qualified weld overlay / spool replacement.

## 5. Non-Destructive Examination of Welds & Nozzles
- **Magnetic Particle Testing (MT / WFMT)**: Perform 100% wet fluorescent magnetic particle inspection on internal nozzle attachment welds and shell longitudinal/circumferential weld seams to detect stress corrosion cracking (SCC) and hydrogen-induced blisters.
- **Phased Array Ultrasonic Testing (PAUT)**: Inspect critical high-stress weld joints for sub-surface volumetric flaws and lack of fusion.
- **Visual Inspection (VT)**: Inspect internal cladding, demister pads, vortex breakers, and tray support rings for erosion and detachment.

## 6. Proof Hydrostatic Pressure Testing & Certification
- After structural repairs or weld overlay, conduct hydrostatic proof test at 1.3x revised design pressure per ASME Sec VIII UG-99.
- Hold test pressure for minimum 30 minutes; inspect all welded joints for leakage or permanent plastic deformation.
- Issue stamped Inspection Compliance Certificate and update Asset Integrity Management Database.
