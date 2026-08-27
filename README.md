# DOOM AI Prototype

This version separates the current triage prototype into modules so the same clinical engine can be called from a Qt UI, tests, a FHIR/REST adapter, or future mobile/web clients.

## Structure

```text
doom/
config/settings.py
models/domain.py
core/
ingestion.py
stratification.py
scoring.py
uncertainty.py
layers.py
routing.py
services/
engine.py
audit.py
arrival_stream.py
demo.py
api/fhir.py
ui/app.ui
ui/main_window.py
main.py
tests/test_harness.py
requirements.txt
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

