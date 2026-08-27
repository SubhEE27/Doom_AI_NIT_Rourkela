# DOOM AI
## Modular OOP Clinical Decision-Support Prototype for Emergency Department Triage

DOOM AI is a modular, object-oriented prototype for **PatientTriage.ai â€” Problem Statement 2** of the Accenture Innovation Challenge.

The central design goal is to help an emergency department prioritize and route arriving patients during normal operation and surge conditions while keeping the final clinical decision with a licensed clinician.

The supplied challenge statement asks for an AI-powered triage assistant that helps staff prioritize and route patients as they arrive, reduces waiting times, does not replace clinical judgment, uses information realistically available in the first few minutes, and is designed for the worst case rather than only the average case.

> **Clinical safety notice:** This repository is a prototype for innovation, architecture and simulation. It is **not a clinically validated ESI implementation, diagnostic device, treatment recommendation engine, or production hospital system**. Physiological thresholds, triage rules, transfer logic and confidence calculations must be validated against institution-approved clinical protocols before any real-patient use.

---

# 1. What We Built

Doom is deliberately separated into independent modules instead of placing the complete application in one Python file.

The system has three major responsibilities:

1. **Clinical decision-support core** â€” converts first-minute patient information into a conservative triage recommendation.
2. **Hospital operations layer** â€” adapts execution to resource availability, bed/OT occupancy, imaging availability and staffing.
3. **Presentation/integration layer** â€” exposes the same engine to a Qt UI, tests and a FHIR-shaped adapter.

The architecture is designed so that the clinical engine can remain unchanged while the frontend or hospital integration is replaced later.

---

# 2. High-Level System Architecture

```text
                         DOOM AI
                                â”‚
                â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                â”‚               â”‚                â”‚
                â–¼               â–¼                â–¼
          Patient Input     Hospital State    Staff State
                â”‚               â”‚                â”‚
                â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                â–¼
                       DoomTriageEngine
                                â”‚
          â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
          â”‚                     â”‚                     â”‚
          â–¼                     â–¼                     â–¼
   Ingestion Engine      Risk Stratifier       Layer Controller
          â”‚                     â”‚                     â”‚
          â–¼                     â–¼                     â–¼
   Demographic Cohort     SI / SIPA-like       L1 / L2 / L3 / L4
   + Missing Data         Pulse Pressure       operational mode
                                â”‚
                                â–¼
                         Triage Model
                                â”‚
                                â–¼
                         Safety Floor
                                â”‚
                                â–¼
                       Uncertainty Engine
                                â”‚
             â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
             â–¼                  â–¼                  â–¼
       Clinical Route     Transfer Planner   Staff Orchestrator
             â”‚                  â”‚                  â”‚
             â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
                                â–¼
                       TriageRecommendation
                                â”‚
                â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¼â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
                â–¼               â–¼                â–¼
             Qt UI         FHIR Adapter       Audit Log
```

The UI is therefore a **consumer of the engine**, not the owner of the clinical logic.

---

# 3. Why the Code Is Split into Multiple Directories

A hospital AI should not have clinical rules, UI code, audit logic and test data mixed together.

The modular structure gives us:

- **Separation of concerns** â€” each class has a defined responsibility.
- **Reusability** â€” the same engine can be called from Qt, REST/FHIR, mobile or another hospital application.
- **Testability** â€” each module can be tested independently.
- **Scalability** â€” the number of patients does not have to be built into the clinical engine.
- **Maintainability** â€” changing the UI does not require changing triage logic.
- **Safer change management** â€” a change to routing does not require rewriting audit storage or the UI.

---

# 4. Complete Folder Structure

