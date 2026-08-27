from __future__ import annotations
import re
from math import isfinite
from typing import Any, Dict, Optional
from doom.models.domain import AgeCohort, PatientRecord, VITAL_BANDS

class IngestionEngine:
    CRITICAL_VITALS = ("hr", "rr", "sbp", "dbp", "spo2")

    def infer_cohort(self, age_years: float) -> AgeCohort:
        if age_years < 1: return AgeCohort.NEONATE_INFANT
        if age_years <= 12: return AgeCohort.PEDIATRIC
        if age_years <= 64: return AgeCohort.ADULT
        return AgeCohort.GERIATRIC

    @staticmethod
    def _clean_numeric(value: Optional[float]) -> Optional[float]:
        if value is None: return None
        try: value = float(value)
        except (TypeError, ValueError): return None
        return value if isfinite(value) else None

    def normalize(self, patient: PatientRecord) -> Dict[str, Any]:
        cohort = self.infer_cohort(patient.age_years)
        band = VITAL_BANDS[cohort]
        vitals = {k.lower(): self._clean_numeric(v) for k, v in patient.vitals.items()}
        missing = [k for k in self.CRITICAL_VITALS if vitals.get(k) is None]
        proxies = {f"baseline_proxy_{k}": (getattr(band, f"{k}_min") if k != "spo2" else band.spo2_min) for k in missing}
        return {
            "cohort": cohort,
            "vitals": vitals,
            "proxy_baseline": proxies,
            "missing_critical": missing,
            "history_known": patient.history_known and patient.files_available,
            "narrative": re.sub(r"\s+", " ", patient.narrative.strip().lower()),
            "complaint": re.sub(r"\s+", " ", patient.chief_complaint.strip().lower()),
        }

