from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from doom.services.priority_queue import (
    EDPRiorityQueue,
)

from doom.models.domain import (
    PatientRecord,
    HospitalAssets,
    StaffRoster,
    TriageRecommendation,
)

from doom.services.engine import (
    DoomTriageEngine,
)


CRITICALITY_LABELS = {

    1:
        "IMMEDIATE RESUSCITATION",

    2:
        "EMERGENCY / HIGH RISK",

    3:
        "URGENT",

    4:
        "LESS URGENT",

    5:
        "NON-URGENT",
}


@dataclass
class BatchTriageResult:

    patients: List[PatientRecord]

    recommendations: List[
        TriageRecommendation
    ]

    history_with: int

    history_without: int

    surge_ratio: float

    rooms_full: bool

    ots_full: bool


class BatchTriageService:
    """
    Handles simultaneous ED arrivals.

    IMPORTANT:
    There is NO fixed patient count.

    If 5 patients arrive -> process 5.
    If 50 arrive -> process 50.
    If 500 arrive -> process 500.
    """

    def __init__(
        self,
        engine: DoomTriageEngine,
    ) -> None:

        self.engine = engine

        # Secondary clinical priority queue
        self.priority_queue = (
            EDPRiorityQueue()
        )

    # ========================================================
    # BATCH EVALUATION
    # ========================================================

    def evaluate_batch(
        self,
        patients: Iterable[PatientRecord],
        assets: HospitalAssets,
        staff: StaffRoster,
    ) -> BatchTriageResult:

        patient_list = list(
            patients
        )

        if not patient_list:

            return BatchTriageResult(
                patients=[],
                recommendations=[],
                history_with=0,
                history_without=0,
                surge_ratio=(
                    assets.resource_surge_ratio
                ),
                rooms_full=(
                    assets.beds_full
                ),
                ots_full=(
                    assets.ots_full
                ),
            )

        # ----------------------------------------------------
        # Evaluate EVERY arriving patient independently.
        # ----------------------------------------------------

        recommendations = []

        for patient in patient_list:

            recommendation = (
                self.engine.evaluate(
                    patient,
                    assets,
                    staff,
                )
            )

            recommendations.append(
                recommendation
            )

        # ----------------------------------------------------
        # Primary ordering:
        #     ESI severity
        #
        # Secondary ordering:
        #     urgency score
        #
        # This means two ESI-2 patients are NOT automatically
        # treated as identical priority.
        # ----------------------------------------------------

        recommendations = (
            self.priority_queue.rank(
                patients=patient_list,
                recommendations=recommendations,
            )
        )

        # ----------------------------------------------------
        # History availability monitoring.
        #
        # This is NOT a restriction.
        # 50/50 is an assumption, not a hard requirement.
        # ----------------------------------------------------

        history_with = sum(
            (
                patient.history_known
                and patient.files_available
            )
            for patient in patient_list
        )

        history_without = (
            len(patient_list)
            - history_with
        )

        # ----------------------------------------------------
        # Resource allocation.
        # ----------------------------------------------------

        self._assign_capacity_routes(
            recommendations,
            assets,
        )

        return BatchTriageResult(

            patients=patient_list,

            recommendations=(
                recommendations
            ),

            history_with=(
                history_with
            ),

            history_without=(
                history_without
            ),

            surge_ratio=(
                assets.resource_surge_ratio
            ),

            rooms_full=(
                assets.beds_full
            ),

            ots_full=(
                assets.ots_full
            ),
        )

    # ========================================================
    # RESOURCE ALLOCATION
    # ========================================================

    def _assign_capacity_routes(
        self,
        recommendations: list[
            TriageRecommendation
        ],
        assets: HospitalAssets,
    ) -> None:

        emergency_slots = max(
            assets.emergency_rooms_available,
            0,
        )

        ot_slots = max(
            assets.operating_theatres_available,
            0,
        )

        for rank, rec in enumerate(
            recommendations,
            start=1,
        ):

            rec.rank = rank

            rec.criticality = (
                CRITICALITY_LABELS[
                    rec.esi_level
                ]
            )

            # =================================================
            # ESI 1 / 2
            #
            # DO NOT automatically transfer simply because
            # rooms are full.
            # =================================================

            if rec.esi_level <= 2:

                if emergency_slots > 0:

                    emergency_slots -= 1

                    rec.resource_dispatch = (
                        "LOCAL EMERGENCY ROOM / "
                        "RESUSCITATION PATH"
                    )

                elif (
                    ot_slots > 0
                    and rec.esi_level == 2
                ):

                    ot_slots -= 1

                    rec.resource_dispatch = (
                        "LOCAL HIGH-ACUITY + "
                        "OT PRIORITY PATH"
                    )

                else:

                    rec.resource_dispatch = (
                        "LOCAL HIGH-ACUITY "
                        "ESCALATION â€” "
                        "NO AUTO-TRANSFER"
                    )

                continue

            # =================================================
            # ESI 3 / 4 / 5
            # =================================================

            if emergency_slots > 0:

                emergency_slots -= 1

                rec.resource_dispatch = (
                    "LOCAL EMERGENCY ROOM / "
                    "URGENT OBSERVATION"
                )

                continue

            # ------------------------------------------------
            # Hospital is full.
            #
            # A transfer candidate can now be considered.
            # ------------------------------------------------

            if rec.transfer_candidate:

                rec.resource_dispatch = (
                    "TRANSFER ELIGIBLE â€” "
                    "CLINICIAN APPROVAL REQUIRED"
                )

            else:

                rec.resource_dispatch = (
                    "WAITING / HOLDING SEQUENCE â€” "
                    "CONTINUOUS REASSESSMENT REQUIRED"
                )
