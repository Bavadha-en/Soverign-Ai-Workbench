# Public Industrial Reference Documents & Knowledge Base Sources

This registry documents all public domain, government publication, open standard, and synthetic reference documents ingested into the ConfigIQ Sovereign Local Knowledge Base for SIH Problem Statement 26117.

In accordance with strict air-gap and IP governance policies:
- No confidential or proprietary client data is included.
- All documents originate from public government bodies, public engineering handbooks, or open technical references.
- All processing and RAG vector indexing occur 100% on-premise using local open-weight embedding models (nomic-embed-text:latest).

---

### Document 1: Centrifugal Pump Overhaul & Mechanical Seal Maintenance Standard (SOP-M-104)
- **Document**: Standard Operating Procedure: Centrifugal Pump Overhaul & Mechanical Seal Maintenance (SOP-M-104)
- **Publisher**: ConfigIQ Sovereign Industrial Engineering Standards (conforming to ISO 10816-3 Class II & API 610 11th Ed.)
- **URL**: https://www.iso.org/standard/53664.html / Synthetic Engineering Specification
- **License / Usage Note**: Public synthetic engineering standard based on public ISO 10816-3 vibration severity standards. Free for educational and demonstration purposes.
- **Why It Is Relevant**: Defines quantitative thresholds for centrifugal pump vibration (Zone A <1.8 mm/s, Zone B 1.8-4.5 mm/s, Zone C 4.5-7.1 mm/s, Zone D >7.1 mm/s), mechanical seal leakage limits (<5 drops/min), and shaft alignment tolerances (0.05 mm). Crucial for ground-truth verification of pump P-101 inspection findings.

---

### Document 2: In-Service Pressure Vessel Non-Destructive Inspection (SOP-INS-301)
- **Document**: Standard Operating Procedure: In-Service Pressure Vessel Non-Destructive Inspection (SOP-INS-301)
- **Publisher**: ConfigIQ Sovereign Engineering Guidelines (conforming to ASME Section VIII Div 1 & API 510 / API 579-1 Fitness-for-Service)
- **URL**: https://www.asme.org/codes-standards/find-codes-standards/bpvc-section-viii-rules-construction-pressure-vessels / Synthetic Guideline
- **License / Usage Note**: Public synthetic engineering standard based on ASME Boiler and Pressure Vessel Code and API 510 in-service rules.
- **Why It Is Relevant**: Specifies ultrasonic thickness (UT) grid scanning protocol, minimum required thickness formula (t_req = PR / (SE - 0.6P)), and defect severity categories for pressure vessels and separators.

---

### Document 3: Control Valve Overhaul & Seat Leakage Testing (SOP-VLV-202)
- **Document**: Standard Operating Procedure: Control Valve Overhaul, Actuator Calibration & Seat Leakage Testing (SOP-VLV-202)
- **Publisher**: ConfigIQ Sovereign Process Guidelines (conforming to ANSI/FCI 70-2 & API 598)
- **URL**: https://www.api.org/products-and-services/standards / Synthetic Guideline
- **License / Usage Note**: Public synthetic engineering specification for industrial valve overhaul and API 598 seat leakage testing.
- **Why It Is Relevant**: Governs valve seat leakage rates, stem packing torque, hysteretic calibration (3-15 psi / 4-20 mA), and hydrostatic testing requirements for valve repairs.

---

### Document 4: Process Piping System Corrosion & Thickness Inspection (SOP-PIP-405)
- **Document**: Standard Operating Procedure: Process Piping System Corrosion Inspection & Circuit Thickness Monitoring (SOP-PIP-405)
- **Publisher**: ConfigIQ Sovereign Plant Guidelines (conforming to API 570 & ASME B31.3)
- **URL**: https://www.api.org/standards / Synthetic Guideline
- **License / Usage Note**: Public synthetic operational procedure based on API 570 piping inspection standards.
- **Why It Is Relevant**: Governs Corrosion Under Insulation (CUI) monitoring, minimum structural thickness calculations, and circuit UT thickness baseline measurements.

---

### Document 5: Hazardous Energy Control & Electrical Isolation (SOP-SAF-001)
- **Document**: Standard Operating Procedure: Hazardous Energy Control & Electrical Isolation - Lockout/Tagout (LOTO) (SOP-SAF-001)
- **Publisher**: ConfigIQ Sovereign Safety Directorate (conforming to OSHA 29 CFR 1910.147)
- **URL**: https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.147
- **License / Usage Note**: Based on U.S. Federal Government OSHA standard 29 CFR 1910.147 (Public Domain).
- **Why It Is Relevant**: Mandatory pre-requisite for all physical equipment maintenance. Mandates zero energy state verification, try-step, group lockout, and double block and bleed (DBB) isolation.

---

### Document 6: DOE Fundamentals Handbook: Mechanical Science (Pumps & Valves)
- **Document**: DOE Fundamentals Handbook: Mechanical Science, Volume 1 (DOE-HDBK-1018/1-93)
- **Publisher**: U.S. Department of Energy (DOE)
- **URL**: https://www.standards.doe.gov/standards-documents/1000/1018-bhdbk-1993-v1
- **License / Usage Note**: Public Domain (Official U.S. Government Technical Work). Free for unlimited redistribution and reproduction.
- **Why It Is Relevant**: Authoritative public technical reference covering centrifugal pump operational principles, net positive suction head (NPSH), cavitation indicators, pump curves, and valve classifications.

---

### Document 7: OSHA Guidance: The Control of Hazardous Energy (Lockout/Tagout)
- **Document**: OSHA Publication 3120: Control of Hazardous Energy (Lockout/Tagout)
- **Publisher**: U.S. Department of Labor, Occupational Safety and Health Administration (OSHA)
- **URL**: https://www.osha.gov/sites/default/files/publications/osha3120.pdf
- **License / Usage Note**: Public Domain (U.S. Federal Government Publication).
- **Why It Is Relevant**: Authoritative federal guidance on establishing zero-energy states, energy control procedures, periodic inspections, and training requirements.

---

### Document 8: NASA Technical Publication: Structural Inspection & Pressure Vessel Criteria
- **Document**: NASA-STD-5009: Non-destructive Evaluation (NDE) Requirements for Pressure Vessels and Pressurized Systems
- **Publisher**: National Aeronautics and Space Administration (NASA)
- **URL**: https://standards.nasa.gov/standard/NASA/NASA-STD-5009
- **License / Usage Note**: Public Domain (NASA Open Technical Standards).
- **Why It Is Relevant**: Detailed public criteria for non-destructive examination (NDE), crack detection limits, ultrasonic calibration, and proof test margin standards.
