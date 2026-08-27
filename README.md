# DOOM AI Prototype

This version separates the current triage prototype into modules so the same clinical engine can be called from a Qt UI, tests, a FHIR/REST adapter, or future mobile/web clients.

## Structure

```text
Doom-Ready/
â”œâ”€â”€ doom/
â”‚   â”œâ”€â”€ config/settings.py
â”‚   â”œâ”€â”€ models/domain.py
â”‚   â”œâ”€â”€ core/
â”‚   â”‚   â”œâ”€â”€ ingestion.py
â”‚   â”‚   â”œâ”€â”€ stratification.py
â”‚   â”‚   â”œâ”€â”€ scoring.py
â”‚   â”‚   â”œâ”€â”€ uncertainty.py
â”‚   â”‚   â”œâ”€â”€ layers.py
â”‚   â”‚   â””â”€â”€ routing.py
â”‚   â”œâ”€â”€ services/
â”‚   â”‚   â”œâ”€â”€ engine.py
â”‚   â”‚   â”œâ”€â”€ audit.py
â”‚   â”‚   â”œâ”€â”€ arrival_stream.py
â”‚   â”‚   â””â”€â”€ demo.py
â”‚   â”œâ”€â”€ api/fhir.py
â”‚   â”œâ”€â”€ ui/app.ui
â”‚   â”œâ”€â”€ ui/main_window.py
â”‚   â””â”€â”€ main.py
â”œâ”€â”€ tests/test_harness.py
â””â”€â”€ requirements.txt
```

## Dynamic patient arrivals

The production-facing abstraction is `ArrivalStream`. It accepts any iterable of patient arrivals and never assumes that 10, 50, 100, or 500 patients will arrive. The 50:50 history/no-history split is treated as a monitoring assumption, not as a hard gate.

## Hospital scale

`HospitalAssets.daily_ed_visits` can represent hospitals from roughly 100 to 500+ ED visits/day. `current_ed_volume` and `normal_ed_volume` drive surge calculations.

## UI

`app.ui` is a Qt Designer file. The UI controller in `main_window.py` calls `DoomTriageEngine`; the engine does not depend on the UI.

## Run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m tests.test_harness
python -m doom.main
```

Clinical thresholds in this prototype are demonstration configurations and must be replaced with institution-approved validated rules before clinical deployment.