```text
Doom-Ready/
â”‚
â”œâ”€â”€ README.md
â”œâ”€â”€ requirements.txt
â”‚
â”œâ”€â”€ doom/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ main.py
â”‚   â”‚
â”‚   â”œâ”€â”€ config/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ settings.py
â”‚   â”‚
â”‚   â”œâ”€â”€ models/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ domain.py
â”‚   â”‚
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ ingestion.py
â”‚   â”‚   â”œâ”€â”€ stratification.py
â”‚   â”‚   â”œâ”€â”€ scoring.py
â”‚   â”‚   â”œâ”€â”€ uncertainty.py
â”‚   â”‚   â”œâ”€â”€ layers.py
â”‚   â”‚   â””â”€â”€ routing.py
â”‚   â”‚
â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â”œâ”€â”€ engine.py
â”‚   â”‚   â”œâ”€â”€ audit.py
â”‚   â”‚   â”œâ”€â”€ arrival_stream.py
â”‚   â”‚   â””â”€â”€ demo.py
â”‚   â”‚
â”‚   â”œâ”€â”€ api/
â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚   â”‚   â””â”€â”€ fhir.py
â”‚   â”‚
â”‚   â””â”€â”€ ui/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ app.ui
â”‚       â””â”€â”€ main_window.py
â”‚
â””â”€â”€ tests/
    â””â”€â”€ test_harness.py
```

---

# 5. Module-by-Module Explanation

## 5.1 `doom/config/settings.py`

This file contains configuration tokens that should remain separate from the clinical engine.

### Deployment profiles

```python
MULTISPECIALTY_TERTIARY_CENTER
RURAL_PRIMARY_HEALTH_CENTRE
```

These allow the same software architecture to adapt to very different hospital environments.

### Permission tokens

```text
BED_MANAGEMENT_SYSTEM
STAFF_ROSTER_DB
INSTRUMENT_INVENTORY
```

These represent infrastructure access domains rather than patient consent.

The engine uses a runtime permission state map to simulate an explicit access handshake before operational data are used.

### Scalability assumptions

```python
SUPPORTED_DAILY_ED_MIN = 100
REFERENCE_DAILY_ED_MAX = 500
EXPECTED_HISTORY_RATIO = 0.50
```

These values represent the challenge's assumed operating envelope. They are configuration references, not a hard limit on the number of patients the software can process.

---

# 6. `doom/models/domain.py` â€” Data Model Layer

This module contains the central domain objects used throughout the system.

## `PatientRecord`

Represents one arriving ED patient.

It can contain:

- patient ID
- age
- sex
- chief complaint
- clinical narrative
- prior-history availability
- comorbidities
- medications
- vitals
- labs
- imaging metadata/tags
- demographic tags
- onset information
- trauma information
- pregnancy flag
- file availability

The important design decision is that **history is optional**.

A patient does not need an existing hospital record for the engine to operate.

---

## `HospitalAssets`

Represents the current operational environment:

- bandwidth
- 5G telemetry
- POCUS status
- imaging pipeline status
- bed occupancy
- OT occupancy
- ED waiting time
- local capacity
- current ED volume
- normal ED volume
- network latency
- daily ED visits
- nearby facilities

It also exposes:

```python
imaging_online
resource_surge_ratio
```

which are used by the layer controller.

---

## `StaffRoster`

Represents staffing at the time of evaluation.

It records:

- shift
- emergency physicians
- nurses
- generalists
- on-call doctors
- specialty availability
- minimum staffing thresholds

The engine uses this to determine whether Layer 4 should be activated.

---

## `RiskAssessment`

Contains the intermediate clinical reasoning features:

- Shock Index
- Shock/SIPA-like label
- pulse pressure
- abnormal vital flags
- critical flags
- possible dangerous syndromes
- missing critical fields
- ambiguity flags
- data completeness

This object separates **risk features** from the final triage recommendation.

---

## `TriageRecommendation`

This is the main output consumed by the UI/API.

It contains:

- patient ID
- ESI level 1â€“5
- exactly three rationale entries
- system confidence indicator
- active operational layer
- risk assessment
- routing recommendation
- transfer-candidate flag
- specialist route
- uncertainty indicator
- clinician-override status

---

# 7. Core Clinical/Decision Modules

## 7.1 `core/ingestion.py` â€” First-Minute Data Ingestion

### Class

```python
IngestionEngine
```

### Main functions

```text
infer_cohort()
_clean_numeric()
normalize()
```

### What it does

The engine receives a raw `PatientRecord` and normalizes it before clinical logic is applied.

It:

1. Determines the age cohort.
2. Converts incoming vital values to safe numeric values.
3. Detects missing critical fields.
4. Creates baseline proxy metadata for uncertainty handling.
5. Normalizes narrative/complaint text.
6. Preserves the fact that critical values were missing.

