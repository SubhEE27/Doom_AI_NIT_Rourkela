from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class ClinicalDisplayResult:
    """
    Canonical presentation object.

    This object contains the information that should be shown
    to a clinician and reproduced in test-case reports.

    IMPORTANT:
    This class does NOT calculate ESI.
    It only packages the result already produced by the
    clinical engine.
    """

    patient_id: str
    patient_name: str = ""

    age_years: Optional[float] = None
    sex: str = ""

    history_available: bool = False

    chief_complaint: str = ""
    clinical_narrative: str = ""

    # --------------------------------------------------------
    # Vital signs
    # --------------------------------------------------------

    heart_rate: Optional[float] = None
    respiratory_rate: Optional[float] = None
    systolic_bp: Optional[float] = None
    diastolic_bp: Optional[float] = None
    spo2: Optional[float] = None

    # --------------------------------------------------------
    # Image evidence
    # --------------------------------------------------------

    image_findings: str = ""
    image_possible_concerns: list[str] = field(
        default_factory=list
    )
    image_review_required: bool = False

    # --------------------------------------------------------
    # Final triage
    # --------------------------------------------------------

    esi_level: Optional[int] = None
    criticality: str = ""

    urgency_score: Optional[float] = None

    system_confidence_pct: Optional[float] = None
    uncertainty_indicator: Optional[float] = None

    active_layer: str = ""

    # --------------------------------------------------------
    # Clinical indices
    # --------------------------------------------------------

    shock_index: Optional[float] = None
    sipa: Optional[float] = None
    pulse_pressure: Optional[float] = None

    # --------------------------------------------------------
    # Explanation
    # --------------------------------------------------------

    rationale: list[str] = field(
        default_factory=list
    )

    # --------------------------------------------------------
    # Operational routing
    # --------------------------------------------------------

    resource_dispatch: str = ""
    routing_recommendation: str = ""

    transfer_candidate: bool = False
    transfer_destination: str = ""
    transfer_distance_km: Optional[float] = None

    specialist_route: str = ""

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------

    hospital_profile: str = ""
    shift: str = ""

    emergency_rooms_total: Optional[int] = None
    emergency_rooms_available: Optional[int] = None

    operating_theatres_total: Optional[int] = None
    operating_theatres_available: Optional[int] = None

    daily_ed_visits: Optional[int] = None

    # --------------------------------------------------------
    # Accountability
    # --------------------------------------------------------

    clinician_override: bool = False
    override_clinician_id: str = ""
    override_reason_code: str = ""
    override_justification: str = ""

    audit_event_id: str = ""

    # --------------------------------------------------------
    # Test-case context
    # --------------------------------------------------------

    test_case_id: str = ""
    test_case_name: str = ""
    queue_rank: Optional[int] = None

    # --------------------------------------------------------
    # Serialization
    # --------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def build_clinical_display_result(
        patient,
        recommendation,
        assets=None,
        staff=None,
        *,
        patient_name: str = "",
        image_findings: str = "",
        image_possible_concerns: list[str] | None = None,
        image_review_required: bool = False,
        test_case_id: str = "",
        test_case_name: str = "",
    ) -> ClinicalDisplayResult:

        assessment = (
            recommendation.risk_assessment
        )

        # --------------------------------------------------------
        # Patient vitals
        # --------------------------------------------------------

        vitals = getattr(
            patient,
            "vitals",
            {},
        ) or {}

        # --------------------------------------------------------
        # Environment
        # --------------------------------------------------------

        hospital_profile = ""

        if assets is not None:
            hospital_profile = (
                getattr(
                    assets,
                    "hospital_profile",
                    "",
                )
                or getattr(
                    assets,
                    "deployment_profile",
                    "",
                )
            )

        shift = ""

        if staff is not None:
            shift = getattr(
                staff,
                "shift_name",
                "",
            )

        # --------------------------------------------------------
        # Transfer destination
        # --------------------------------------------------------

        transfer_destination = ""

        if hasattr(
            recommendation,
            "transfer_destination",
        ):
            transfer_destination = (
                getattr(
                    recommendation,
                    "transfer_destination",
                )
                or ""
            )

        transfer_distance = getattr(
            recommendation,
            "transfer_distance_km",
            None,
        )

        # --------------------------------------------------------
        # Urgency score
        # --------------------------------------------------------

        urgency_score = getattr(
            recommendation,
            "urgency_score",
            None,
        )

        # --------------------------------------------------------
        # SIPA compatibility
        # --------------------------------------------------------

        sipa = getattr(
            assessment,
            "sipa",
            None,
        )

        if sipa is None:
            sipa = getattr(
                assessment,
                "shock_index_pediatric_adjusted",
                None,
            )

        # --------------------------------------------------------
        # Override data
        # --------------------------------------------------------

        override_clinician_id = getattr(
            recommendation,
            "override_clinician_id",
            "",
        ) or ""

        override_reason = getattr(
            recommendation,
            "override_reason_code",
            "",
        ) or ""

        override_justification = getattr(
            recommendation,
            "override_justification",
            "",
        ) or ""

        audit_event_id = getattr(
            recommendation,
            "audit_event_id",
            "",
        ) or ""

        return ClinicalDisplayResult(

            patient_id=(
                patient.patient_id
            ),

            patient_name=patient_name,

            age_years=getattr(
                patient,
                "age_years",
                None,
            ),

            sex=getattr(
                patient,
                "sex",
                "",
            ),

            history_available=(
                bool(
                    getattr(
                        patient,
                        "history_known",
                        False,
                    )
                    and
                    getattr(
                        patient,
                        "files_available",
                        False,
                    )
                )
            ),

            chief_complaint=(
                getattr(
                    patient,
                    "chief_complaint",
                    "",
                )
                or ""
            ),

            clinical_narrative=(
                getattr(
                    patient,
                    "narrative",
                    "",
                )
                or ""
            ),

            heart_rate=vitals.get(
                "hr"
            ),

            respiratory_rate=vitals.get(
                "rr"
            ),

            systolic_bp=vitals.get(
                "sbp"
            ),

            diastolic_bp=vitals.get(
                "dbp"
            ),

            spo2=vitals.get(
                "spo2"
            ),

            image_findings=(
                image_findings
            ),

            image_possible_concerns=(
                image_possible_concerns
                or []
            ),

            image_review_required=(
                image_review_required
            ),

            esi_level=(
                recommendation.esi_level
            ),

            criticality=(
                getattr(
                    recommendation,
                    "criticality",
                    "",
                )
                or ""
            ),

            urgency_score=(
                urgency_score
            ),

            system_confidence_pct=(
                recommendation.confidence_pct
            ),

            uncertainty_indicator=(
                getattr(
                    recommendation,
                    "uncertainty_indicator",
                    None,
                )
            ),

            active_layer=(
                recommendation.operational_layer
            ),

            shock_index=(
                assessment.shock_index
            ),

            sipa=sipa,

            pulse_pressure=(
                assessment.pulse_pressure
            ),

            rationale=list(
                recommendation.rationale
            ),

            resource_dispatch=(
                getattr(
                    recommendation,
                    "resource_dispatch",
                    "",
                )
                or ""
            ),

            routing_recommendation=(
                recommendation.routing_recommendation
            ),

            transfer_candidate=(
                bool(
                    recommendation.transfer_candidate
                )
            ),

            transfer_destination=(
                transfer_destination
            ),

            transfer_distance_km=(
                transfer_distance
            ),

            specialist_route=(
                getattr(
                    recommendation,
                    "specialist_route",
                    "",
                )
                or ""
            ),

            hospital_profile=(
                hospital_profile
            ),

            shift=shift,

            emergency_rooms_total=(
                getattr(
                    assets,
                    "emergency_rooms_total",
                    None,
                )
                if assets is not None
                else None
            ),

            emergency_rooms_available=(
                getattr(
                    assets,
                    "emergency_rooms_available",
                    None,
                )
                if assets is not None
                else None
            ),

            operating_theatres_total=(
                getattr(
                    assets,
                    "operating_theatres_total",
                    None,
                )
                if assets is not None
                else None
            ),

            operating_theatres_available=(
                getattr(
                    assets,
                    "operating_theatres_available",
                    None,
                )
                if assets is not None
                else None
            ),

            daily_ed_visits=(
                getattr(
                    assets,
                    "daily_ed_visits",
                    None,
                )
                if assets is not None
                else None
            ),

            clinician_override=(
                bool(
                    getattr(
                        recommendation,
                        "clinician_override",
                        False,
                    )
                )
            ),

            override_clinician_id=(
                override_clinician_id
            ),

            override_reason_code=(
                override_reason
            ),

            override_justification=(
                override_justification
            ),

            audit_event_id=(
                audit_event_id
            ),

            test_case_id=(
                test_case_id
            ),

            test_case_name=(
                test_case_name
            ),

            queue_rank=(
                getattr(
                    recommendation,
                    "rank",
                    None,
                )
            ),
        )