from doom.models.domain import PatientRecord, HospitalAssets, StaffRoster

class ClinicalRouting:
    MAP = {"stroke":"neurology/stroke team","facial droop":"neurology/stroke team","chest pain":"cardiology/acute-care team","chest pressure":"cardiology/acute-care team","pregnancy":"obstetrics","vaginal bleeding":"obstetrics","trauma":"trauma surgery","fall":"trauma/geriatrics","sepsis":"critical care/infectious diseases","difficulty breathing":"critical care/respiratory team"}
    def suggest_specialty(self, patient: PatientRecord):
        text = f"{patient.chief_complaint.lower()} {patient.narrative.lower()}"
        return next((v for k,v in self.MAP.items() if k in text), None)

class TransferPlanner:
    def plan(self, patient: PatientRecord, esi: int, assets: HospitalAssets):
        if esi <= 2: return False, "retain locally: high-acuity patient"
        if assets.bed_occupancy_pct < 100: return False, "retain locally: receiving capacity exists"
        candidates = [f for f in assets.nearby_facilities if float(f.get("distance_km",999)) <= 5 and int(f.get("available_beds",0)) > 0]
        if not candidates: return False, "no nearby receiving facility within 5 km with declared capacity"
        candidate = min(candidates, key=lambda f: float(f.get("dispatch_minutes",10))+float(f.get("travel_minutes",20))+float(f.get("receiving_wait_minutes",10)))
        local = max(float(assets.ed_wait_minutes),0)
        transfer = float(candidate.get("dispatch_minutes",10))+float(candidate.get("travel_minutes",20))+float(candidate.get("receiving_wait_minutes",10))
        if transfer + 10 < local:
            return True, f"candidate for clinician-approved transfer to {candidate['name']} ({transfer:.0f} min vs local {local:.0f} min)"
        return False, f"retain locally: transfer {transfer:.0f} min does not beat local {local:.0f} min"

class StaffOrchestrator:
    def orchestrate(self, patient: PatientRecord, esi: int, staff: StaffRoster):
        if not (staff.night_shift and staff.personnel_deficit): return None
        specialty = ClinicalRouting().suggest_specialty(patient)
        if esi <= 2 and specialty:
            key = specialty.split("/")[0]
            if staff.specialists.get(key, 0) > 0:
                return f"push-page {specialty}"
            return "push-page emergency physician/on-call lead"
        return "holding-sequence eligible: reassess at interval with generalist staff"

