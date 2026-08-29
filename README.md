# DOOM AI — Emergency Department Command & Triage Decision Support
=======
﻿# DOOM AI — Emergency Department Command & Triage Decision Support

DOOM AI is an AI-assisted emergency-department triage and resource-dispatch prototype designed to help hospital staff prioritize, sequence, and route arriving patients when an emergency department is under pressure.

The system is designed as a **clinical decision-support tool, not a replacement for a clinician**. It combines structured patient information, physiological observations, prior-history availability, hospital-resource context, ambulance pre-arrival telemetry, and optional clinical image findings to produce an explainable triage recommendation and operational routing suggestion.

---

## 1. Problem We Are Solving

When an emergency department becomes busy, patient sequencing can depend heavily on rapid human judgment. The challenge is not only identifying how sick a patient appears, but also deciding:

- who needs attention first;
- how two patients with the same ESI level should be ordered;
- what resources are available right now;
- whether a patient can be retained locally;
- whether a transfer should be considered;
- how the recommendation should change when the hospital is operating with fewer resources;
- how to work when patient history is incomplete;
- how pre-arrival ambulance data can prepare the ED before arrival;
- how image-derived findings can become additional evidence without independently assigning ESI.

The project follows the challenge direction of helping staff prioritize and route patients as they arrive, reducing waiting time without replacing clinical judgment, using realistically available early-arrival data, and designing for worst-case operating conditions.

---

# 2. Core Design Philosophy

DOOM AI follows five main principles.

### 2.1 Patient severity first

The system evaluates physiological and clinical evidence before considering operational routing.

### 2.2 Explainable recommendation

The UI exposes ESI, criticality, confidence, physiological indicators, rationale, operational layer, resource dispatch and transfer recommendation.

### 2.3 Dynamic priority, not just ESI sorting

ESI is not treated as the entire queue.

If several patients receive the same ESI, available urgency and physiological evidence can be used for secondary ordering.

```text
ESI
  ↓
Secondary urgency ordering
  ↓
Resource availability
  ↓
Operational routing
```

### 2.4 Resource-aware operation

The system considers the current ER/OT capacity, operational layer, staff/resource state and transfer options rather than assuming unlimited capacity.

### 2.5 Clinician remains in control

The system recommends. A clinician can review and override the recommendation. The audit workflow records the recommendation/review path.

---

# 3. High-Level Solution Architecture

```text
                         ┌─────────────────────────┐
                         │       DOOM AI UI        │
                         │     PySide6 / Qt UI     │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
              ▼                       ▼                        ▼
       Manual patient          Ambulance Gateway        Test Case Lab
       entry / batch            pre-arrival feed         isolated UI
              │                       │                        │
              └───────────────┬───────┴───────────────┬────────┘
                              ▼                       │
                       Patient / evidence             │
                              │                       │
                    ┌─────────▼─────────┐             │
                    │  Triage pipeline  │◄────────────┘
                    │  & AI engine      │
                    └─────────┬─────────┘
                              │
             ┌────────────────┼─────────────────┐
             ▼                ▼                 ▼
         ESI / severity   Priority queue   Resource routing
             │                │                 │
             └────────────────┼─────────────────┘
                              ▼
                    Explainable UI result
                              │
                              ▼
                    Result / audit reporting
```

---

# 4. Project Structure

```text
Doom_AI_ChatGPT Backup/
│
├── doom/
│   ├── api/
│   ├── config/
│   ├── core/
│   ├── models/
│   ├── services/
│   │   ├── ambulance_feed.py
│   │   ├── ambulance_gateway_client.py
│   │   ├── arrival_stream.py
│   │   ├── audit.py
│   │   ├── batch_triage.py
│   │   ├── engine.py
│   │   ├── hospital_resources.py
│   │   ├── image_parser.py
│   │   ├── priority_queue.py
│   │   ├── presentation_result.py
│   │   ├── result_reporter.py
│   │   ├── test_case_ui_service.py
│   │   └── vision_analysis.py
│   ├── ui/
│   │   ├── app.ui
│   │   ├── main_window.py
│   │   ├── test_case_window.py
│   │   └── test_case_window.ui
│   └── main.py
│
├── ambulance_gateway/
│   ├── __init__.py
│   ├── server.py
│   ├── database.py
│   └── schemas.py
│
├── tools/
│   └── simulate_ambulance.py
│
├── test_cases/
│   ├── test_case_runner.py
│   ├── test_01_profiles.py
│   ├── test_02_history_mix.py
│   ├── test_03_dynamic_arrivals_scale.py
│   ├── test_04_priority_reshuffle.py
│   ├── test_05_capacity_transfer.py
│   ├── test_06_layers.py
│   ├── test_07_demographic.py
│   ├── test_08_safety_floor.py
│   ├── test_09_ambulance.py
│   ├── test_10_image_pipeline.py
│   ├── test_11_override_audit.py
│   ├── test_12_permissions.py
│   ├── test_13_fhir.py
│   ├── test_14_unseen_stress.py
│   ├── test_15_mass_casualty.py
│   └── test_16_ui_contract.py
│
├── tests/
├── reports/
├── requirements.txt
└── README.md
```