### Important safety behavior

Missing vitals are **not silently replaced and then treated as real measurements**.

A proxy is only used as a software feature for uncertainty handling. The original field remains missing and can activate the pessimistic safety floor.

---

# 8. `core/stratification.py` â€” Demographic-Calibrated Risk Engine

### Class

```python
RiskStratifier
```

This module addresses one of the central problems in the prototype: the risk of applying one adult rule set to every age group.

## Four age cohorts

```text
< 1 year       â†’ Neonate/Infant
1â€“12 years     â†’ Pediatric
13â€“64 years    â†’ Adult
>= 65 years    â†’ Geriatric
```

Each cohort has its own configured demonstration bands for:

- HR
- RR
- SBP
- DBP
- SpO2

These are prototype thresholds and must be replaced/validated clinically before deployment.

---

## Shock Index

The system calculates:

```text
Shock Index = Heart Rate / Systolic Blood Pressure
```

For younger cohorts the output is labelled SIPA-like where appropriate.

The prototype uses an escalation-oriented rule rather than treating the index as an autonomous diagnosis.

---

## Pulse Pressure

The system calculates:

```text
Pulse Pressure = SBP - DBP
```

A narrow pulse pressure condition is recorded as a critical signal when the configured prototype threshold is crossed.

Again, this is a decision-support feature, not proof of a specific disease.

---

## NLP-style symptom tokenization

The prototype performs rule-based text matching against symptom/syndrome groups such as:

- chest symptoms
- dyspnea
- neurologic symptoms
- infection
- bleeding
- anaphylaxis
- trauma
- metabolic emergencies
- pregnancy-related emergencies

The result is a **guarded differential/syndrome signal**, not a final diagnosis.

The text parser also attempts to recognize basic negation such as:

```text
no chest pain
without dyspnea
denies bleeding
```

so that an explicitly denied symptom is not automatically treated as positive.

---

# 9. `core/scoring.py` â€” Triage Severity Engine

### Classes

```text
SafetyFloor
TriageModel
```

## Triage Model

The current output is a five-level ESI-like severity scale:

```text
ESI 1 â†’ immediate life threat
ESI 2 â†’ very high urgency / high-risk presentation
ESI 3 â†’ moderate/high resource need
ESI 4 â†’ lower acuity
ESI 5 â†’ lowest prototype acuity
```

The implementation intentionally does **not claim to reproduce the official ESI algorithm**.

It is a competition prototype that uses a familiar 1â€“5 output so that hospitals can understand the recommendation without abandoning their existing triage framework.

---

# 10. Safety-First Pessimistic Floor

One of the most important architectural decisions is that uncertainty can **increase urgency**.

The rule is conceptually:

```text
Missing critical data
        OR
Highly ambiguous presentation
        â†“
Increase uncertainty
        â†“
Apply pessimistic safety floor
        â†“
Minimum recommended ESI = 2
        â†“
Human clinician rule-out
```

This is designed to prevent the AI from confidently placing a patient into a low-acuity path when important information is unavailable.

The floor does not downgrade an existing ESI-1 recommendation.

---

# 11. `core/uncertainty.py` â€” Uncertainty Indicator

### Class

```python
UncertaintyEstimator
```

The prototype generates an uncertainty indicator from factors such as:

- missing critical vitals
- ambiguous presentation
- unavailable history/files
- limited supporting data
- simple internal consistency checks

The UI converts that into a confidence-style percentage.

### Important distinction

```text
System confidence â‰  probability the diagnosis is correct
```

It is an engineering uncertainty indicator for the prototype and must not be presented to clinicians as a validated probability of clinical outcome.

---

# 12. Four-Layer Polymorphic Operational Engine

## `core/layers.py`

### Class

```python
PolymorphicController
```

This is the operational brain of the architecture.

Instead of assuming every ED has identical infrastructure, the controller selects an execution mode based on the real-time hospital state.

---

## LAYER 1 â€” Full-Resource Modern Omni-Mode

Identifier:

```text
L1-FULL-RESOURCE-OMNI
```

Activated when the prototype sees:

