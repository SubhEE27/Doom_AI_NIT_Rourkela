from .common import load_modules, run_case, skip_case
from datetime import datetime


def run():
    mods = load_modules()
    if mods["ambulance"] is None:
        return [skip_case("H09", "Ambulance pre-arrival telemetry", "AmbulanceFeedService not present in current checkout.")]

    def ambulance():
        feed_cls = mods["ambulance"].AmbulanceFeedService
        rec_cls = mods["ambulance"].AmbulanceRecord
        feed = feed_cls()
        feed.register(rec_cls(patient_id="AMB-001", patient_name="Demo Patient", recorded_at=datetime.now(), hr=118, rr=26, sbp=94, dbp=61, spo2=91, chief_complaint="chest pressure", narrative="Telemetry captured en route."))
        found = feed.find("AMB-001")
        found_by_name = feed.find("Demo Patient")
        payload = feed.build_preload_payload(found)
        return (found is not None and found_by_name is not None and payload["spo2"] == 91, f"Lookup by ID and name succeeded; preloaded telemetry HR={payload['hr']}, RR={payload['rr']}, SBP={payload['sbp']}, SpO2={payload['spo2']}.")
    return [run_case("H09", "Ambulance pre-arrival data lookup and preload", ambulance, "Ambulance telemetry is an evidence source; it is preloaded into patient context rather than assigning ESI on upload.")]


