from .common import load_modules, new_engine, make_assets, make_staff, authorize, make_patient, run_case


def run():
    mods = load_modules()
    def override():
        engine = new_engine(mods)
        authorize(engine)
        patient = make_patient(mods,"O1",68,"M","chest pain","pressure",vitals={"hr":100,"rr":20,"sbp":108,"dbp":70,"spo2":96})
        rec = engine.evaluate(patient, make_assets(mods), make_staff(mods))
        updated = engine.clinician_override(patient, rec, "DR-DEMO-01", min(2, rec.esi_level), "NEW_CLINICAL_FINDING", "Clinician identifies additional high-risk feature after bedside reassessment.")
        events = getattr(engine.audit, "events", ())
        return (updated.clinician_override is True and len(events) >= 2 and any(e.action == "TRIAGE_OVERRIDE" for e in events), f"Override recorded; audit events={len(events)}; chain validation={engine.audit.verify_chain() if hasattr(engine.audit,'verify_chain') else 'n/a'}.")
    return [run_case("H11", "Clinician override and immutable audit event", override, "Manual override requires a structured reason and is appended to the audit trail.")]


