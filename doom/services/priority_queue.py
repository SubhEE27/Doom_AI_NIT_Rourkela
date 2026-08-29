from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from doom.models.domain import (
    PatientRecord,
    TriageRecommendation,
)


@dataclass
class PriorityDecision:
    patient_id: str
    esi_level: int
    urgency_score: float
    queue_rank: int
    reason: str


class EDPRiorityQueue:
    """
    Secondary prioritization layer.

    Primary ordering:
        ESI 1 â†’ ESI 2 â†’ ESI 3 â†’ ESI 4 â†’ ESI 5

    Within the same ESI:
        1. immediate critical physiology
        2. shock / perfusion abnormality
        3. respiratory compromise
        4. neurologic deterioration
        5. high-risk presentation
        6. waiting time
        7. uncertainty / missing data

    This is a prototype prioritization heuristic and must
    be prospectively validated before clinical deployment.
    """

    HIGH_RISK_TERMS = {
        "chest pain": 20,
        "chest pressure": 20,
        "stroke": 25,
        "facial droop": 25,
        "slurred speech": 25,
        "seizure": 20,
        "bleeding": 20,
        "vomiting blood": 25,
        "trauma": 15,
        "difficulty breathing": 25,
        "shortness of breath": 20,
        "anaphylaxis": 30,
        "pregnancy": 15,
        "sepsis": 30,
    }

    def __init__(self) -> None:
        self._arrival_minutes: dict[str, int] = {}

    # ========================================================
    # Register / update waiting time
    # ========================================================

    def set_waiting_time(
        self,
        patient_id: str,
        minutes: int,
    ) -> None:

        self._arrival_minutes[
            patient_id
        ] = max(
            0,
            int(minutes),
        )

    # ========================================================
    # Secondary urgency score
    # ========================================================

    def calculate_urgency_score(
        self,
        patient: PatientRecord,
        recommendation: TriageRecommendation,
    ) -> float:

        score = 0.0

        assessment = (
            recommendation.risk_assessment
        )

        # ----------------------------------------------------
        # Critical physiological flags
        # ----------------------------------------------------

        score += (
            25
            * len(
                assessment.critical_flags
            )
        )

        # ----------------------------------------------------
        # Shock / perfusion
        # ----------------------------------------------------

        shock_index = (
            assessment.shock_index
        )

        if (
            shock_index is not None
            and shock_index >= 1.0
        ):
            score += 30

        elif (
            shock_index is not None
            and shock_index >= 0.9
        ):
            score += 15

        # ----------------------------------------------------
        # Pulse-pressure narrowing
        # ----------------------------------------------------

        pulse_pressure = getattr(
            assessment,
            "pulse_pressure",
            None,
        )

        if (
            pulse_pressure is not None
            and pulse_pressure < 25
        ):
            score += 25

        # ----------------------------------------------------
        # High-risk symptom language
        # ----------------------------------------------------

        text = (
            patient.chief_complaint
            + " "
            + patient.narrative
        ).lower()

        for term, points in (
            self.HIGH_RISK_TERMS.items()
        ):

            if term in text:
                score += points

        # ----------------------------------------------------
        # Uncertainty
        #
        # Missing critical information is treated as a
        # safety concern, not ignored.
        # ----------------------------------------------------

        score += (
            10
            * len(
                assessment.missing_critical_fields
            )
        )

        # ----------------------------------------------------
        # Waiting time
        #
        # Used only as a tie-breaker, not to override
        # a more clinically urgent patient.
        # ----------------------------------------------------

        score += min(
            20,
            self._arrival_minutes.get(
                patient.patient_id,
                0,
            )
            / 5.0,
        )

        # ----------------------------------------------------
        # Pediatric / geriatric vulnerability tie-breaker
        # ----------------------------------------------------

        if (
            patient.age_years < 1
            or patient.age_years >= 75
        ):
            score += 5

        return round(
            score,
            2,
        )

    # ========================================================
    # Sort an already evaluated queue
    # ========================================================

    def rank(
        self,
        patients: list[PatientRecord],
        recommendations: list[TriageRecommendation],
    ) -> list[TriageRecommendation]:

        patient_map = {
            patient.patient_id:
                patient
            for patient in patients
        }

        scored = []

        for recommendation in recommendations:

            patient = patient_map[
                recommendation.patient_id
            ]

            urgency = (
                self.calculate_urgency_score(
                    patient,
                    recommendation,
                )
            )

            print(
                f"[QUEUE] "
                f"{patient.patient_id} | "
                f"ESI={recommendation.esi_level} | "
                f"urgency={urgency:.2f} | "
                f"confidence={recommendation.confidence_pct:.1f}%"
            )

            scored.append(
                (
                    recommendation.esi_level,
                    -urgency,
                    -recommendation.confidence_pct,
                    recommendation.patient_id,
                    recommendation,
                )
            )

        scored.sort(
            key=lambda item: item[:4]
        )

        ordered = []

        for rank, item in enumerate(
            scored,
            start=1,
        ):

            recommendation = item[4]

            recommendation.rank = rank

            # Keep this available for UI/API consumers.
            recommendation.urgency_score = (
                -item[1]
            )

            ordered.append(
                recommendation
            )

        return ordered