- high-speed bandwidth
- 5G telemetry
- POCUS availability
- imaging pipeline availability

Purpose:

```text
Use richer data when the hospital actually has it.
```

The architecture supports image metadata/tags as part of the input model. A production implementation would connect those tags to validated POCUS/eFAST/image-processing services.

The current repository does **not** contain a medical computer-vision model or direct video interpretation engine.

---

## LAYER 2 â€” Asymmetric Low-Resource Shield

Identifier:

```text
L2-ASYMMETRIC-LOW-RESOURCE-SHIELD
```

Triggered when:

- imaging is offline
- prior history is unavailable
- hospital technology is degraded
- deployment profile is rural PHC

Purpose:

```text
Keep triage operational even when advanced data disappear.
```

The system relies primarily on:

- current vitals
- chief complaint
- clinical narrative
- demographic context
- available basic metadata

This is what we mean by breaking the **Symmetrical Data Trap**: the AI must not assume that every patient arrives with the same amount of information.

---

## LAYER 3 â€” Network-Aware Transit Offloader

Identifier:

```text
L3-NETWORK-AWARE-TRANSIT-OFFLOADER
```

Triggered when local capacity is exhausted, especially when:

```text
Bed occupancy = 100%
OR
OT occupancy = 100%
```

The system evaluates a simplified Time-to-Treatment comparison:

```text
Local pathway time
        VS
Transfer dispatch
+ travel
+ receiving wait
```

A transfer candidate is produced only for lower-acuity/stable candidates when the transfer pathway is materially faster and a receiving facility is available within the configured radius.

### Important safety rule

The prototype does **not auto-transfer high-acuity patients**.

Transfer remains a clinician-controlled decision.

The repository's demonstration facility data use a nearby facility at approximately 3.5 km.

---

## LAYER 4 â€” Predictive Staff & OT Orchestrator

Identifier:

```text
L4-PREDICTIVE-STAFF-ORCHESTRATOR
```

Triggered by:

- night/overnight shift
- shortage of emergency physicians
- shortage of nurses

Purpose:

```text
Match high-risk patients to whatever qualified staff are actually available.
```

The prototype can generate actions such as:

- specialist push-page suggestion
- emergency physician escalation
- generalist-led holding sequence for lower-acuity patients

The current repository models the paging/dispatch decision but does **not send a real SMS/pager notification**.

---

# 13. Rural Primary Health Centre Deployment Lock

The configuration layer supports:

```text
MULTISPECIALTY_TERTIARY_CENTER
RURAL_PRIMARY_HEALTH_CENTRE
```

For:

```text
RURAL_PRIMARY_HEALTH_CENTRE
```

the controller is hard-locked to:

```text
L2
```

This prevents the system from pretending that advanced imaging or high-bandwidth capabilities exist at a low-resource deployment.

This is an architectural scalability feature, not a clinical severity rule.

---

# 14. Runtime Infrastructure Permission Handshake

The main engine maintains explicit runtime access states for:

```text
BED_MANAGEMENT_SYSTEM
STAFF_ROSTER_DB
INSTRUMENT_INVENTORY
```

The method:

```python
request_system_access_permissions(tokens_list)
```

simulates an explicit runtime authorization step.

Before infrastructure-dependent evaluation is allowed, the required flags must be authorized.

Otherwise the engine raises:

```python
PermissionError
```

### Important distinction

These are **system/infrastructure access permissions**.

They are not the same thing as patient consent or a legal basis for processing personal data.

---

# 15. Manual Clinician Entry Router

The engine provides:

```python
process_manual_clinician_entry(
    patient_record,
    data_category,
    payload_dict,
)
```

The supported categories are:

```text
VITAL_SIGNS
CLINICAL_NARRATIVE
IMAGING_METADATA
```

## `VITAL_SIGNS`

Allows a nurse/clinician workflow to update values such as:

- HR
- RR
- SBP
- DBP
- SpO2

## `CLINICAL_NARRATIVE`

Allows additional bedside text/keyword information to be attached to the patient presentation.

## `IMAGING_METADATA`

Allows point-of-care imaging findings to be added as structured metadata/tags.

Every manual update is also written to the audit chain.

---

# 16. Dynamic Patient Arrival Architecture

