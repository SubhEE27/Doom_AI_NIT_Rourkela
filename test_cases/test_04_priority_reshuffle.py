from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    if mods["batch"] is None or mods["priority"] is None:
        return [] if False else [__import__("hackathon_tests.common", fromlist=["skip_case"]).skip_case("H04", "Same-ESI secondary priority reshuffling", "BatchTriageService or EDPRiorityQueue is not present in the current checkout.")]

    def reshuffle():
        engine = new_engine(mods)
        authorize(engine)
        batch = mods["batch"].BatchTriageService(engine)
        assets = make_assets(mods)
        staff = make_staff(mods, shift="day")
        high = make_patient(mods, "R1", 72, "M", "chest pain", "diaphoresis and nausea", history_known=True, files_available=True, vitals={"hr":118,"rr":24,"sbp":92,"dbp":60,"spo2":93})
        lower = make_patient(mods, "R2", 42, "F", "chest pain", "mild pain, stable", history_known=True, files_available=True, vitals={"hr":90,"rr":18,"sbp":122,"dbp":76,"spo2":98})
        result = batch.evaluate_batch([lower, high], assets, staff)
        ids = [r.patient_id for r in result.recommendations]
        same_esi = result.recommendations[0].esi_level == result.recommendations[1].esi_level
        return (ids[0] == "R1" if same_esi else result.recommendations[0].esi_level <= result.recommendations[1].esi_level, f"Queue order={ids}; ESI={[r.esi_level for r in result.recommendations]}; same-ESI={same_esi}")
    return [run_case("H04", "Same-ESI secondary priority reshuffling", reshuffle, "Primary sort is ESI; ties are resolved by urgency signals rather than treating equal ESI patients identically.")]


