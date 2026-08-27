from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from doom.models.domain import HospitalAssets


@dataclass(frozen=True)
class HospitalProfile:
    hospital_id: str
    display_name: str

    emergency_rooms_total: int
    emergency_rooms_available: int

    operating_theatres_total: int
    operating_theatres_available: int

    daily_ed_visits: int
    ed_wait_minutes: float

    nearby_facilities: list[dict[str, Any]]


class HospitalDatabaseAdapter:
    """
    Simulated hospital database adapter.

    Later this class can be replaced by:
        Hospital HIS
        FHIR
        ABDM-compatible connector
        REST API
        hospital bed-management API
    """

    def __init__(self) -> None:

        self._records: Dict[
            str,
            HospitalProfile
        ] = {

            # ------------------------------------------------
            # Tertiary Center
            # ------------------------------------------------

            "SG-IND-001": HospitalProfile(

                hospital_id="SG-IND-001",

                display_name=(
                    "DOOM AI Tertiary Demo Hospital"
                ),

                emergency_rooms_total=3,
                emergency_rooms_available=3,

                operating_theatres_total=3,
                operating_theatres_available=3,

                daily_ed_visits=500,

                ed_wait_minutes=35.0,

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
            ),

            # ------------------------------------------------
            # Large Urban Center
            # ------------------------------------------------

            "SG-IND-002": HospitalProfile(

                hospital_id="SG-IND-002",

                display_name=(
                    "High-Volume Urban Emergency Center"
                ),

                emergency_rooms_total=12,
                emergency_rooms_available=5,

                operating_theatres_total=8,
                operating_theatres_available=2,

                daily_ed_visits=650,

                ed_wait_minutes=70.0,

                nearby_facilities=[
                    {
                        "name": "Partner Hospital C",
                        "distance_km": 4.1,
                        "available_beds": 12,
                        "travel_minutes": 18,
                        "dispatch_minutes": 8,
                        "receiving_wait_minutes": 7,
                    }
                ],
            ),

            # ------------------------------------------------
            # Rural PHC
            # ------------------------------------------------

            "SG-PHC-001": HospitalProfile(

                hospital_id="SG-PHC-001",

                display_name=(
                    "Rural Primary Health Centre"
                ),

                emergency_rooms_total=1,
                emergency_rooms_available=0,

                operating_theatres_total=0,
                operating_theatres_available=0,

                daily_ed_visits=120,

                ed_wait_minutes=55.0,

                nearby_facilities=[
                    {
                        "name": "District Referral Hospital",
                        "distance_km": 4.8,
                        "available_beds": 10,
                        "travel_minutes": 28,
                        "dispatch_minutes": 12,
                        "receiving_wait_minutes": 12,
                    }
                ],
            ),
        }

    # ========================================================
    # AVAILABLE HOSPITALS
    # ========================================================

    def list_hospitals(
        self
    ) -> list[tuple[str, str]]:

        return [
            (
                profile.hospital_id,
                profile.display_name,
            )
            for profile in self._records.values()
        ]

    # ========================================================
    # FETCH PROFILE
    # ========================================================

    def get_profile(
        self,
        hospital_id: str,
    ) -> HospitalProfile:

        try:

            return self._records[
                hospital_id
            ]

        except KeyError as exc:

            raise KeyError(
                f"Hospital '{hospital_id}' "
                f"not found in registry"
            ) from exc

    # ========================================================
    # APPLY DATABASE PROFILE
    # ========================================================

    def apply_profile(
        self,
        assets: HospitalAssets,
        hospital_id: str,
    ) -> HospitalAssets:

        profile = self.get_profile(
            hospital_id
        )

        assets.hospital_id = (
            profile.hospital_id
        )

        assets.emergency_rooms_total = (
            profile.emergency_rooms_total
        )

        assets.emergency_rooms_available = (
            profile.emergency_rooms_available
        )

        assets.operating_theatres_total = (
            profile.operating_theatres_total
        )

        assets.operating_theatres_available = (
            profile.operating_theatres_available
        )

        assets.daily_ed_visits = (
            profile.daily_ed_visits
        )

        assets.ed_wait_minutes = (
            profile.ed_wait_minutes
        )

        assets.local_bed_capacity = (
            profile.emergency_rooms_total
        )

        assets.nearby_facilities = list(
            profile.nearby_facilities
        )

        # Calculate occupancy dynamically.
        if profile.emergency_rooms_total > 0:

            assets.bed_occupancy_pct = (
                (
                    profile.emergency_rooms_total
                    - profile.emergency_rooms_available
                )
                / profile.emergency_rooms_total
            ) * 100.0

        else:

            assets.bed_occupancy_pct = 100.0

        if profile.operating_theatres_total > 0:

            assets.ot_occupancy_pct = (
                (
                    profile.operating_theatres_total
                    - profile.operating_theatres_available
                )
                / profile.operating_theatres_total
            ) * 100.0

        else:

            assets.ot_occupancy_pct = 100.0

        return assets

    # ========================================================
    # MANUAL OVERRIDE
    # ========================================================

    @staticmethod
    def apply_manual_capacity(
        assets: HospitalAssets,
        *,
        emergency_total: int,
        emergency_available: int,
        ot_total: int,
        ot_available: int,
        ed_wait_minutes: float,
        daily_ed_visits: int,
    ) -> HospitalAssets:

        if emergency_total < 0:
            raise ValueError(
                "Emergency-room total cannot be negative"
            )

        if ot_total < 0:
            raise ValueError(
                "OT total cannot be negative"
            )

        if not (
            0
            <= emergency_available
            <= emergency_total
        ):
            raise ValueError(
                "Invalid emergency-room availability"
            )

        if not (
            0
            <= ot_available
            <= ot_total
        ):
            raise ValueError(
                "Invalid OT availability"
            )

        assets.emergency_rooms_total = (
            emergency_total
        )

        assets.emergency_rooms_available = (
            emergency_available
        )

        assets.operating_theatres_total = (
            ot_total
        )

        assets.operating_theatres_available = (
            ot_available
        )

        assets.local_bed_capacity = (
            emergency_total
        )

        assets.ed_wait_minutes = max(
            float(ed_wait_minutes),
            0.0,
        )

        assets.daily_ed_visits = max(
            int(daily_ed_visits),
            0,
        )

        assets.bed_occupancy_pct = (
            100.0
            if emergency_total == 0
            else (
                (
                    emergency_total
                    - emergency_available
                )
                / emergency_total
            ) * 100.0
        )

        assets.ot_occupancy_pct = (
            100.0
            if ot_total == 0
            else (
                (
                    ot_total
                    - ot_available
                )
                / ot_total
            ) * 100.0
        )

        return assets