## `services/arrival_stream.py`

### Class

```python
ArrivalStream
```

This is important for real ED deployment.

The system does **not** assume:

```text
10 patients
50 patients
100 patients
500 patients
```

Instead, `ArrivalStream` accepts an iterable of however many patients have actually arrived.

Conceptually:

```text
Registration / Triage Event
          â†“
      ArrivalStream
          â†“
      PatientRecord
          â†“
  DoomTriageEngine
```

Therefore:

```text
3 arrivals   â†’ process 3
17 arrivals  â†’ process 17
126 arrivals â†’ process 126
500 arrivals â†’ process 500
```

The clinical engine contains no hardcoded patient count.

---

# 17. 50:50 History Availability Assumption

The challenge assumption is approximately half of arriving patients have some prior health record while half do not.

We implement this as a **deployment assumption/monitoring statistic**, not a hard system requirement.

`HistoryMixMonitor` reports:

```text
Total arrivals
With history
Without history
With-history percentage
Without-history percentage
```

### Example

```text
10 arrivals
5 with history
5 without history
```

works.

But the engine will also continue working with:

```text
20 arrivals
7 with history
13 without history
```

The system must never reject a patient because the population is not exactly 50:50.

That is the intended real-world behavior.

---

# 18. Hospital Scale: 100 to 500+ ED Visits/Day

`HospitalAssets.daily_ed_visits` allows the hospital deployment scale to be represented explicitly.

The current configuration defines a reference range of approximately:

```text
100 ED visits/day
        â†“
250 ED visits/day
        â†“
500+ ED visits/day
```

This is a capacity/deployment parameter rather than a processing limit.

The real-time surge calculation is based on:

```text
current_ed_volume
------------------
normal_ed_volume
```

so a simulated:

```text
100 â†’ 300
```

produces a 3Ã— volume surge.

The same architecture can process larger batches because patient count is not embedded in the clinical classes.

---

# 19. `services/routing.py` â€” Operational Routing

This module contains two major services.

## `ClinicalRouting`

Maps symptom/presentation signals to a suggested specialty path such as:

- neurology/stroke
- cardiology/acute care
- obstetrics
- trauma surgery
- critical care

These are recommendations for staff workflow, not autonomous consultation orders.

## `TransferPlanner`

Evaluates local vs external treatment pathway time and searches configured nearby facilities.

The prototype checks:

- receiving capacity
- distance
- dispatch delay
- travel time
- receiving wait
- local ED wait

---

# 20. `services/engine.py` â€” Main Orchestrator

This is the central OOP service:

```python
DoomTriageEngine
```

It composes the other classes instead of implementing everything itself.

A simplified flow inside `evaluate()` is:

```text
1. Receive PatientRecord
        â†“
2. Normalize input
        â†“
3. Infer demographic cohort
        â†“
4. Evaluate vitals / SI / pulse pressure
        â†“
5. Extract dangerous symptom syndromes
        â†“
6. Select operational layers
        â†“
7. Generate ESI-like recommendation
        â†“
8. Apply pessimistic safety floor
        â†“
9. Calculate uncertainty/confidence
        â†“
10. Generate rationale
        â†“
11. Generate specialty route
        â†“
12. Evaluate transfer candidate
        â†“
13. Evaluate staff orchestration
        â†“
14. Write audit event
        â†“
15. Return TriageRecommendation
```

This class is the main object that the frontend should call.

---

# 21. `services/audit.py` â€” Clinical Accountability

The audit subsystem uses a hash chain.

Each event stores:

```text
Event ID
Timestamp
Patient ID
Actor type
Action
Payload
Previous hash
Current hash
```

The relationship is:

```text
Event 1
  â”‚
  â””â”€â”€ hash â†’ Event 2
              â”‚
              â””â”€â”€ hash â†’ Event 3
                           â”‚
                           â””â”€â”€ hash â†’ Event 4
```

The method:

```python
verify_chain()
```

recalculates the chain and verifies integrity.

---

# 22. Clinician-in-the-Loop Override

The engine provides:

```python
clinician_override(...)
```

A clinician can replace the AI recommendation, but the override requires:

- clinician ID
- new ESI level
- structured justification code
- free-text clinical explanation