---

# 5. Main Functional Modules

## 5.1 Hospital profiles

The current design supports:

```text
Multispecialty Tertiary Center
Rural Primary Health Centre
```

### Multispecialty Tertiary Center

Provides the richer operational workflow, including ambulance pre-arrival telemetry and higher-resource capabilities.

### Rural Primary Health Centre

Represents a constrained deployment. Ambulance integration is intentionally disabled in this profile in the current prototype, so the rural workflow uses local/manual information and the selected low-resource operational behavior.

---

# 6. Hospital Capacity

The UI exposes:

- ER total;
- ER available;
- OT total;
- OT available;
- ED visits/day;
- ED wait time.

This allows the operational response to change when resources are constrained.

Example:

```text
High-acuity patient
+
local capacity available
        ↓
retain / route locally

High-acuity patient
+
local capacity unavailable
        ↓
consider transfer / alternate routing
```

---

# 7. Triage and Priority Behavior

The output uses a five-level ESI scale:

```text
ESI 1 — Immediate Resuscitation
ESI 2 — Emergency / High Risk
ESI 3 — Urgent
ESI 4 — Less Urgent
ESI 5 — Non-Urgent
```

The UI also exposes:

```text
Criticality
System confidence
Uncertainty
Shock index / physiological indicators
Data completeness
Rationale
Operational layer
Resource dispatch / routing
Transfer consideration
```

## Secondary priority

Two patients can have the same ESI but different immediate urgency.

Therefore the queue can perform secondary ordering using the available evidence instead of treating every same-ESI patient as identical.

---

# 8. History Availability

The project explicitly tests mixed availability of patient history.

The intended scenario mix is approximately:

```text
50% prior history available
50% no prior history
```

The system should not invent missing history. It should continue using the evidence that is actually available.

---

# 9. Ambulance Pre-Arrival Telemetry

The ambulance workflow is implemented as a separate gateway:

```text
Ambulance / simulator
        ↓
FastAPI gateway
        ↓
Telemetry storage
        ↓
DOOM AI gateway client
        ↓
Existing UI
```

The gateway can receive:

```text
Patient ID
Patient name
HR
RR
SBP
DBP
SpO₂
ETA
Ambulance source
Notes
Timestamp
```

The clinician enters a patient identifier and selects:

```text
Load Ambulance Data
```

The retrieved telemetry appears in the existing ambulance section.

## Ambulance triage modes

The UI supports:

```text
Ignore ambulance data
Ambulance-only provisional triage
Combine ambulance + hospital data
```

### Ignore ambulance data

Telemetry may be displayed but is not used in the triage decision.

### Ambulance-only provisional triage

The pre-arrival measurements can be used to form a provisional assessment before hospital observations are entered.

### Combined mode

Ambulance telemetry can be combined with current hospital observations. Current in-hospital measurements take precedence where they exist; ambulance measurements remain useful as pre-arrival context.

## Deployment restriction

The ambulance feature is exposed only for:

```text
Multispecialty Tertiary Center
```

and disabled for:

```text
Rural Primary Health Centre
```

---

# 10. Clinical Image Workflow

Image analysis is an **evidence-generation layer**, not an independent ESI classifier.

```text
Image uploaded
      ↓
Local image parsing / multimodal analysis
      ↓
Image findings
      ↓
Other patient information
      ↓
Final triage evaluation
```

Possible findings represented by the prototype include observable trauma and injury-related signs such as:

```text
visible trauma
superficial bleeding
chest asymmetry
possible structural abnormality
other observable injury findings
```

The live Gemini multimodal path is optional and only active when the Gemini API key is configured.

---

# 11. Clinician Override and Audit

