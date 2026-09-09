# Standard Operating Procedure: Hazardous Energy Control & Electrical Isolation LOTO (SOP-SAF-001)

## 1. Scope & Objective
This procedure specifies the mandatory safety requirements for establishing an electrically safe work condition and implementing Lockout/Tagout (LOTO) protocols for low-voltage (480V) and medium-voltage (up to 13.8kV) switchgear, motor control centers (MCC), variable frequency drives (VFD), and power distribution transformers, strictly enforcing OSHA 29 CFR 1910.147 and NFPA 70E standards.

## 2. Authorized Personnel & Personal Protective Equipment (PPE)
- Only certified Qualified Electrical Personnel (QEP) who have completed annual high-voltage safety certification are authorized to perform switching, racking, and grounding operations.
- Minimum PPE based on calculated Arc Flash Incident Energy:
  - **Category 2 (≤ 8 cal/cm²)**: Arc-rated long-sleeve shirt and pants, arc-rated face shield with balaclava, safety glasses, Class 0 (1000V) dielectric rubber gloves with leather protectors.
  - **Category 4 (> 25 to 40 cal/cm²)**: Full 40-cal arc flash suit with hood and forced air ventilation, safety helmet, dielectric rubber gloves (Class 2 or 4), steel-toe EH dielectric boots.

## 3. The 6-Step Mandatory Electrical Isolation Lifecycle
1. **Preparation & System Identification**: Review single-line electrical diagrams (SLD). Identify all primary, secondary, and emergency backup power feeds, control power transformers (CPT), and interlocks.
2. **Operational Notification**: Formally notify unit operations supervisor and control room operators before initiating breaker trips or equipment isolation.
3. **Controlled Equipment Shutdown**: De-energize load using normal local or SCADA stop controls before opening isolating disconnects.
4. **Physical Disconnection & Rack-Out**:
   - Trip the main circuit breaker.
   - For drawout switchgear, rack breaker out to the TEST/DISCONNECTED position with racking shutter locked closed.
   - Open and visually verify physical separation of air-gap knife disconnect switches where installed.
5. **Stored Energy Dissipation & Grounding**:
   - Discharge all high-voltage capacitor banks and VFD DC bus capacitors; wait mandatory 10-minute bleed-down time.
   - Attach certified portable safety grounding clusters from phase conductors to station ground bus.
6. **Zero Energy Verification (Live-Dead-Live Test)**:
   - Verify calibrated high-voltage proximity detector/voltmeter on a known energized source.
   - Test every phase-to-phase and phase-to-ground conductor on the isolated equipment to confirm 0.0V.
   - Re-verify voltmeter on the known energized source to confirm instrument functionality.

## 4. Padlocking & Hazard Tag Placement
- Each authorized technician must attach their personal red safety padlock and durable lockout tag to the multi-lock hasp on the breaker disconnect handle or racking port.
- Hazard tags must clearly state: Technician Name, Department, Date/Time, Equipment ID, Contact Phone, and Specific Work Order Number.
- Master keys are strictly prohibited; each technician retains sole custody of their individual padlock key.

## 5. Complex LOTO & Group Lockbox System
- For large multi-craft turnaround maintenance, designated Lead Electrical Isolator executes isolation and places all equipment keys inside a centralized Group Lockbox.
- Each discipline supervisor and field worker attaches their personal padlock to the outside of the Lockbox. No isolated equipment can be re-energized until the final individual padlock is removed.

## 6. De-Isolation & System Re-Energization Protocol
- Inspect work area: Ensure all tools, test leads, and grounding jumpers have been removed.
- Re-install all arc-resistant panel barriers, dead-front covers, and interlocks.
- Notify all personnel in the area that equipment is being re-energized.
- Remove individual locks and tags in reverse sequence.
- Rack breaker in, close disconnect switch, and verify nominal phase voltages and phase sequence before starting motor.