The resulting audit event records:

```text
AI ESI
New ESI
Clinician identity
Reason code
Reason narrative
AI confidence
Operational layer
```

This preserves human clinical authority.

### Example flow

```text
AI â†’ ESI 3
      â†“
Clinician bedside review
      â†“
Override â†’ ESI 2
      â†“
Reason code + explanation
      â†“
Audit event
```

---

# 23. `api/fhir.py` â€” Integration Boundary

This module provides a lightweight FHIR-shaped representation:

```python
patient_to_fhir_bundle(patient, recommendation)
```

The current adapter creates a collection `Bundle` containing:

- Patient
- Observation
- ServiceRequest

This demonstrates how the internal domain model can be translated into an interoperability representation.

### Important limitation

This is a **FHIR-shaped prototype adapter**, not a complete HL7 FHIR server.

Production interoperability would require:

- a real HTTP API
- FHIR resource validation
- authentication/authorization
- terminology mapping
- versioning
- error handling
- hospital-specific profile conformance
- secure transport
- persistence
- integration with the hospital EHR/HIS

---

# 24. UI Layer

## `ui/app.ui`

This is the Qt Designer layout file.

It keeps the visual design separate from the clinical logic.

The current interface exposes fields for:

- Patient ID
- Age
- Sex
- Chief complaint
- Narrative
- History availability
- HR
- RR
- SBP
- DBP
- SpO2

and buttons for:

- system permission authorization
- triage evaluation

The result area displays:

- ESI
- active layer
- confidence
- rationale
- routing recommendation

---

## `ui/main_window.py`

### Class

```python
MainWindowController
```

This controller:

1. Loads `app.ui`.
2. Connects button events.
3. Converts form values into `PatientRecord`.
4. Calls `DoomTriageEngine.evaluate()`.
5. Displays the returned recommendation.
6. Displays errors through the UI.

The controller does **not** implement the clinical rules.

That separation is essential.

---

# 25. `main.py` â€” Application Entry Point

`python -m doom.main` starts the Qt application.

The main sequence is:

```text
QApplication
    â†“
DoomTriageEngine
    â†“
Hospital demo configuration
    â†“
Staff demo configuration
    â†“
MainWindowController
    â†“
app.ui
```

---

# 26. Test Harness

## `tests/test_harness.py`

The test harness checks the architecture rather than simply testing one patient.

The current tests include:

1. Infrastructure access is blocked before permissions are granted.
2. Required infrastructure permissions can be explicitly authorized.
3. A dynamic arrival stream can process multiple patients.
4. A 10-patient demonstration can contain 5 with history and 5 without history.
5. No-history patients do not break triage evaluation.
6. ESI outputs stay within 1â€“5.
7. A FHIR-shaped Bundle can be generated.
8. Manual vital-sign entry works.
9. Manual narrative entry works.
10. Manual imaging metadata entry works.
11. Rural PHC deployment locks to L2.
12. Clinician override works.
13. Override is recorded in the audit trail.
14. Audit hash-chain integrity remains valid.
15. Hospital scale can be represented as 500 ED visits/day.

The current harness intentionally uses a 10-patient batch as a **test scenario only**. The production-facing `ArrivalStream` does not depend on a predefined count.

---

# 27. Typical End-to-End Patient Journey

Assume a patient arrives at the ED.

```text
Patient arrives
      â†“
Registration / triage input
      â†“
Is prior record available?
      â”‚
      â”œâ”€â”€ Yes â†’ use available history
      â”‚
      â””â”€â”€ No  â†’ continue with first-minute data
                     â†“
             IngestionEngine
                     â†“
             Age cohort detection
                     â†“
             Vital normalization
                     â†“
             RiskStratifier
                     â†“
        HR/RR/BP/SpO2 + SI + PP
                     â†“
           NLP symptom signals
                     â†“
            TriageModel
                     â†“
            Safety Floor
                     â†“
          Uncertainty Engine
                     â†“
         Layer Controller
                     â†“
       Routing / Transfer / Staff
                     â†“
            Recommendation
                     â†“
         Clinician assessment
                     â†“
             â”Œâ”€â”€â”€â”€â”€â”€â”´â”€â”€â”€â”€â”€â”€â”
             â”‚             â”‚
          Accept         Override
             â”‚             â”‚
             â””â”€â”€â”€â”€â”€â”€â”¬â”€â”€â”€â”€â”€â”€â”˜
                    â†“
                Audit Log
```

