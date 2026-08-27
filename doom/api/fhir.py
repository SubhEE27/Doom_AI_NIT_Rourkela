from datetime import datetime, timezone

def patient_to_fhir_bundle(patient, recommendation):
    return {"resourceType":"Bundle","type":"collection","timestamp":datetime.now(timezone.utc).isoformat(),"entry":[
        {"resource":{"resourceType":"Patient","id":patient.patient_id,"gender":patient.sex,"extension":[{"url":"age-years","valueDecimal":patient.age_years}]}},
        {"resource":{"resourceType":"Observation","status":"final","code":{"text":"DOOM AI triage recommendation"},"subject":{"reference":f"Patient/{patient.patient_id}"},"valueInteger":recommendation.esi_level}},
        {"resource":{"resourceType":"ServiceRequest","status":"active","intent":"order","code":{"text":"ED triage decision support"},"subject":{"reference":f"Patient/{patient.patient_id}"},"note":[{"text":f"Recommended ESI {recommendation.esi_level}; confidence {recommendation.confidence_pct}%"}]}}
    ]}

