from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    def floor():
        engine = new_engine(mods)
        authorize(engine)
        p = make_patient(mods, "FLOOR1", 50, "U", "vague dizziness", "first visit", history_known=False, files_available=False, vitals={"hr":None,"rr":None,"sbp":None,"dbp":None,"spo2":None})
        r = engine.evaluate(p, make_assets(mods), make_staff(mods))
        return (r.esi_level <= 2, f"Missing critical vitals/history produced ESI {r.esi_level} with uncertainty={r.uncertainty_indicator:.3f} and layer={r.operational_layer}.")
    return [run_case("H08", "Pessimistic safety floor under missing/corrupt data", floor, "Ambiguous or incomplete critical data escalates conservatively and never produces a low-urgency recommendation by accident.")]