---

# 28. Mass-Casualty / Surge Behavior

During a surge, hospital state changes.

Example:

```text
Normal ED volume = 100
Current volume   = 300

Surge ratio = 300 / 100 = 3.0Ã—
```

At the same time:

```text
Bed occupancy = 100%
OT occupancy  = 100%
Night shift   = yes
Staff deficit = yes
```

The controller can therefore activate:

```text
L2 or L1
  +
L3
  +
L4
```

depending on actual data availability.

The resulting recommendation can include:

- specialist route
- holding sequence
- transfer candidate
- emergency escalation

---

# 29. What Each Layer Is Solving

| Layer | Problem | Main Solution |
|---|---|---|
| L1 | Rich-resource ED has advanced telemetry/imaging | Use richer available inputs |
| L2 | Missing history/imaging/resource degradation | Continue safely using asymmetric first-minute data |
| L3 | Hospital capacity is exhausted | Compare local vs transfer treatment time |
| L4 | Specialist/staff shortage | Allocate scarce qualified staff and hold lower-acuity patients safely |

The layers are **operational modes**, not four separate disease classifiers.

---

# 30. What the Prototype Does Not Yet Do

The architecture deliberately exposes where further development is required.

## Not yet production-grade

### Real EHR integration
The current project does not connect directly to a hospital HIS/EHR.

### Real FHIR server
The FHIR module is a lightweight adapter, not a full FHIR server.

### Real-time paging
Layer 4 produces routing decisions but does not connect to a real paging gateway.

### Real medical computer vision
L1 accepts imaging metadata/tags but does not contain a validated POCUS/eFAST vision model.

### Production database
The audit log currently uses an in-process append-only structure rather than a production immutable/WORM store.

### Encryption and key management
A production implementation would need TLS, encryption at rest, managed keys/HSM where appropriate, secret rotation and strong identity management.

### Clinical validation
No threshold or model in this repository should be treated as clinically validated.

### Regulatory certification
The prototype is designed with accountability and interoperability concepts in mind but has not undergone regulatory certification or legal compliance assessment.

---

# 31. India Deployment Context

The intended project context is India.

The architecture is therefore designed around concepts relevant to:

- ABDM-oriented interoperability
- health-data minimization
- clinician accountability
- auditability
- role-based infrastructure access
- FHIR-based exchange

The repository should **not** be represented as legally certified ABDM/DPDP-compliant software merely because these concepts are implemented.

A real deployment would require legal review and implementation of the hospital's applicable privacy, security, consent, retention, access-control, breach-response and interoperability requirements.

---

# 32. Installation

Create a virtual environment.

## Windows

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```

## Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

# 33. Run the Automated Tests

From the project root:

```bash
python -m tests.test_harness
```

Expected output:

```text
ALL MODULAR TESTS PASSED
Dynamic arrivals processed: 10 | history: 5 | no-history: 5 | hospital daily capacity setting: 500
```

Again, this 10-patient batch is only a demonstration. The real arrival abstraction is dynamic.

---

# 34. Run the Visual Application

From the project root:

```bash
python -m doom.main
```

The Qt interface loads:

```text
doom/ui/app.ui
```

and connects it to:

```text
doom/ui/main_window.py
```

The frontend can therefore be redesigned in Qt Designer without rewriting the clinical core.

---

# 35. How to Extend the Project

## Add a real hospital data feed

Create an integration class that converts incoming EHR/HIS events into `PatientRecord` objects and feeds them into `ArrivalStream`.

```text
Hospital Registration
        â†“
FHIR/REST/HL7 Adapter
        â†“
PatientRecord
        â†“
ArrivalStream
        â†“
DoomTriageEngine
```

## Add a production ML model

A validated model should be placed behind a dedicated strategy/service interface rather than embedded directly inside the UI.

```text
TriageModel interface
      â”œâ”€â”€ PrototypeRuleModel
      â””â”€â”€ ValidatedMLModel
