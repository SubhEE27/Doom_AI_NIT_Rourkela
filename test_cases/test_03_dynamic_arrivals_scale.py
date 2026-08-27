from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    def scale_test():
        engine = new_engine(mods)
        authorize(engine)
        assets = make_assets(mods, volume=500, normal_volume=500, daily_ed_visits=500)
        staff = make_staff(mods, shift="day", emergency_physicians=6, nurses=16)
        patients = [make_patient(mods, f"S{i:03d}", 30+(i%40), "U", "minor injury" if i%5 else "chest pain", vitals={"hr":80 if i%5 else 108,"rr":16 if i%5 else 24,"sbp":120 if i%5 else 102,"dbp":75 if i%5 else 62,"spo2":98 if i%5 else 94}) for i in range(100)]
        out = [engine.evaluate(p, assets, staff) for p in patients]
        surge = make_assets(mods, volume=300, normal_volume=100, daily_ed_visits=500, bed_occupancy_pct=100, ot_occupancy_pct=100)
        surge_results = [engine.evaluate(p, surge, staff) for p in patients[:30]]
        return (len(out)==100 and len(surge_results)==30 and all(1<=r.esi_level<=5 for r in out+surge_results), f"Processed 100 arrivals at 500/day configuration and 30 additional surge arrivals at 3Ã— load.")
    return [run_case("H03", "100â€“500+ ED/day scalability and surge", scale_test, "No fixed 10-patient limit; the same engine handles larger arrival batches.")]


