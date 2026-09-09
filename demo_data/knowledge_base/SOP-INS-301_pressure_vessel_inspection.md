# Standard Operating Procedure: In-Service Pressure Vessel Non-Destructive Inspection (SOP-INS-301)

## 1. Scope & Objective
Governs in-service and shutdown non-destructive examination (NDE), ultrasonic wall thickness profiling, and fitness-for-service evaluation for pressure vessels, separators, and storage drums conforming to ASME Boiler and Pressure Vessel Code Section VIII Division 1 and API 510.

## 2. Safety & Entry Requirements
- Confined Space Entry Permit (CSEP) required before vessel entry.
- Positive isolation via blind flanges / slip blinds on process lines.
- Multi-gas atmospheric testing: Oxygen 19.5% to 23.5%, LEL < 1%, H2S < 1 ppm, CO < 25 ppm.
- Continuous forced-draft mechanical air circulation throughout inspection.

## 3. Ultrasonic Thickness (UT) Grid Scanning
- Establish 100 mm x 100 mm inspection grid across shell plates, ellipsoidal heads, bottom sump, and vapor-liquid interface.
- Calibrate ultrasonic gauge with certified step wedge blocks matching SA-516 Gr 70 carbon steel.
- Calculate required minimum wall thickness per ASME Section VIII Div 1:
  t_req = (P * R) / (S * E - 0.6 * P)
  where P = MAWP (MPa), R = inside radius (mm), S = allowable stress (MPa), E = joint efficiency (1.0 for full radiography).

## 4. Defect Categorization & Action Thresholds
- **LOW / NORMAL**: Actual thickness t_act >= t_req + Corrosion Allowance. Routine 5-year cycle.
- **MEDIUM / REMEDIATE**: t_req < t_act < t_req + CA. Calculate corrosion rate and remaining life. Re-inspect within 12 months.
- **CRITICAL / IMMEDIATE ACTION**: Actual thickness t_act < t_req or localized wall loss > 35%. Vessel must be immediately depressurized, isolated, and derated or repaired via ASME code-qualified weld overlay.

## 5. Weld & Nozzle Inspection
- 100% Wet Fluorescent Magnetic Particle Testing (WFMT) on internal nozzle fillet welds.
- Phased Array Ultrasonic Testing (PAUT) on circumferential and longitudinal seams.