```

This keeps the rest of the application stable.

## Add a production audit store

Replace the in-memory audit implementation with a persistent append-only or WORM-backed service while preserving the same `AuditLog` interface.

## Add a real paging system

Connect the Layer 4 orchestration result to an authenticated hospital notification gateway.

## Add live dashboards

The current `TriageRecommendation` object can be displayed as:

- triage queue
- severity heatmap
- waiting-time monitor
- staff allocation view
- transfer queue
- uncertainty queue
- clinician override history

---

# 36. Recommended Future Frontend

The final ED dashboard should ideally show three operational areas.

## A. Live Triage Queue

```text
Patient | ESI | Confidence | Layer | Waiting | Risk Flags | Route
```

## B. Hospital Operations

```text
ED Volume
Bed Occupancy
OT Occupancy
Available Doctors
Available Specialists
Imaging Status
Network Status
Transfer Capacity
```

## C. Safety Watch

```text
Patients awaiting reassessment
Missing critical data
High uncertainty
Potential deterioration
Clinician overrides
```

The existing OOP backend is intended to provide the data required for these views.

---

# 37. Core Design Principles

Doom is built around the following principles:

### 1. Assist, don't replace

The AI provides a recommendation. The clinician remains accountable for the final clinical decision.

### 2. Missing data is normal

A first-time patient must not cause the engine to fail.

### 3. Worst-case safety

Ambiguity should increase caution rather than create false confidence.

### 4. Resource-aware AI

The same logic must adapt to different hospital capabilities.

### 5. Dynamic arrivals

The system does not assume that a fixed number of patients will arrive.

### 6. Separation of clinical logic and UI

The engine can be reused by different frontends and integration channels.

### 7. Auditable decisions

Every AI recommendation and clinician override should be traceable.

### 8. Interoperability by design

The internal model should be convertible into standardized healthcare resources.

---

# 38. One-Sentence Architecture Summary

> **DOOM AI is a modular, safety-first, resource-aware clinical decision-support engine that converts incomplete first-minute ED data into an auditable 1â€“5 triage recommendation, adapts its operating mode to hospital constraints, routes scarce resources intelligently, and keeps final clinical authority with the clinician.**

---

# 39. Final Project Status

### Implemented in this prototype

- [x] OOP modular architecture
- [x] Patient data model
- [x] Hospital asset model
- [x] Staff roster model
- [x] Four demographic cohorts
- [x] Demographic vital bands
- [x] Shock Index
- [x] SIPA-like pediatric branch
- [x] Pulse pressure feature
- [x] Missing-data detection
- [x] NLP-style syndrome tokenization
- [x] Five-level ESI-like output
- [x] Pessimistic ESI-2 floor
- [x] Confidence/uncertainty indicator
- [x] L1/L2/L3/L4 operational controller
- [x] Rural PHC L2 lock
- [x] Infrastructure permission handshake
- [x] Manual clinician data-entry router
- [x] Dynamic arrival stream abstraction
- [x] History/no-history monitoring
- [x] Transfer time comparison
- [x] Specialist routing
- [x] Staff shortage orchestration
- [x] Clinician override
- [x] Hash-chained audit log
- [x] FHIR-shaped adapter
- [x] Qt Designer UI
- [x] Automated modular test harness

### Still required before real-world clinical deployment

- [ ] Prospective clinical validation
- [ ] Multicenter validation
- [ ] Calibration and bias assessment
- [ ] Real EHR/HIS integration
- [ ] Production FHIR/HL7 gateway
- [ ] Secure identity and access control
- [ ] Encryption and key management
- [ ] Production audit/WORM storage
- [ ] Formal privacy/consent implementation
- [ ] Hospital-specific retention policy
- [ ] Clinical governance and liability review
- [ ] Regulatory assessment/certification as applicable
- [ ] Real specialist paging integration
- [ ] Validated POCUS/eFAST AI integration

---

# 40. Important Disclaimer

This repository is an engineering prototype created for an innovation-challenge context. It demonstrates architecture, workflow, interoperability boundaries and safety concepts. It must not be used to triage real patients without formal clinical validation, governance, cybersecurity review, privacy/legal review and appropriate regulatory approval.

