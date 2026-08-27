from __future__ import annotations

import json
import sys
from pathlib import Path

from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient


def main(path: str) -> int:
    scenario = json.loads(Path(path).read_text(encoding="utf-8"))
    mods = load_modules()

    engine = new_engine(mods, scenario.get("deployment_profile")) if scenario.get("deployment_profile") else new_engine(mods)
    authorize(engine)

    patients = []
    for item in scenario.get("patients", []):
        patients.append(make_patient(
            mods,
            item["patient_id"],
            float(item.get("age_years", 35)),
            item.get("sex", "U"),
            item.get("chief_complaint", ""),
            item.get("narrative", ""),
            history_known=bool(item.get("history_known", True)),
            files_available=bool(item.get("files_available", item.get("history_known", True))),
            vitals=item.get("vitals", {}),
            labs=item.get("labs", {}),
            comorbidities=item.get("comorbidities", []),
            medications=item.get("medications", []),
            image_tags=item.get("image_tags", []),
            trauma_mechanism=item.get("trauma_mechanism"),
            pregnancy_possible=bool(item.get("pregnancy_possible", False)),
        ))

    a = scenario.get("hospital", {})
    assets = make_assets(mods, **a)
    s = scenario.get("staff", {})
    staff = make_staff(mods, **s)

    if len(patients) == 1:
        recommendations = [engine.evaluate(patients[0], assets, staff)]
    else:
        batch = mods.get("batch")
        if batch is None:
            print("Batch service is unavailable in this checkout.")
            return 2
        recommendations = batch.BatchTriageService(engine).evaluate_batch(patients, assets, staff).recommendations

    print("\nDOOM AI â€” JUDGE SCENARIO\n" + "=" * 90)
    for r in recommendations:
        print(f"Patient {r.patient_id}: ESI={r.esi_level} | confidence={r.confidence_pct}% | layer={r.operational_layer}")
        print("  " + " | ".join(r.rationale))
        print(f"  Route: {r.routing_recommendation}")
        if hasattr(r, "rank") and r.rank is not None:
            print(f"  Rank: {r.rank} | dispatch: {r.resource_dispatch}")
        print()
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python -m hackathon_tests.judge_scenario_runner path/to/scenario.json")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))


