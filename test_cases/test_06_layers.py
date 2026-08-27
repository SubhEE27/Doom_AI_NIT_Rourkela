from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    def layers():
        engine = new_engine(mods)
        authorize(engine)
        p = make_patient(mods, "L1", 40, "M", "minor injury", vitals={"hr":80,"rr":16,"sbp":120,"dbp":75,"spo2":99})
        l1 = engine.evaluate(p, make_assets(mods, imaging=True, bandwidth=True, fiveg=True), make_staff(mods, shift="day", emergency_physicians=4, nurses=8))
        p_nohist = make_patient(mods, "L2", 40, "M", "minor injury", history_known=False, files_available=False, vitals={"hr":80,"rr":16,"sbp":120,"dbp":75,"spo2":99})
        l2 = engine.evaluate(p_nohist, make_assets(mods, imaging=False, bandwidth=False, fiveg=False), make_staff(mods, shift="day", emergency_physicians=4, nurses=8))
        l3 = engine.evaluate(p, make_assets(mods, bed_occupancy_pct=100, ot_occupancy_pct=100, emergency_rooms_available=0, operating_theatres_available=0), make_staff(mods, shift="day", emergency_physicians=4, nurses=8))
        l4 = engine.evaluate(p, make_assets(mods), make_staff(mods, shift="night", emergency_physicians=1, nurses=2))
        rural = new_engine(mods, "RURAL_PRIMARY_HEALTH_CENTRE")
        authorize(rural)
        lr = rural.evaluate(p, make_assets(mods, imaging=True, bandwidth=True, fiveg=True), make_staff(mods, shift="day", emergency_physicians=4, nurses=8))
        return ("L1" in l1.operational_layer and "L2" in l2.operational_layer and "L3" in l3.operational_layer and "L4" in l4.operational_layer and lr.operational_layer.startswith("L2"), f"L1={l1.operational_layer}, L2={l2.operational_layer}, L3={l3.operational_layer}, L4={l4.operational_layer}, Rural={lr.operational_layer}")
    return [run_case("H06", "Polymorphic L1/L2/L3/L4 controller", layers, "Each layer activates from its environmental trigger; rural PHC is forced to L2.")]


