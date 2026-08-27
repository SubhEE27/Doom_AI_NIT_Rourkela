from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case, skip_case


def run():
    mods = load_modules()
    if mods["fhir"] is None:
        return [skip_case("H13", "FHIR-shaped middleware output", "FHIR adapter not present in current checkout.")]

    def fhir():
        patient = make_patient(mods,"F1",39,"F","abdominal pain","urgent evaluation",vitals={"hr":92,"rr":19,"sbp":116,"dbp":74,"spo2":98})
        engine = new_engine(mods)
        authorize(engine)
        rec = engine.evaluate(patient, make_assets(mods), make_staff(mods))
        adapter = mods["fhir"]
        # Find a conversion function without assuming one exact API name.
        candidate_names = ["patient_to_fhir_bundle", "to_fhir_bundle", "build_bundle", "recommendation_to_bundle", "patient_to_fhir"]
        fn = next((getattr(adapter, n, None) for n in candidate_names if hasattr(adapter, n)), None)
        if fn is None:
            return (False, "FHIR module exists but no known conversion function was found.")
        bundle = fn(patient, rec) if fn.__code__.co_argcount >= 2 else fn(rec)
        return (isinstance(bundle, dict) and bundle.get("resourceType") in {"Bundle", "Patient", "Observation"}, f"FHIR adapter returned resourceType={bundle.get('resourceType') if isinstance(bundle,dict) else type(bundle).__name__}.")
    return [run_case("H13", "FHIR-shaped middleware contract", fhir, "Interoperability layer should expose machine-readable clinical context without coupling the UI to the engine.")]


