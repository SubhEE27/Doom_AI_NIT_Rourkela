# DOOM AI — Hackathon Validation Suite

This folder is intentionally kept **outside the production `doom_ai/` package**. It does not replace or modify the triage engine. It feeds scenarios into the same engine used by the UI and records the observed behavior.

## Coverage

- Tertiary ↔ Rural profile switching and rural L2 lock
- 50:50 history/no-history assumption without fixed patient count
- 100–500+ ED/day scaling and surge load
- Dynamic multi-patient arrival evaluation
- Same-ESI secondary priority reshuffling
- Full ER/OT capacity and nearby transfer logic
- L1/L2/L3/L4 operational layers
- Infant/pediatric/adult/geriatric stratification
- Missing-data pessimistic safety floor
- Ambulance pre-arrival telemetry lookup/preload
- Image metadata ingestion and optional live Gemini findings-only analysis
- Clinician override + audit event
- Infrastructure permission handshake
- FHIR adapter contract
- 200 unseen/randomized scenarios
- 10-patient mass-casualty scenario with 3 ER beds + 3 OTs + night staffing deficit
- Frontend `app.ui` object-name contract

## Important design principle

The suite does **not** contain patient-ID-specific clinical logic. It uses generated patient records and the same `engine.evaluate()` / `BatchTriageService` pathways used by the application.

## Where it goes

Copy this folder into the project root:

```text
DoomAI/
├── doom_ai/
├── tests/
├── hackathon_tests/     <-- this folder
├── reports/             <-- generated after a run
├── README.md
└── requirements.txt
```

The import adapter automatically looks for `doom_ai`, then `doom`, then `safeguard`, so it can be used during the naming transition.

## Run

From the project root, with the project virtual environment activated:

```powershell
python -m hackathon_tests.scenario_runner
```

For live image analysis in `test_10_image_pipeline.py`, set:

```powershell
$env:GEMINI_API_KEY="YOUR_KEY"
```

If the key is absent, the local image-parser test still runs and the live Gemini case is marked **SKIP** rather than failing the whole suite.

## Reports

After a run:

```text
reports/
├── hackathon_latest.json
├── hackathon_latest.csv
└── hackathon_latest.html
```

The HTML report is intended for judges: open it in a browser after running the suite.

## Interpreting results

A `PASS` means the tested software invariant held for the scenario. A `FAIL` means the implementation or interface does not satisfy that invariant. A `SKIP` means an optional dependency/feature was not available in the current environment.

The suite is a software validation harness, not clinical validation. None of the test cases should be presented as evidence that the model is medically safe for autonomous use.
