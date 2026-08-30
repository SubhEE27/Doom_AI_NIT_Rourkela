<div align="center">

# 🚨 DOOM AI
### Emergency Department Command & Triage Decision-Support System

*Because in an emergency, seconds decide priorities — and priorities decide outcomes.*

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt%20UI-41CD52?logo=qt&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Ambulance%20Gateway-009688?logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-Multimodal%20Vision-8E75B2?logo=googlegemini&logoColor=white)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)
![Status](https://img.shields.io/badge/Status-Hackathon%20Prototype-orange)

**Built at NIT Rourkela** · [Repository](https://github.com/SubhEE27/Doom_AI_NIT_Rourkela)

</div>

---

## 🩺 What is DOOM AI?

Picture an emergency department at 2 a.m. Five patients walk in within ten minutes. Two ambulances are inbound. The OT is nearly full. Someone has to decide — *right now* — who gets seen first, who can wait, and who needs to be sent elsewhere.

**DOOM AI** is an AI-assisted command layer for exactly that moment. It's not a diagnosis engine and it's not trying to replace the clinician standing at the desk — it's the system quietly doing the math in the background: reading vitals, prior history, ambulance telemetry, and even image-based findings, then handing the care team a ranked, explainable, resource-aware recommendation they can accept or override in one click.

> ⚠️ **DOOM AI is a hackathon prototype, not a certified medical device.** The clinician always has the final word — see [Safety, Scope & Limitations](#-safety-scope--limitations).

---

## 🎯 The Problem

When an ED gets busy, sequencing patients isn't just "who looks sickest." Real triage has to answer, simultaneously:

- Who needs attention **first**, right now?
- Two patients share the same ESI level — who actually goes first?
- What resources (beds, OT, staff) are free *at this exact moment*?
- Can this patient be treated locally, or does it need a transfer?
- What changes if the hospital is running on reduced resources?
- What do you do when half your patients arrive with **no prior history**?
- Can pre-arrival ambulance data get the ED ready *before the patient walks in*?
- Can an uploaded image add evidence — without hijacking the whole decision?

DOOM AI is built to answer all of these together, using only the data that's realistically available in the first minutes of an arrival — and to keep working sensibly even in worst-case, resource-starved conditions.

---

## 🧭 Design Philosophy

| Principle | What it means |
|---|---|
| **1. Severity first** | Physiological and clinical evidence is weighed *before* any operational routing decision. |
| **2. Explainable, always** | Every recommendation ships with ESI, criticality, confidence, rationale, and the operational context behind it — never a black-box number. |
| **3. Dynamic priority, not just ESI sorting** | Same ESI ≠ same urgency. Secondary evidence reorders the queue when it matters. |
| **4. Resource-aware** | Recommendations factor in live ER/OT capacity and staffing — never assume infinite resources. |
| **5. Clinician stays in control** | The system *recommends*. A human reviews, accepts, or overrides — and that decision is audited. |

```text
ESI
 ↓
Secondary urgency ordering
 ↓
Resource availability
 ↓
Operational routing
```

---

## 🏗️ System Architecture

```text
                         ┌─────────────────────────┐
                         │        DOOM AI UI        │
                         │      PySide6 / Qt UI     │
                         └────────────┬────────────┘
                                      │
              ┌───────────────────────┼────────────────────────┐
              │                       │                        │
              ▼                       ▼                        ▼
       Manual patient          Ambulance Gateway         Test Case Lab
       entry / batch            pre-arrival feed          isolated UI
              │                       │                        │
              └───────────────┬───────┴───────────────┬────────┘
                               ▼                        │
                       Patient / evidence               │
                               │                        │
                     ┌─────────▼─────────┐              │
                     │  Triage pipeline  │◄─────────────┘
                     │   & AI engine     │
                     └─────────┬─────────┘
                               │
              ┌────────────────┼─────────────────┐
              ▼                ▼                  ▼
        ESI / severity   Priority queue    Resource routing
              │                │                  │
              └────────────────┼──────────────────┘
                               ▼
                     Explainable UI result
                               │
                               ▼
                     Result / audit reporting
```

---

## 🧰 Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **Desktop UI** | [PySide6](https://doc.qt.io/qtforpython/) (Qt for Python) | Native, responsive desktop app for the live triage console and the isolated Test Case Lab |
| **AI Engine** | Python core services (`doom/services/engine.py`) | Rule + evidence-driven triage, priority queueing, and resource routing logic |
| **Multimodal Vision** | [Google Gemini](https://ai.google.dev/) (`google-genai`) | Optional live image-evidence analysis (trauma, bleeding, structural findings) |
| **Ambulance Gateway** | [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/) | Standalone microservice that ingests pre-arrival ambulance telemetry |
| **Data Contracts** | [Pydantic](https://docs.pydantic.dev/) | Structured, validated patient/telemetry/FHIR-shaped data models |
| **Networking** | `requests` | Client-side calls from the DOOM AI app to the ambulance gateway |
| **Testing** | Custom test runner (`test_cases/`) + `tests/` | 16-scenario hackathon validation suite + unit tests, with JSON/CSV/HTML reports |
| **Language** | Python 3.10+ | Everything, end to end |
| **License** | GPL-3.0 | Open source |

---

## 📁 Project Structure

```text
Doom_AI_NIT_Rourkela/
│
├── doom/                          # Core application
│   ├── api/                       # API-facing contracts
│   ├── config/                    # App configuration
│   ├── core/                      # Core domain logic
│   ├── models/                    # Data models
│   ├── services/
│   │   ├── ambulance_feed.py
│   │   ├── ambulance_gateway_client.py
│   │   ├── arrival_stream.py
│   │   ├── audit.py
│   │   ├── batch_triage.py
│   │   ├── engine.py               # 🧠 The triage/AI engine
│   │   ├── hospital_resources.py
│   │   ├── image_parser.py
│   │   ├── priority_queue.py
│   │   ├── presentation_result.py
│   │   ├── result_reporter.py
│   │   ├── test_case_ui_service.py
│   │   └── vision_analysis.py      # Gemini multimodal path
│   ├── ui/
│   │   ├── app.ui
│   │   ├── main_window.py
│   │   ├── test_case_window.py
│   │   └── test_case_window.ui
│   └── main.py                     # Entry point: `python -m doom.main`
│
├── ambulance_gateway/               # Standalone FastAPI microservice
│   ├── __init__.py
│   ├── server.py
│   ├── database.py
│   └── schemas.py
│
├── tools/
│   └── simulate_ambulance.py        # CLI ambulance simulator for demos
│
├── test_cases/                      # 🧪 The 16-scenario (H01–H16) validation suite
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
├── hackathon_tests/
│   └── fixtures/                    # Sample fixtures used by the validation suite
│
├── sample_images/                   # Sample clinical images for the vision pipeline demo
│
├── tests/                           # Additional unit tests
├── reports/                         # Auto-generated hackathon_latest.{json,csv,html}
├── requirements.txt
├── LICENSE                          # GPL-3.0
└── README.md
```

---

## ✨ Core Features

### 🏥 Two Deployment Profiles
| Profile | Behavior |
|---|---|
| **Multispecialty Tertiary Center** | Full workflow — ambulance pre-arrival telemetry, richer resource capabilities |
| **Rural Primary Health Centre** | Constrained deployment — ambulance integration intentionally disabled, low-resource operational behavior |

### 📊 Explainable Five-Level ESI Triage
```text
ESI 1 — Immediate Resuscitation
ESI 2 — Emergency / High Risk
ESI 3 — Urgent
ESI 4 — Less Urgent
ESI 5 — Non-Urgent
```
...plus criticality, system confidence, uncertainty, shock index, data completeness, rationale, and operational layer — all surfaced in the UI, not buried in a log file.

### 🚑 Ambulance Pre-Arrival Telemetry
```text
Ambulance / simulator → FastAPI gateway → Telemetry storage → DOOM AI gateway client → Existing UI
```
Three triage modes: **ignore** telemetry, **ambulance-only provisional** triage, or **combine** ambulance + hospital data (with in-hospital measurements always taking precedence once available).

### 🖼️ Clinical Image Evidence Layer
Images are treated as **additional evidence**, not an independent verdict — findings like visible trauma, superficial bleeding, chest asymmetry, or possible structural abnormality feed into the final assessment. The live Gemini multimodal path activates only when an API key is configured.

### 👨‍⚕️ Human-in-the-Loop Override & Audit
```text
AI recommendation → Clinician review → Accept or override
```
Every override is recorded in an audit trail. The AI never has the last word.

### 🧪 Isolated Test Case Lab
A dedicated **"SIMULATION MODE — NO LIVE PATIENT DATA"** window lets you run any of the 16 validation scenarios without ever touching the live patient workflow.

---

## 🧪 The 16-Scenario Validation Suite

| ID | Scenario | Tests |
|---|---|---|
| **H01** | Tertiary ↔ Rural Profile Switching | Switching deployment profiles and restoring capabilities |
| **H02** | Dynamic 50/50 History Availability | Mixed history / no-history stream |
| **H03** | 100–500+ ED/Day Scalability & Surge | Behavior under heavy load |
| **H04** | Same-ESI Secondary Priority Reshuffle | Reordering equal-ESI patients by urgency |
| **H05** | Full ER/OT Capacity + Nearby Transfer | Routing under constrained capacity |
| **H06** | Polymorphic L1–L4 Controller | Adapting to operational layers |
| **H07** | Demographic-Calibrated Cohorts | Infant, pediatric, adult, geriatric handling |
| **H08** | Pessimistic Safety Floor | Behavior on missing/sparse/degraded input |
| **H09** | Ambulance Pre-Arrival Lookup & Preload | Gateway lookup → UI preload |
| **H10** | Clinical Image Ingestion | Image pipeline + Gemini findings |
| **H11** | Clinician Override + Audit | Review/override recording |
| **H12** | Runtime System Permissions | Permission-aware access |
| **H13** | FHIR-Shaped Middleware Contract | Structured data exchange boundary |
| **H14** | Unseen / Randomized Scenario Robustness | Novel, non-hardcoded cases |
| **H15** | 10-Patient Mass-Casualty Surge | Batch evaluation + priority ordering at scale |
| **H16** | Frontend Object-Name Contract | Required UI object names present |

Run the whole suite:
```powershell
python -m test_cases.test_case_runner
```
The runner reports `PASS` / `FAIL` / `SKIP` / `TOTAL` and writes results to `reports/hackathon_latest.{json,csv,html}`.

---

## 📸 Screenshots & Test Results

> Drop your screenshots and test-run captures into a `docs/screenshots/` folder in the repo and reference them below — this section is the visual proof of DOOM AI in action.

<div align="center">

| Live Triage Console | Test Case Lab |
|---|---|
| ![Live Triage Console](docs/screenshots/live_triage_console.png) | ![Test Case Lab](https://dash.cloudflare.com/f62295aa5ed7e36cd3ac635d38135e84/r2/default/buckets/doomai/objects/Live.png) |

| H04 — Same-ESI Reshuffle | H15 — Mass Casualty Surge |
|---|---|
| ![H04 result](docs/screenshots/h04_same_esi_reshuffle.png) | ![H15 result](docs/screenshots/h15_mass_casualty.png) |

| Ambulance Telemetry Preload | HTML Test Report |
|---|---|
| ![Ambulance preload](docs/screenshots/ambulance_preload.png) | ![HTML report](docs/screenshots/hackathon_report.png) |

</div>

**Suggested captures to add:**
- ✅ A normal single-patient walkthrough (ESI → criticality → rationale → dispatch)
- ✅ An ambulance simulator run feeding live telemetry into the UI
- ✅ A same-ESI reshuffle (H04) before/after comparison
- ✅ A full-capacity transfer decision (H05)
- ✅ The 10-patient mass-casualty queue (H15) fully populated
- ✅ The generated `hackathon_latest.html` report with PASS/FAIL counts

---

## ⚙️ Getting Started

### 1. Clone & set up
```powershell
git clone https://github.com/SubhEE27/Doom_AI_NIT_Rourkela.git
cd Doom_AI_NIT_Rourkela
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2. Configure Gemini (optional, enables live image analysis)
```powershell
[Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "YOUR_REAL_GEMINI_KEY", "User")
```
Restart your terminal/IDE afterward so the variable is picked up, then verify:
```powershell
python -c "import os; print('Gemini key detected:', bool(os.getenv('GEMINI_API_KEY')))"
```

### 3. Launch the main UI
```powershell
python -m doom.main
```

### 4. Run the Ambulance Gateway (in a second terminal)
```powershell
python -m uvicorn ambulance_gateway.server:app --host 127.0.0.1 --port 8000
```
Interactive docs at `http://127.0.0.1:8000/docs`.

### 5. Simulate an ambulance (in a third terminal)
```powershell
python tools/simulate_ambulance.py --patient-id AMB-1001 --patient-name "Demo Patient"
```
Then in the app, enter `AMB-1001` in the ambulance field and click **Load Ambulance Data**.

---

## 🎬 Suggested Demo Flow

1. **Normal patient** — manual entry → ESI, criticality, confidence, rationale, dispatch.
2. **Ambulance arrival** — simulator → gateway → `Load Ambulance Data` → provisional/combined assessment.
3. **Same-ESI priority** — run **H04** and show equal ESI ≠ equal priority.
4. **Resource-constrained patient** — run **H05** and show capacity-driven routing.
5. **Mass casualty** — open the Test Case Lab, load **H15**, and watch the ten-patient queue resolve.

---

## 🛡️ Safety, Scope & Limitations

DOOM AI is a **hackathon prototype** — it is **not a medical device** and must never substitute for professional clinical judgment. A real-world deployment would additionally need: clinical validation, prospective evaluation, formal governance/approval, secure auth, encrypted transport, privacy-preserving data handling, model monitoring, demographic/clinical validation, hospital-system integration, incident response, and formal audit/retention policies. That's precisely why the human-in-the-loop override sits at the center of the design.

**Never commit:** `.venv/`, `.env`, API keys, private patient data, production credentials, or database secrets. Run `git status --short` before every commit, and keep `GEMINI_API_KEY` out of source code — always.

---

## 🚀 Why This Matters

| Benefit | Impact |
|---|---|
| **Faster prioritization** | Multiple arriving patients processed in one unified workflow |
| **Better queue quality** | Same-ESI patients still differentiated by real urgency signals |
| **Resource-aware decisions** | Clinical demand weighed against actual, live hospital capacity |
| **Pre-arrival readiness** | Ambulance data visible *before* the patient reaches the door |
| **Multimodal evidence** | Image findings strengthen — never override — the final call |
| **Adaptable deployment** | One codebase covers both a tertiary center and a rural PHC |
| **Human oversight** | Clinicians keep final authority, always |
| **Reproducible testing** | 16-case automated suite + isolated Test Case Lab, zero contamination of live data |

---

## 🗺️ Roadmap

- **H17 — Ambulance Telemetry → ED Handoff**: a full closed-loop scenario from ambulance upload through combined assessment to final audit/report.
- Authenticated ambulance devices & stronger hospital-network security
- Formal FHIR/ABDM integration
- Richer uncertainty analysis and persistent, secure telemetry storage
- Deeper image validation, role-based access, and operational monitoring

---

## 📜 License

Released under the **GPL-3.0 License**. See [`LICENSE`](LICENSE) for details.

---

## 👤 Author

**Subhajit** ([@SubhEE27](https://github.com/SubhEE27))
Department of Electrical Engineering, National Institute of Technology Rourkela

- GitHub: [github.com/SubhEE27](https://github.com/SubhEE27)
- Project: [Doom_AI_NIT_Rourkela](https://github.com/SubhEE27/Doom_AI_NIT_Rourkela)

*Feel free to open an issue or a pull request — feedback, bug reports, and contributions are welcome.*

---

<div align="center">

### Built with 🩺 + 🤖 at NIT Rourkela

*Patient severity + clinical evidence + history + images + ambulance data + hospital profile + resource capacity + operational layer → an explainable triage recommendation, always reviewed by a human.*

</div>