DOOM AI follows a human-in-the-loop design.

```text
AI recommendation
        ↓
Clinician review
        ↓
Accept or override
```

The UI includes:

```text
Manual Clinician Override
Audit status
```

The clinician remains responsible for the final clinical decision.

---

# 12. Operational Layers

The architecture supports operational layers representing different levels of resource and deployment constraints.

The layer can influence routing, resource dispatch and safety-oriented behavior.

This allows the same overall architecture to operate under different conditions instead of assuming a single fully resourced environment.

---

# 13. Live ED Arrival Stream

The main UI supports multi-patient arrival handling through:

```text
+ Add Patient
Remove Selected
Import CSV
Upload Image for Selected
EVALUATE ALL ARRIVALS
```

The intended flow is:

```text
multiple arrivals
      ↓
patient evaluation
      ↓
ESI / severity
      ↓
secondary priority ordering
      ↓
resource-aware routing
      ↓
priority queue
```

This is the basis for surge and mass-casualty scenarios.

---

# 14. Isolated Test Case Lab

Test cases are intentionally separated from the live patient workflow.

The main UI exposes:

```text
Open Test Case Lab — Simulation
```

The separate window is labeled:

```text
DOOM AI — TEST CASE LAB
SIMULATION MODE — NO LIVE PATIENT DATA
```

The Test Case Lab contains:

- H01–H16 selector;
- scenario description;
- simulated patient arrivals;
- isolated results;
- run/clear controls.

The automated test runner remains independent.

Thus:

```text
LIVE UI
    ↓
real/manual patient workflow

TEST CASE LAB
    ↓
isolated simulation workflow

AUTOMATED TEST RUNNER
    ↓
repeatable validation + reports
```

This prevents test patients from being mixed into the live workflow.

---

# 15. Complete Test-Case Catalogue

The current validation suite defines 16 core scenarios.

## H01 — Tertiary → Rural → Tertiary Profile Switching

Tests switching between hospital deployment profiles and restoring the appropriate operational capabilities when switching back.

## H02 — Dynamic 50/50 History Availability

Tests a mixed stream with and without prior history.

Expected behavior: evaluate using available evidence without assuming missing historical data.

## H03 — 100–500+ ED/Day Scalability and Surge

Tests increasing emergency-department load and larger simultaneous arrival batches.

Expected behavior: retain functional triage, priority and resource-aware behavior under surge conditions.

## H04 — Same-ESI Secondary Priority Reshuffling

Tests cases where patients have the same ESI but different urgency signals.

Expected behavior: secondary ordering determines who should be handled first.

## H05 — Full ER/OT Capacity + Nearby Transfer

Tests high-acuity demand when local capacity is constrained.

Expected behavior: consider current resource availability and transfer/routing options.

## H06 — Polymorphic L1/L2/L3/L4 Controller

Tests adaptation to different operational layers.

Expected behavior: operational decisions change with resource/deployment conditions.

## H07 — Demographic-Calibrated Cohorts

Tests infant, pediatric, adult and geriatric cohorts.

Expected behavior: preserve clinically meaningful differences without breaking the common decision framework.

## H08 — Pessimistic Safety Floor

Tests missing, sparse, uncertain or degraded inputs.

Expected behavior: avoid optimistic assumptions and preserve conservative safety behavior.

## H09 — Ambulance Pre-Arrival Data Lookup and Preload

Tests:

```text
patient ID
   ↓
gateway lookup
   ↓
ambulance telemetry
   ↓
UI preload
```

## H10 — Clinical Image Ingestion / Metadata

Tests the image-ingestion and image-analysis path.

Expected behavior: supported images are accepted; live multimodal findings are produced when the Gemini service is configured.

## H11 — Clinician Override + Immutable Audit Event

Tests review/override and audit recording.

## H12 — Runtime System Permissions

Tests permission-aware access to operational data/resources.

## H13 — FHIR-Shaped Middleware Contract

Tests the structured integration boundary used for middleware-style patient data exchange.

## H14 — Unseen / Randomized Scenario Robustness

Tests newly constructed patient conditions rather than relying on known/hardcoded identifiers.

## H15 — 10-Patient Mass-Casualty Surge

Tests simultaneous evaluation and priority ordering of a ten-patient surge.

Expected behavior:

```text
10 patients
    ↓
batch evaluation
    ↓
ESI
    ↓
priority ordering
    ↓
resource-aware dispatch
```

## H16 — Frontend Object-Name Contract

