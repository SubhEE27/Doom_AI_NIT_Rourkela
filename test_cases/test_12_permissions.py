from .common import load_modules, new_engine, make_assets, make_staff, make_patient, run_case


def run():
    mods = load_modules()
    def permissions():
        engine = new_engine(mods)
        patient = make_patient(mods,"P12",44,"M","minor injury",vitals={"hr":80,"rr":16,"sbp":120,"dbp":75,"spo2":98})
        assets = make_assets(mods)
        staff = make_staff(mods)
        denied = False
        try:
            engine.evaluate(patient, assets, staff)
        except PermissionError:
            denied = True
        engine.request_system_access_permissions(["BED_MANAGEMENT_SYSTEM","STAFF_ROSTER_DB","INSTRUMENT_INVENTORY"])
        allowed = engine.evaluate(patient, assets, staff)
        return (denied and 1<=allowed.esi_level<=5, f"Unauthorized evaluation blocked={denied}; authorized evaluation succeeded with ESI {allowed.esi_level}.")
    return [run_case("H12", "Runtime system-permission handshake", permissions, "Infrastructure data access is denied until explicit system permissions are granted.")]


