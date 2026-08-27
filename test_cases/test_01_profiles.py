from .common import CaseResult, load_modules, new_engine, make_assets, make_staff, authorize, run_case


def run():
    mods = load_modules()
    from_profile = "MULTISPECIALTY_TERTIARY_CENTER"
    rural = "RURAL_PRIMARY_HEALTH_CENTRE"
    results = []

    def profile_switch():
        engine = new_engine(mods, from_profile)
        authorize(engine)
        assets = make_assets(mods)
        staff = make_staff(mods, shift="day")
        patient = mods["models"].PatientRecord("P01", 40, "M", "sore throat", vitals={"hr":80,"rr":16,"sbp":120,"dbp":75,"spo2":98})
        r1 = engine.evaluate(patient, assets, staff)
        engine.deployment_profile = rural
        r2 = engine.evaluate(patient, assets, staff)
        engine.deployment_profile = from_profile
        r3 = engine.evaluate(patient, assets, staff)
        return ("L1" in r1.operational_layer and "L2" in r2.operational_layer and "L1" in r3.operational_layer, f"Tertiaryâ†’Ruralâ†’Tertiary layers: {r1.operational_layer} â†’ {r2.operational_layer} â†’ {r3.operational_layer}")

    results.append(run_case("H01", "Tertiary â†’ Rural â†’ Tertiary profile switching", profile_switch, "Rural forces L2; returning to tertiary restores L1-capable state."))
    return results


