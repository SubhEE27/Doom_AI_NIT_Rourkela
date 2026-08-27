from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class AmbulanceRecord:
    patient_id: str
    patient_name: str
    recorded_at: datetime

    hr: Optional[float] = None
    rr: Optional[float] = None
    sbp: Optional[float] = None
    dbp: Optional[float] = None
    spo2: Optional[float] = None

    # Optional pre-arrival information
    chief_complaint: str = ""
    narrative: str = ""
    source: str = "AMBULANCE_TELEMETRY"


class AmbulanceFeedService:
    """
    Prototype pre-arrival ambulance telemetry registry.

    In production, this class can be replaced by:
        ambulance telemetry gateway
        hospital HIS
        FHIR Observation feed
        ABDM-compatible integration layer
        REST/MQTT telemetry gateway
    """

    def __init__(self) -> None:
        self._records: Dict[str, AmbulanceRecord] = {}

    # --------------------------------------------------------
    # Register / update incoming ambulance data
    # --------------------------------------------------------

    def register(
        self,
        record: AmbulanceRecord,
    ) -> None:

        self._records[
            record.patient_id.strip().lower()
        ] = record

    # --------------------------------------------------------
    # Search using patient ID OR patient name
    # --------------------------------------------------------

    def find(
        self,
        patient_name_or_id: str,
    ) -> Optional[AmbulanceRecord]:

        query = (
            patient_name_or_id
            .strip()
            .lower()
        )

        if not query:
            return None

        # Exact patient-ID match first
        if query in self._records:
            return self._records[query]

        # Then search patient name
        for record in self._records.values():

            if (
                record.patient_name
                .strip()
                .lower()
                == query
            ):
                return record

        return None

    # --------------------------------------------------------
    # Convert ambulance data into UI preload payload
    # --------------------------------------------------------

    def build_preload_payload(
        self,
        record: AmbulanceRecord,
    ) -> dict:

        return {
            "patient_id": record.patient_id,
            "patient_name": record.patient_name,

            "hr": record.hr,
            "rr": record.rr,
            "sbp": record.sbp,
            "dbp": record.dbp,
            "spo2": record.spo2,

            "chief_complaint":
                record.chief_complaint,

            "narrative":
                record.narrative,

            "source":
                record.source,

            "recorded_at":
                record.recorded_at.isoformat(),
        }
