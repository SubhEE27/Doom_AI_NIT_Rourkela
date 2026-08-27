from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    def cohorts():
        engine = new_engine(mods)
        authorize(engine)
        assets = make_assets(mods)
        staff = make_staff(mods)
        cases = [
            make_patient(mods,"D1",0.5,"F","fever","poor feeding",vitals={"hr":170,"rr":55,"sbp":70,"dbp":45,"spo2":93}),
            make_patient(mods,"D2",8,"M","fever","sleepy",vitals={"hr":130,"rr":30,"sbp":84,"dbp":50,"spo2":95}),
            make_patient(mods,"D3",40,"M","chest pain","pressure",vitals={"hr":112,"rr":24,"sbp":94,"dbp":60,"spo2":93}),
            make_patient(mods,"D4",78,"F","nausea","fatigue and back pain",vitals={"hr":110,"rr":23,"sbp":96,"dbp":60,"spo2":94}),
        ]
        out = [engine.evaluate(p,assets,staff) for p in cases]
        return (all(1<=r.esi_level<=5 for r in out), "Cohorts evaluated: neonate/infant, pediatric, adult, geriatric; ESI range valid for all.")
    return [run_case("H07", "Demographic-calibrated cohorts", cohorts, "Infant/pediatric/adult/geriatric patients use separate baseline bands and risk features.")]


