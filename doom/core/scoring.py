from doom.models.domain import PatientRecord, RiskAssessment

class SafetyFloor:
    def __init__(self, floor_esi: int = 2): self.floor_esi = floor_esi
    def apply(self, esi: int, assessment: RiskAssessment):
        needs_floor = bool(assessment.missing_critical_fields or assessment.ambiguity_flags)
        return (self.floor_esi, True) if needs_floor and esi > self.floor_esi else (esi, False)

class TriageModel:
    def predict(self, patient: PatientRecord, assessment: RiskAssessment) -> int:
        text = f"{patient.chief_complaint.lower()} {patient.narrative.lower()} {' '.join(patient.image_tags).lower()}"
        if any(x in text for x in ["cardiac arrest","pulseless","apneic","airway obstruction","severe anaphylaxis","massive hemorrhage"]): return 1
        if assessment.critical_flags:
            return 1 if any(x in " ".join(assessment.critical_flags).lower() for x in ["severe hypoxemia","severe hypotension","immediate life threat","altered consciousness"]) else 2
        if any(x in text for x in ["stroke","facial droop","slurred speech","chest pain","chest pressure","heavy bleeding","vomiting blood","melena","major trauma","seizure"]): return 2
        if patient.age_years < 13 and any(x in text for x in ["fever","difficulty breathing","very sleepy"]): return 2
        if patient.age_years >= 65 and any(x in text for x in ["nausea","back pain","fatigue"]): return 2
        if any(x in text for x in ["abdominal pain","vomiting","dehydration","dka","diabetic","shortness of breath","head injury","fracture","syncope"]): return 3
        if any(x in text for x in ["laceration","sore throat","rash","ankle sprain","refill","minor burn"]): return 4
        return 5