Tests the presence of UI object names required by the controller/application.

---

# 16. Test and Validation Strategy

## 16.1 Python compilation checks

```powershell
python -m py_compile doom/ui/main_window.py
python -m py_compile doom/ui/test_case_window.py
python -m py_compile doom/services/test_case_ui_service.py
```

## 16.2 Automated test suite

```powershell
python -m test_cases.test_case_runner
```

The runner reports:

```text
PASS
FAIL
SKIP
TOTAL
```

and writes validation reports.

## 16.3 Interactive Test Case Lab

```powershell
python -m doom.main
```

Then:

```text
Open Test Case Lab — Simulation
        ↓
Select H01–H16
        ↓
Load Test Case
        ↓
RUN TEST CASE
```

---

# 17. Reports

Reports are written to:

```text
reports/
```

Common outputs include:

```text
hackathon_latest.json
hackathon_latest.csv
hackathon_latest.html
```

Open the report directory:

```powershell
explorer .
eports
```

Open the HTML report:

```powershell
start .
eports\hackathon_latest.html
```

---

# 18. Dependencies

The project uses:

```text
Python
PySide6
google-genai
Pydantic
requests
FastAPI
Uvicorn
```

Install the exact committed dependency set with:

```powershell
python -m pip install -r requirements.txt
```

The authoritative versions are those recorded in `requirements.txt`.

---

# 19. Fresh Installation

Clone the repository:

```powershell
git clone https://github.com/SubhEE27/Doom_AI_NIT_Rourkela.git
cd Doom_AI_NIT_Rourkela
```

Create the virtual environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

# 20. Gemini API Configuration

Do not commit the Gemini API key to GitHub.

Set it as a Windows User environment variable:

```powershell
[Environment]::SetEnvironmentVariable(
    "GEMINI_API_KEY",
    "YOUR_REAL_GEMINI_KEY",
    "User"
)
```

Restart VS Code after setting it so the new terminal inherits the variable.

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Verify:

```powershell
if ($env:GEMINI_API_KEY) {
    "Gemini API key is loaded"
} else {
    "Gemini API key is missing"
}
```

Python check:

```powershell
python -c "import os; print('Gemini key detected:', bool(os.getenv('GEMINI_API_KEY')))"
```

SDK check:

```powershell
python -c "from google import genai; print('Gemini SDK OK')"
```

Each machine should provide its own Gemini API key.

---

# 21. Launching the Main DOOM AI UI

```powershell
.\.venv\Scripts\Activate.ps1
python -m doom.main
```

The live application provides:

```text
Hospital Environment
Hospital Capacity
Ambulance / Pre-Arrival
Single-Patient Detailed Triage
Live ED Arrival Stream
AI Priority Queue / Resource Dispatch
```

---

# 22. Running the Ambulance Gateway

Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
python -m uvicorn ambulance_gateway.server:app --host 127.0.0.1 --port 8000
```

Health endpoint:

```text
http://127.0.0.1:8000
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

---

# 23. Simulating an Ambulance

Terminal 2:

```powershell
.\.venv\Scripts\Activate.ps1
python tools/simulate_ambulance.py --patient-id AMB-1001 --patient-name "Demo Patient"
```

Verify the gateway data:

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/ambulance/patient/AMB-1001"
```

Launch DOOM AI and enter:

```text
AMB-1001
```

in the ambulance Patient Name / ID field, then click:

```text
Load Ambulance Data
```

---

# 24. Recommended Judge Demonstration

A strong demo sequence is:

### 24.1 Normal patient

Enter patient information manually and show:

```text
ESI
Criticality
Confidence
Rationale
Resource dispatch
```

### 24.2 Ambulance arrival

```text
Ambulance simulator
    ↓
telemetry upload
    ↓
Load Ambulance Data
    ↓
preloaded vitals
    ↓
