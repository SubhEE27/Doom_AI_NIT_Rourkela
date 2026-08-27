from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    def mixed_stream():
        engine = new_engine(mods)
        authorize(engine)
        assets = make_assets(mods, volume=20, normal_volume=20)
        staff = make_staff(mods, shift="day")
        patients = []
        for i in range(12):
            history = i < 6
            patients.append(make_patient(mods, f"H{i+1:02d}", 30+i, "U", "abdominal pain", "live arrival", history_known=history, files_available=history, vitals={"hr":80,"rr":18,"sbp":120,"dbp":75,"spo2":98}))
        results = [engine.evaluate(p, assets, staff) for p in patients]
        no_history_layers = [results[i].operational_layer for i in range(6,12)]
        return (len(results)==12 and all(1 <= r.esi_level <= 5 for r in results) and all("L2" in x for x in no_history_layers), f"12 arrivals processed; history=6, no-history=6; no-history layers={no_history_layers}")
    return [run_case("H02", "Dynamic 50/50 prior-history availability", mixed_stream, "Any arrival count can be processed; approximately half may have no prior record and must not break the pipeline.")]


