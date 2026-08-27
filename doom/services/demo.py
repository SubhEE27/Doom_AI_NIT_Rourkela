from __future__ import annotations

from typing import Dict, Optional

from doom.models.domain import (
    HospitalAssets,
    StaffRoster,
)


def base_assets(
    *,
    occupancy: float = 82.0,
    ot_occupancy: float = 75.0,
    volume: int = 100,
    normal_volume: int = 100,
    imaging: bool = True,
    bandwidth: bool = True,
    fiveg: bool = True,
    ed_wait: float = 35.0,

    # Backward-compatible parameter names used by the
    # newer batch test harness.
    bed_occupancy_pct: float | None = None,
    ot_occupancy_pct: float | None = None,
    current_ed_volume: int | None = None,
    daily_ed_visits: int | None = None,
    ed_wait_minutes: float | None = None,

    emergency_rooms_total: int = 3,
    emergency_rooms_available: int = 3,
    operating_theatres_total: int = 3,
    operating_theatres_available: int = 3,
) -> HospitalAssets:
    """
    Factory for HospitalAssets.

    Supports both the original helper parameter names and
    the newer batch-test parameter names so that old tests
    and new tests can coexist.
    """

    # --------------------------------------------------------
    # Resolve aliases
    # --------------------------------------------------------

    final_bed_occupancy = (
        bed_occupancy_pct
        if bed_occupancy_pct is not None
        else occupancy
    )

    final_ot_occupancy = (
        ot_occupancy_pct
        if ot_occupancy_pct is not None
        else ot_occupancy
    )

    final_volume = (
        current_ed_volume
        if current_ed_volume is not None
        else volume
    )

    final_daily_visits = (
        daily_ed_visits
        if daily_ed_visits is not None
        else normal_volume
    )

    final_wait = (
        ed_wait_minutes
        if ed_wait_minutes is not None
        else ed_wait
    )

    # --------------------------------------------------------
    # Calculate available capacity from occupancy only when
    # explicit availability was not supplied.
    # --------------------------------------------------------

    if (
        emergency_rooms_available
        > emergency_rooms_total
    ):
        emergency_rooms_available = (
            emergency_rooms_total
        )

    if (
        operating_theatres_available
        > operating_theatres_total
    ):
        operating_theatres_available = (
            operating_theatres_total
        )

    return HospitalAssets(
        hospital_id="SG-IND-001",

        high_speed_bandwidth=bandwidth,
        five_g_telemetry=fiveg,

        pocus_online=imaging,
        imaging_pipeline_online=imaging,

        bed_occupancy_pct=(
            float(final_bed_occupancy)
        ),

        ot_occupancy_pct=(
            float(final_ot_occupancy)
        ),

        ed_wait_minutes=(
            float(final_wait)
        ),

        local_bed_capacity=(
            emergency_rooms_total
        ),

        current_ed_volume=(
            int(final_volume)
        ),

        normal_ed_volume=(
            int(final_daily_visits)
        ),

        network_latency_ms=18.0,

        daily_ed_visits=(
            int(final_daily_visits)
        ),

        emergency_rooms_total=(
            emergency_rooms_total
        ),

        emergency_rooms_available=(
            emergency_rooms_available
        ),

        operating_theatres_total=(
            operating_theatres_total
        ),

        operating_theatres_available=(
            operating_theatres_available
        ),

        nearby_facilities=[
            {
                "name": "Partner Hospital A",
                "distance_km": 3.5,
                "available_beds": 10,
                "travel_minutes": 12,
                "dispatch_minutes": 5,
                "receiving_wait_minutes": 5,
            },
            {
                "name": "Partner Hospital B",
                "distance_km": 4.7,
                "available_beds": 4,
                "travel_minutes": 21,
                "dispatch_minutes": 10,
                "receiving_wait_minutes": 12,
            },
        ],
    )

def base_staff(
    *,
    shift: str = "day",
    shift_name: str | None = None,
    emergency_physicians: int = 4,
    nurses: int = 8,
    generalists: int = 4,
    specialists: Optional[Dict[str, int]] = None,
) -> StaffRoster:
    """
    Create a StaffRoster.

    Both `shift` and `shift_name` are accepted for compatibility
    with the different modules/tests in the project.

    If both are supplied, `shift_name` takes precedence.
    """

    # --------------------------------------------------------
    # Resolve shift alias
    # --------------------------------------------------------

    selected_shift = (
        shift_name
        if shift_name is not None
        else shift
    )

    selected_shift = (
        str(selected_shift)
        .strip()
        .lower()
    )

    if selected_shift not in {
        "day",
        "night",
        "overnight",
    }:
        raise ValueError(
            "shift must be 'day', 'night', or 'overnight'"
        )

    # Normalize overnight.
    if selected_shift == "overnight":
        selected_shift = "night"

    # --------------------------------------------------------
    # Default specialist roster
    # --------------------------------------------------------

    default_specialists = {
        "neurology": 1,
        "cardiology": 1,
        "obstetrics": 1,
        "trauma surgery": 1,
        "orthopaedics": 1,
        "critical care": 1,
        "generalist": 1,
    }

    if specialists is not None:
        default_specialists.update(
            specialists
        )

    # --------------------------------------------------------
    # Build the actual domain object.
    #
    # StaffRoster expects `shift_name`.
    # --------------------------------------------------------

    return StaffRoster(
        shift_name=selected_shift,

        on_call_doctors=2,

        emergency_physicians=(
            emergency_physicians
        ),

        nurses=nurses,

        generalists=generalists,

        specialists=default_specialists,

        required_min_emergency_physicians=2,

        required_min_nurses=4,
    )