provisional / combined assessment
```

### 24.3 Same-ESI priority

Run:

```text
H04 — Same-ESI Secondary Priority Reshuffle
```

and show that equal ESI does not imply equal priority.

### 24.4 Resource-constrained patient

Run:

```text
H05 — Full ER/OT Capacity + Nearby Transfer
```

and show how capacity affects operational routing.

### 24.5 Mass casualty

Open:

```text
Test Case Lab
```

Select:

```text
H15 — Mass Casualty Surge
```

Load and execute the scenario.

Show the simulated patient queue and resulting priority order.

---

# 25. Why the Solution Is Useful

## Faster prioritization

Several arriving patients can be processed within one common workflow.

## Better queue quality

Same-ESI patients can still be differentiated by urgency signals.

## Resource-aware decisions

The AI considers the relationship between clinical demand and actual hospital capacity.

## Pre-arrival readiness

Ambulance information can be visible before the patient reaches the ED.

## Multimodal evidence

Image findings can contribute additional evidence to the final assessment.

## Adaptable deployment

The same application can represent richer tertiary resources and more constrained rural operation.

## Human oversight

The clinician retains final authority and can override the recommendation.

## Explainability

The UI exposes not only a number but the supporting indicators, rationale, confidence and operational context.

## Reproducible testing

The automated suite and isolated Test Case Lab allow repeatable scenarios without mixing simulated and live workflows.

---

# 26. Safety, Scope and Limitations

DOOM AI is a hackathon prototype.

It is **not a medical device** and should not be used as a substitute for professional medical judgment.

Real deployment would require, among other things:

- clinical validation;
- prospective evaluation;
- formal governance and approval;
- secure authentication/authorization;
- encrypted communication;
- privacy-preserving data handling;
- model monitoring;
- demographic and clinical validation;
- hospital-system integration;
- incident response;
- formal audit and retention policies.

The prototype therefore uses an explicit human-in-the-loop design.

---

# 27. Security Guidelines

Never commit:

```text
.venv/
.env
API keys
private patient data
production credentials
database secrets
```

Before committing:

```powershell
git status --short
```

The Gemini secret should remain in:

```text
GEMINI_API_KEY
```

and never be hardcoded into Python source.

---

# 28. Current Implementation Status

Implemented:

```text
✓ Hospital profile switching
✓ Multispecialty / rural behavior
✓ Five-level ESI workflow
✓ Criticality and confidence presentation
✓ Secondary priority reshuffling
✓ Multi-patient arrival handling
✓ Hospital capacity awareness
✓ Resource dispatch
✓ Transfer consideration
✓ Operational layers
✓ History / no-history scenarios
✓ Demographic cohorts
✓ Safety-floor behavior
✓ Ambulance gateway
✓ Ambulance telemetry preload
✓ Ambulance-only provisional triage
✓ Combined ambulance + hospital mode
✓ Clinical image ingestion path
✓ Gemini multimodal vision path
✓ Clinician override
✓ Audit workflow
✓ Permission checks
✓ FHIR-shaped middleware contract
✓ Unseen-scenario testing
✓ Mass-casualty simulation
✓ UI object-contract testing
✓ Automated reports
✓ Isolated Test Case Lab
✓ GitHub dependency setup
```

---

# 29. Future Extension

A natural next validation scenario is:

```text
H17 — Ambulance Telemetry → ED Handoff
```

Potential flow:

```text
ambulance upload
    ↓
gateway
    ↓
lookup
    ↓
DOOM AI preload
    ↓
hospital arrival observations
    ↓
combined assessment
    ↓
final triage
    ↓
audit/report
```

Future production-oriented enhancements could include authenticated ambulance devices, stronger hospital-network security, formal FHIR/ABDM integration, richer uncertainty analysis, persistent secure telemetry storage, deeper image validation, role-based access and operational monitoring.

---

# 30. Final Summary

DOOM AI is designed as an **emergency-department command and decision-support system**, not merely as an ESI classifier.

Its central concept is:

```text
Patient severity
      +
Clinical evidence
      +
History availability
      +
Image findings, when available
      +
Ambulance pre-arrival data, when available
      +
Hospital profile
      +
Resource capacity
      +
Operational layer
      ↓
Triage recommendation
      ↓
Secondary priority ordering
      ↓
Resource dispatch
      ↓
Transfer consideration
      ↓
Explainable result + clinician oversight
```

When a patient arrives, DOOM AI evaluates what is known, estimates the severity, considers the hospital context, and presents a recommendation that can be reviewed by the clinician.

When many patients arrive together, the system can classify them, order them dynamically, and account for resource availability.

When the hospital operates under different resource conditions, the operational behavior adapts to the selected deployment profile.

When a judge wants to challenge the system, the automated 16-case validation suite and isolated Test Case Lab provide reproducible scenarios without contaminating the live workflow.

The overall objective is to help an emergency department move from **patient-by-patient reaction** toward a more structured, explainable and resource-aware command workflow while keeping clinical authority with the human team.
