from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class AgeCohort(str, Enum):
    NEONATE_INFANT = "neonate/infant"
    PEDIATRIC = "pediatric"
    ADULT = "adult"
    GERIATRIC = "geriatric"

class Layer(str, Enum):
    L1 = "L1-FULL-RESOURCE-OMNI"
    L2 = "L2-ASYMMETRIC-LOW-RESOURCE-SHIELD"
    L3 = "L3-NETWORK-AWARE-TRANSIT-OFFLOADER"
    L4 = "L4-PREDICTIVE-STAFF-ORCHESTRATOR"

@dataclass(frozen=True)
class VitalBand:
    hr_min: int; hr_max: int
    rr_min: int; rr_max: int
    sbp_min: int; sbp_max: int
    dbp_min: int; dbp_max: int
    spo2_min: int

VITAL_BANDS = {
    AgeCohort.NEONATE_INFANT: VitalBand(100, 180, 30, 60, 60, 100, 30, 65, 94),
    AgeCohort.PEDIATRIC: VitalBand(70, 130, 18, 30, 80, 110, 45, 70, 94),
    AgeCohort.ADULT: VitalBand(60, 100, 12, 20, 100, 129, 60, 79, 94),
    AgeCohort.GERIATRIC: VitalBand(58, 96, 12, 22, 100, 139, 58, 84, 93),
}

@dataclass
class PatientRecord:
    patient_id: str
    age_years: float
    sex: str
    chief_complaint: str
    narrative: str = ""
    history_known: bool = True
    comorbidities: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    vitals: Dict[str, Optional[float]] = field(default_factory=dict)
    labs: Dict[str, Optional[float]] = field(default_factory=dict)
    image_tags: List[str] = field(default_factory=list)
    demographic_tags: Dict[str, str] = field(default_factory=dict)
    onset_minutes: Optional[int] = None
    trauma_mechanism: Optional[str] = None
    pregnancy_possible: bool = False
    files_available: bool = True

@dataclass
class HospitalAssets:
    hospital_id: str
    high_speed_bandwidth: bool
    five_g_telemetry: bool
    pocus_online: bool
    imaging_pipeline_online: bool
    bed_occupancy_pct: float
    ot_occupancy_pct: float
    ed_wait_minutes: float
    local_bed_capacity: int
    current_ed_volume: int
    normal_ed_volume: int
    network_latency_ms: float

    # Hospital-scale configuration
    daily_ed_visits: int = 100

    nearby_facilities: List[Dict[str, Any]] = field(
        default_factory=list
    )

    # Physical emergency capacity
    emergency_rooms_total: int = 3
    emergency_rooms_available: int = 3

    # Operating theatre capacity
    operating_theatres_total: int = 3
    operating_theatres_available: int = 3

    @property
    def imaging_online(self) -> bool:
        return (
            self.pocus_online
            and self.imaging_pipeline_online
        )

    @property
    def resource_surge_ratio(self) -> float:
        return (
            self.current_ed_volume
            / max(self.normal_ed_volume, 1)
        )

    @property
    def beds_full(self) -> bool:
        return (
            self.emergency_rooms_available <= 0
        )

    @property
    def ots_full(self) -> bool:
        return (
            self.operating_theatres_available <= 0
        )

@dataclass
class StaffRoster:
    shift_name: str
    on_call_doctors: int
    emergency_physicians: int
    nurses: int
    generalists: int
    specialists: Dict[str, int] = field(default_factory=dict)
    required_min_emergency_physicians: int = 2
    required_min_nurses: int = 4

    @property
    def night_shift(self) -> bool:
        return self.shift_name.lower() in {"night", "overnight"}

    @property
    def personnel_deficit(self) -> bool:
        return self.emergency_physicians < self.required_min_emergency_physicians or self.nurses < self.required_min_nurses

@dataclass
class RiskAssessment:
    shock_index: Optional[float]
    shock_index_label: str
    pulse_pressure: Optional[float]
    abnormal_vitals: List[str]
    critical_flags: List[str]
    possible_syndromes: List[str]
    missing_critical_fields: List[str]
    ambiguity_flags: List[str]
    data_completeness: float

@dataclass
class TriageRecommendation:
    patient_id: str
    esi_level: int
    rationale: List[str]
    confidence_pct: float
    operational_layer: str
    risk_assessment: RiskAssessment
    routing_recommendation: str

    transfer_candidate: bool = False
    specialist_route: Optional[str] = None
    uncertainty_indicator: float = 0.0
    clinician_override: bool = False

    # Batch-triage fields
    rank: Optional[int] = None
    criticality: str = ""
    resource_dispatch: str = ""

