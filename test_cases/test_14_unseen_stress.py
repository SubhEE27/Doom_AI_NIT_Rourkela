from __future__ import annotations

import random

from .common import load_modules, new_engine, make_assets, make_staff, authorize, random_patient, run_case


def run():
    mods = load_modules()
    def stress():
        engine = new_engine(mods)
        authorize(engine)
        assets = make_assets(mods, volume=500, normal_volume=500, daily_ed_visits=500)
        staff = make_staff(mods, shift="day", emergency_physicians=8, nurses=20)
        rng = random.Random(20260824)
        patients = [random_patient(mods, f"U{i:04d}", rng) for i in range(200)]
        failures = []
        results = []
        for p in patients:
            try:
                results.append(engine.evaluate(p, assets, staff))
            except Exception as exc:
                failures.append(f"{p.patient_id}: {type(exc).__name__}: {exc}")
        valid = all(1 <= r.esi_level <= 5 for r in results)
        return (not failures and valid and len(results)==200, f"Generated and evaluated 200 unseen mixed scenarios; failures={len(failures)}; valid ESI outputs={valid}.")
    return [run_case("H14", "Unseen/randomized scenario robustness", stress, "The engine should process novel combinations without matching a predefined patient ID or scenario string.")]


