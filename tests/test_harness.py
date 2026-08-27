from doom.config.settings import DeploymentProfile
from doom.models.domain import PatientRecord
from doom.services.demo import base_assets, base_staff
from doom.services.engine import DoomTriageEngine
from doom.services.arrival_stream import ArrivalStream, HistoryMixMonitor
from doom.api.fhir import patient_to_fhir_bundle

def run():
    assets=base_assets(bed_occupancy_pct=100,ot_occupancy_pct=100,current_ed_volume=300,daily_ed_visits=500,ed_wait_minutes=120)
    staff=base_staff(shift_name="night",emergency_physicians=1,nurses=2,specialists={"trauma surgery":1,"orthopaedics":1,"generalist":1})
    engine=DoomTriageEngine()
    try:
        engine.evaluate(PatientRecord("X",40,"U","ankle fracture",vitals={"hr":80,"rr":18,"sbp":120,"dbp":75,"spo2":98}),assets,staff)
        raise AssertionError("permission guard failed")
    except PermissionError:
        pass
    engine.request_system_access_permissions(["BED_MANAGEMENT_SYSTEM","STAFF_ROSTER_DB","INSTRUMENT_INVENTORY"])
    arriving=[]
    for i in range(10):
        with_history=(i%2==0)
        arriving.append(PatientRecord(f"P{i+1}",35+i,"U","chest pain" if i<2 else "ankle fracture", "arrival narrative", history_known=with_history, files_available=with_history, vitals={"hr":80,"rr":18,"sbp":120,"dbp":75,"spo2":98}))
    results=ArrivalStream(arriving).consume(lambda p: engine.evaluate(p,assets,staff))
    mix=HistoryMixMonitor().inspect(arriving)
    assert len(results)==10
    assert mix["with_history"]==5 and mix["without_history"]==5
    assert all(1<=r.esi_level<=5 for r in results)
    bundle=patient_to_fhir_bundle(arriving[0],results[0]); assert bundle["resourceType"]=="Bundle"
    manual=arriving[0]; engine.process_manual_clinician_entry(manual,"VITAL_SIGNS",{"hr":110}); engine.process_manual_clinician_entry(manual,"CLINICAL_NARRATIVE",{"keywords":["new symptom"]}); engine.process_manual_clinician_entry(manual,"IMAGING_METADATA",{"findings":["POCUS-no-free-fluid"]})
    rural=DoomTriageEngine(DeploymentProfile.RURAL_PRIMARY_HEALTH_CENTRE.value); rural.request_system_access_permissions(["BED_MANAGEMENT_SYSTEM","STAFF_ROSTER_DB","INSTRUMENT_INVENTORY"])
    assert rural.controller.flag(rural.controller.select_layers(assets,staff,arriving[0],rural.deployment_profile))=="L2"
    rec=engine.evaluate(arriving[0],assets,staff); over=engine.clinician_override(arriving[0],rec,"DR-001",2,"MANUAL_REASSESSMENT","Clinician reassessed patient after bedside review."); assert over.clinician_override
    assert engine.audit.verify_chain()
    print("ALL MODULAR TESTS PASSED")
    print(f"Dynamic arrivals processed: {len(arriving)} | history: {mix['with_history']} | no-history: {mix['without_history']} | hospital daily capacity setting: {assets.daily_ed_visits}")

if __name__=="__main__": run()

