from __future__ import annotations
import re
from typing import Any, Dict, List
from doom.models.domain import AgeCohort, PatientRecord, RiskAssessment, VITAL_BANDS
from doom.core.ingestion import IngestionEngine

class RiskStratifier:
    SYNDROME_MAP = {
        "chest": (["chest pain","chest pressure","tightness","jaw pain","epigastric pain"], ["acute coronary syndrome","aortic catastrophe","pulmonary embolism","pneumothorax"]),
        "dyspnea": (["shortness of breath","dyspnea","breathless","difficulty breathing","respiratory distress"], ["acute respiratory failure","severe infection","pulmonary embolism","acute heart failure"]),
        "neuro": (["facial droop","slurred speech","aphasia","confusion","unresponsive","seizure"], ["acute stroke","intracranial hemorrhage","seizure/status epilepticus"]),
        "infection": (["fever","chills","rigors","sepsis","very sleepy"], ["sepsis/septic shock","meningitis/encephalitis","severe pneumonia"]),
        "bleeding": (["vomiting blood","hematemesis","melena","heavy bleeding","bleeding"], ["major hemorrhage","hemorrhagic shock","GI bleed"]),
        "allergy": (["anaphylaxis","throat swelling","wheeze","allergic reaction"], ["anaphylaxis","acute airway compromise"]),
        "trauma": (["trauma","fall","crash","collision","stab","crush"], ["major trauma","occult hemorrhage","traumatic brain injury"]),
        "metabolic": (["diabetic","vomiting","polyuria","polydipsia","low sugar","hypoglycemia","dka"], ["hypoglycemia","diabetic ketoacidosis","hyperosmolar crisis"]),
        "pregnancy": (["pregnant","pregnancy","vaginal bleeding","contractions"], ["ectopic pregnancy","obstetric hemorrhage","pre-eclampsia/eclampsia"]),
    }

    def _active_keyword(self, text: str, keyword: str) -> bool:
        match = re.search(r"(?:^|[^a-z0-9])" + re.escape(keyword) + r"(?:$|[^a-z0-9])", text)
        if not match: return False
        prefix = text[max(0, match.start()-12):match.start()].strip()
        return not re.search(r"(?:no|not|denies|without)$", prefix)

    def _text(self, patient: PatientRecord) -> str:
        return " ".join([patient.chief_complaint.lower(), patient.narrative.lower(), " ".join(patient.comorbidities).lower(), " ".join(patient.image_tags).lower()])

    def assess(self, patient: PatientRecord, ingested: Dict[str, Any]) -> RiskAssessment:
        cohort = ingested["cohort"]; vitals = ingested["vitals"]; text = self._text(patient); band = VITAL_BANDS[cohort]
        abnormal: List[str] = []; critical: List[str] = []; syndromes: List[str] = []; ambiguity: List[str] = []
        missing = list(ingested["missing_critical"])
        checks = {"hr": (band.hr_min, band.hr_max), "rr": (band.rr_min, band.rr_max), "sbp": (band.sbp_min, band.sbp_max), "dbp": (band.dbp_min, band.dbp_max), "spo2": (band.spo2_min, float("inf"))}
        for key, (lo, hi) in checks.items():
            val = vitals.get(key)
            if val is not None and not (lo <= val <= hi): abnormal.append(f"{key.upper()} {val:g} outside {cohort.value} demo band")
        hr, sbp, dbp = vitals.get("hr"), vitals.get("sbp"), vitals.get("dbp")
        si = hr / sbp if hr is not None and sbp and sbp > 0 else None
        threshold = 1.35 if cohort == AgeCohort.NEONATE_INFANT else (1.10 if cohort == AgeCohort.PEDIATRIC else 1.0)
        si_label = "not available"
        if si is not None:
            si_label = ("SIPA-like: high" if cohort in {AgeCohort.NEONATE_INFANT, AgeCohort.PEDIATRIC} and si >= threshold else "SI: high" if cohort not in {AgeCohort.NEONATE_INFANT, AgeCohort.PEDIATRIC} and si > 1.0 else "not high")
            if si > 1.0: critical.append(f"shock index elevated ({si:.2f})")
        pp = sbp - dbp if sbp is not None and dbp is not None else None
        if pp is not None and pp < 25: critical.append(f"narrow pulse pressure ({pp:.0f} mmHg)")
        spo2, rr = vitals.get("spo2"), vitals.get("rr")
        if spo2 is not None and spo2 < 85: critical.append("severe hypoxemia")
        elif spo2 is not None and spo2 < band.spo2_min: critical.append("hypoxemia")
        if rr is not None and rr >= 35: critical.append("marked respiratory distress")
        if rr is not None and rr <= 7: critical.append("marked bradypnea")
        if sbp is not None and sbp < 80: critical.append("severe hypotension")
        elif sbp is not None and sbp < 90: critical.append("hypotension")
        if any(self._active_keyword(text, x) for x in ["unresponsive","altered mental status","not responding"]): critical.append("altered consciousness")
        if any(self._active_keyword(text, x) for x in ["cardiac arrest","pulseless","apneic","airway obstruction","massive hemorrhage","severe anaphylaxis"]): critical.append("possible immediate life threat")
        for _, (keywords, candidates) in self.SYNDROME_MAP.items():
            if any(self._active_keyword(text, k) for k in keywords): syndromes.extend(candidates)
        if not patient.history_known or not patient.files_available: ambiguity.append("history/files unavailable")
        if missing: ambiguity.append("critical vital fields missing")
        if patient.age_years >= 65 and any(self._active_keyword(text, x) for x in ["nausea","back pain","fatigue"]):
            ambiguity.append("geriatric atypical vascular presentation possible")
            syndromes.extend(["aortic catastrophe","acute coronary syndrome"])
        if patient.age_years < 1 and self._active_keyword(text,"fever"): ambiguity.append("infant age increases consequence of missed infection")
        syndromes = list(dict.fromkeys(syndromes))
        completeness = sum(vitals.get(k) is not None for k in IngestionEngine.CRITICAL_VITALS)/5
        completeness = min(1.0, completeness + (0.10 if patient.history_known and patient.files_available else 0) + (0.08 if patient.labs else 0) + (0.05 if patient.image_tags else 0))
        return RiskAssessment(si, si_label, pp, abnormal, list(dict.fromkeys(critical)), syndromes[:8], missing, list(dict.fromkeys(ambiguity)), round(completeness,3))

