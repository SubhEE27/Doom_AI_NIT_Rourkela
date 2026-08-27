class UncertaintyEstimator:
    def calculate(self, patient, assessment):
        missing_rate = len(assessment.missing_critical_fields) / 5.0
        ambiguity_penalty = min(0.30, 0.10 * len(assessment.ambiguity_flags))
        inconsistency = 0.0
        text = f"{patient.chief_complaint} {patient.narrative}".lower()
        spo2 = patient.vitals.get("spo2")
        if spo2 is not None and spo2 >= 98 and "severe respiratory distress" in text: inconsistency += 0.08
        uncertainty = 0.05 + 0.55 * missing_rate + ambiguity_penalty + inconsistency
        if not patient.history_known or not patient.files_available: uncertainty += 0.08
        return max(0.02, min(0.95, uncertainty))

