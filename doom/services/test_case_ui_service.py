from __future__ import annotations

from dataclasses import dataclass

from doom.models.domain import PatientRecord


@dataclass
class UITestCase:
    case_id: str
    name: str
    description: str

    hospital_profile: str
    shift: str

    er_total: int
    er_available: int

    ot_total: int
    ot_available: int

    ed_visits: int
    ed_wait: float

    patients: list[PatientRecord]


class TestCaseUIService:
    """
    Supplies deterministic scenarios to the existing Doom AI UI.

    IMPORTANT:
    This service does NOT perform triage.

    It only prepares input data.

    The actual classification is still performed by the
    existing BatchTriageService / DoomTriageEngine pipeline.
    """

    def list_cases(self) -> list[dict[str, str]]:
        """
        Return all 16 official Doom AI validation cases.

        These IDs intentionally match test_case_runner.py so the
        automated tests and the interactive UI use the same case
        catalogue.
        """

        return [
            {
                "id": "H01",
                "name": "H01 — Tertiary → Rural → Tertiary Profile Switching",
            },
            {
                "id": "H02",
                "name": "H02 — Dynamic 50/50 History Availability",
            },
            {
                "id": "H03",
                "name": "H03 — 100–500+ ED/Day Scalability & Surge",
            },
            {
                "id": "H04",
                "name": "H04 — Same-ESI Secondary Priority Reshuffling",
            },
            {
                "id": "H05",
                "name": "H05 — Full ER/OT Capacity + Nearby Transfer",
            },
            {
                "id": "H06",
                "name": "H06 — Polymorphic L1/L2/L3/L4 Controller",
            },
            {
                "id": "H07",
                "name": "H07 — Demographic-Calibrated Cohorts",
            },
            {
                "id": "H08",
                "name": "H08 — Pessimistic Safety Floor",
            },
            {
                "id": "H09",
                "name": "H09 — Ambulance Pre-Arrival Data & Preload",
            },
            {
                "id": "H10",
                "name": "H10 — Clinical Image Ingestion & Findings",
            },
            {
                "id": "H11",
                "name": "H11 — Clinician Override + Immutable Audit",
            },
            {
                "id": "H12",
                "name": "H12 — Runtime System Permissions",
            },
            {
                "id": "H13",
                "name": "H13 — FHIR Middleware Contract",
            },
            {
                "id": "H14",
                "name": "H14 — Unseen / Randomized Scenario Robustness",
            },
            {
                "id": "H15",
                "name": "H15 — 10-Patient Mass-Casualty Surge",
            },
            {
                "id": "H16",
                "name": "H16 — Frontend Object-Name Contract",
            },
        ]

    def load(self, case_id: str) -> UITestCase:

        case_id = (
            str(case_id)
            .strip()
            .upper()
        )

        builders = {
            "H01": self._profile_switching,
            "H02": self._history_mix,
            "H03": self._surge,
            "H04": self._priority_reshuffle,
            "H05": self._full_capacity_transfer,
            "H06": self._layer_controller,
            "H07": self._demographic,
            "H08": self._safety_floor,
            "H09": self._ambulance,
            "H10": self._image_pipeline,
            "H11": self._override_audit,
            "H12": self._permissions,
            "H13": self._fhir,
            "H14": self._unseen_stress,
            "H15": self._mass_casualty,
            "H16": self._ui_contract,
        }

        builder = builders.get(case_id)

        if builder is None:
            raise ValueError(
                f"UI test case '{case_id}' is not available yet."
            )

        return builder()

    def _profile_switching(
        self,
    ) -> UITestCase:

        patients = [
            PatientRecord(
                patient_id="H01-P01",
                age_years=46,
                sex="M",
                chief_complaint=(
                    "Emergency abdominal pain"
                ),
                narrative=(
                    "Profile switching demonstration. "
                    "Patient initially arrives at tertiary center."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 102,
                    "rr": 22,
                    "sbp": 108,
                    "dbp": 68,
                    "spo2": 95,
                },
                image_tags=[],
            ),
            PatientRecord(
                patient_id="H01-P02",
                age_years=29,
                sex="F",
                chief_complaint="Orthopaedic injury",
                narrative=(
                    "Stable injury suitable for lower-resource "
                    "demonstration."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 88,
                    "rr": 18,
                    "sbp": 118,
                    "dbp": 76,
                    "spo2": 98,
                },
                image_tags=[],
            ),
        ]

        return UITestCase(
            case_id="H01",
            name=(
                "H01 — Tertiary → Rural → Tertiary "
                "Profile Switching"
            ),
            description=(
                "Demonstrates switching between "
                "Multispecialty Tertiary Center and "
                "Rural Primary Health Centre profiles."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=5,
            ot_total=3,
            ot_available=3,
            ed_visits=400,
            ed_wait=25,
            patients=patients,
        )

    # =========================================================
    # H02 — 50/50 HISTORY
    # =========================================================

    def _history_mix(self) -> UITestCase:

        patients = []

        for index in range(10):

            history_available = index < 5

            patients.append(
                PatientRecord(
                    patient_id=f"H02-P{index + 1:02d}",
                    age_years=30 + index,
                    sex="M" if index % 2 == 0 else "F",
                    chief_complaint=(
                        "Emergency department arrival"
                    ),
                    narrative=(
                        "Mixed history availability simulation."
                    ),
                    history_known=history_available,
                    files_available=history_available,
                    vitals={
                        "hr": 82 + index,
                        "rr": 18 + (index % 3),
                        "sbp": 118,
                        "dbp": 76,
                        "spo2": 98,
                    },
                    image_tags=[],
                )
            )

        return UITestCase(
            case_id="H02",
            name="H02 — 50/50 History Availability",
            description=(
                "Ten simultaneous arrivals: five with "
                "hospital history and five without history."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=5,
            ot_total=2,
            ot_available=2,
            ed_visits=500,
            ed_wait=35,
            patients=patients,
        )

    # =========================================================
    # H03 — HIGH VOLUME
    # =========================================================

    def _surge(self) -> UITestCase:

        patients = []

        for index in range(25):

            patients.append(
                PatientRecord(
                    patient_id=f"H03-P{index + 1:03d}",
                    age_years=20 + (index % 60),
                    sex="M" if index % 2 == 0 else "F",
                    chief_complaint=(
                        "Emergency arrival"
                    ),
                    narrative=(
                        "High-volume emergency department "
                        "simulation."
                    ),
                    history_known=(index % 2 == 0),
                    files_available=(index % 2 == 0),
                    vitals={
                        "hr": 70 + (index % 60),
                        "rr": 16 + (index % 14),
                        "sbp": 110 + (index % 30),
                        "dbp": 68 + (index % 15),
                        "spo2": 95 + (index % 5),
                    },
                    image_tags=[],
                )
            )

        return UITestCase(
            case_id="H03",
            name="H03 — High-Volume ED Surge",
            description=(
                "Twenty-five simultaneous arrivals at a "
                "hospital configured for 500 ED visits/day."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=10,
            er_available=7,
            ot_total=5,
            ot_available=4,
            ed_visits=500,
            ed_wait=60,
            patients=patients,
        )

    # =========================================================
    # H04 — PRIORITY RESHUFFLE
    # =========================================================

    def _priority_reshuffle(self) -> UITestCase:

        patients = [

            PatientRecord(
                patient_id="H04-P01",
                age_years=58,
                sex="M",
                chief_complaint="Chest pain",
                narrative=(
                    "Pressure-like chest pain."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 106,
                    "rr": 21,
                    "sbp": 108,
                    "dbp": 68,
                    "spo2": 94,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H04-P02",
                age_years=45,
                sex="F",
                chief_complaint="Back pain",
                narrative=(
                    "Moderate acute back pain."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 84,
                    "rr": 18,
                    "sbp": 122,
                    "dbp": 76,
                    "spo2": 98,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H04-P03",
                age_years=71,
                sex="M",
                chief_complaint=(
                    "Nausea and back discomfort"
                ),
                narrative=(
                    "Atypical geriatric presentation. "
                    "Sudden onset."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 118,
                    "rr": 24,
                    "sbp": 92,
                    "dbp": 60,
                    "spo2": 93,
                },
                image_tags=[],
            ),
        ]

        return UITestCase(
            case_id="H04",
            name="H04 — Same-ESI Priority Reshuffle",
            description=(
                "Demonstrates secondary urgency ordering "
                "when multiple patients have comparable ESI."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=5,
            ot_total=2,
            ot_available=2,
            ed_visits=300,
            ed_wait=30,
            patients=patients,
        )

    # =========================================================
    # H05 — FULL CAPACITY + TRANSFER
    # =========================================================

    def _full_capacity_transfer(self) -> UITestCase:

        patients = [

            PatientRecord(
                patient_id="H05-P01",
                age_years=34,
                sex="M",
                chief_complaint=(
                    "Stable isolated femur fracture"
                ),
                narrative=(
                    "Orthopaedic trauma candidate. "
                    "Hemodynamically stable."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 82,
                    "rr": 17,
                    "sbp": 124,
                    "dbp": 78,
                    "spo2": 98,
                },
                image_tags=[
                    "apparent lower limb injury",
                ],
            ),

            PatientRecord(
                patient_id="H05-P02",
                age_years=62,
                sex="M",
                chief_complaint=(
                    "Possible internal bleeding"
                ),
                narrative=(
                    "Blunt abdominal trauma with "
                    "dizziness."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 126,
                    "rr": 30,
                    "sbp": 84,
                    "dbp": 52,
                    "spo2": 91,
                },
                image_tags=[
                    "abdominal bruising",
                ],
            ),

            PatientRecord(
                patient_id="H05-P03",
                age_years=28,
                sex="F",
                chief_complaint=(
                    "Stable ankle fracture"
                ),
                narrative=(
                    "Isolated orthopaedic injury."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 76,
                    "rr": 16,
                    "sbp": 120,
                    "dbp": 76,
                    "spo2": 99,
                },
                image_tags=[
                    "ankle swelling",
                ],
            ),
        ]

        return UITestCase(
            case_id="H05",
            name="H05 — Full Capacity + Transfer",
            description=(
                "All ER/OT capacity is occupied. "
                "Stable overflow patients must be considered "
                "for safe transfer while critical patients "
                "remain locally prioritized."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Night",
            er_total=3,
            er_available=0,
            ot_total=3,
            ot_available=0,
            ed_visits=500,
            ed_wait=120,
            patients=patients,
        )

    def _layer_controller(
        self,
    ) -> UITestCase:

        patients = [
            PatientRecord(
                patient_id="H06-P01",
                age_years=41,
                sex="M",
                chief_complaint=(
                    "Major trauma"
                ),
                narrative=(
                    "High-acuity trauma case for "
                    "operational layer evaluation."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 128,
                    "rr": 31,
                    "sbp": 86,
                    "dbp": 54,
                    "spo2": 90,
                },
                image_tags=[
                    "trauma",
                    "chest asymmetry",
                ],
            ),
            PatientRecord(
                patient_id="H06-P02",
                age_years=36,
                sex="F",
                chief_complaint=(
                    "Stable fracture"
                ),
                narrative=(
                    "Stable orthopaedic candidate "
                    "for resource-layer evaluation."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 80,
                    "rr": 17,
                    "sbp": 122,
                    "dbp": 78,
                    "spo2": 99,
                },
                image_tags=[],
            ),
        ]

        return UITestCase(
            case_id="H06",
            name=(
                "H06 — Polymorphic L1/L2/L3/L4 "
                "Controller"
            ),
            description=(
                "Demonstrates operational adaptation "
                "to resource, network, occupancy and "
                "staff constraints."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Night",
            er_total=3,
            er_available=1,
            ot_total=3,
            ot_available=1,
            ed_visits=500,
            ed_wait=80,
            patients=patients,
        )

    # =========================================================
    # H07 — DEMOGRAPHIC CALIBRATION
    # =========================================================

    def _demographic(self) -> UITestCase:

        patients = [

            PatientRecord(
                patient_id="H07-INF",
                age_years=0.3,
                sex="M",
                chief_complaint=(
                    "Poor feeding and tachypnea"
                ),
                narrative=(
                    "Infant with increased breathing effort."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 158,
                    "rr": 52,
                    "sbp": 72,
                    "dbp": 44,
                    "spo2": 94,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H07-PED",
                age_years=8,
                sex="F",
                chief_complaint=(
                    "Fever and lethargy"
                ),
                narrative=(
                    "Pediatric patient with worsening weakness."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 132,
                    "rr": 30,
                    "sbp": 96,
                    "dbp": 60,
                    "spo2": 95,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H07-ADULT",
                age_years=35,
                sex="M",
                chief_complaint=(
                    "Moderate abdominal pain"
                ),
                narrative=(
                    "Stable adult presentation."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 88,
                    "rr": 18,
                    "sbp": 122,
                    "dbp": 78,
                    "spo2": 98,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H07-GER",
                age_years=78,
                sex="F",
                chief_complaint=(
                    "Nausea and back discomfort"
                ),
                narrative=(
                    "Atypical geriatric presentation."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 116,
                    "rr": 23,
                    "sbp": 94,
                    "dbp": 60,
                    "spo2": 93,
                },
                image_tags=[],
            ),
        ]

        return UITestCase(
            case_id="H07",
            name="H07 — Demographic Calibration",
            description=(
                "Infant, pediatric, adult and geriatric "
                "patients evaluated in one arrival batch."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=5,
            ot_total=2,
            ot_available=2,
            ed_visits=350,
            ed_wait=30,
            patients=patients,
        )

    # =========================================================
    # H08 — PESSIMISTIC SAFETY FLOOR
    # =========================================================

    def _safety_floor(self) -> UITestCase:

        patient = PatientRecord(
            patient_id="H08-P01",
            age_years=0.5,
            sex="U",
            chief_complaint="",
            narrative="Unknown presentation.",
            history_known=False,
            files_available=False,
            vitals={
                "hr": None,
                "rr": None,
                "sbp": None,
                "dbp": None,
                "spo2": None,
            },
            image_tags=[],
        )

        return UITestCase(
            case_id="H08",
            name="H08 — Pessimistic Safety Floor",
            description=(
                "Zero-history infant with ambiguous and "
                "missing vital information."
            ),
            hospital_profile=(
                "Rural Primary Health Centre"
            ),
            shift="Night",
            er_total=1,
            er_available=0,
            ot_total=0,
            ot_available=0,
            ed_visits=120,
            ed_wait=90,
            patients=[patient],
        )

    def _ambulance(
        self,
    ) -> UITestCase:

        patient = PatientRecord(
            patient_id="H09-P01",
            age_years=52,
            sex="M",
            chief_complaint=(
                "Chest trauma with respiratory distress"
            ),
            narrative=(
                "Ambulance telemetry available before "
                "hospital arrival."
            ),
            history_known=False,
            files_available=False,
            vitals={
                "hr": 118,
                "rr": 26,
                "sbp": 94,
                "dbp": 60,
                "spo2": 91,
            },
            image_tags=[
                "visible chest trauma",
            ],
        )

        return UITestCase(
            case_id="H09",
            name=(
                "H09 — Ambulance Pre-Arrival "
                "Data & Preload"
            ),
            description=(
                "Demonstrates ambulance telemetry being "
                "available before the patient reaches the ED."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=4,
            ot_total=3,
            ot_available=3,
            ed_visits=350,
            ed_wait=25,
            patients=[patient],
        )

    def _image_pipeline(
        self,
    ) -> UITestCase:

        patients = [
            PatientRecord(
                patient_id="H10-P01",
                age_years=37,
                sex="M",
                chief_complaint=(
                    "Road traffic accident"
                ),
                narrative=(
                    "Image-assisted trauma assessment."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 112,
                    "rr": 28,
                    "sbp": 98,
                    "dbp": 64,
                    "spo2": 92,
                },
                image_tags=[
                    "visible chest bruising",
                    "chest asymmetry",
                    "superficial bleeding",
                ],
            ),
        ]

        return UITestCase(
            case_id="H10",
            name=(
                "H10 — Clinical Image Ingestion "
                "& Findings"
            ),
            description=(
                "Image findings should be generated separately "
                "and become evidence for final triage only after "
                "the rest of the patient information is evaluated."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=4,
            ot_total=3,
            ot_available=2,
            ed_visits=400,
            ed_wait=35,
            patients=patients,
        )

    def _override_audit(
        self,
    ) -> UITestCase:

        patient = PatientRecord(
            patient_id="H11-P01",
            age_years=64,
            sex="F",
            chief_complaint=(
                "Chest discomfort"
            ),
            narrative=(
                "AI recommendation will be reviewed "
                "by a clinician for override demonstration."
            ),
            history_known=True,
            files_available=True,
            vitals={
                "hr": 96,
                "rr": 20,
                "sbp": 114,
                "dbp": 72,
                "spo2": 96,
            },
            image_tags=[],
        )

        return UITestCase(
            case_id="H11",
            name=(
                "H11 — Clinician Override "
                "+ Immutable Audit"
            ),
            description=(
                "Demonstrates clinician-in-the-loop "
                "override and audit recording."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=5,
            ot_total=2,
            ot_available=2,
            ed_visits=300,
            ed_wait=25,
            patients=[patient],
        )

    def _permissions(
        self,
    ) -> UITestCase:

        patient = PatientRecord(
            patient_id="H12-P01",
            age_years=44,
            sex="M",
            chief_complaint=(
                "Emergency abdominal pain"
            ),
            narrative=(
                "System permission handshake demonstration."
            ),
            history_known=True,
            files_available=True,
            vitals={
                "hr": 92,
                "rr": 19,
                "sbp": 118,
                "dbp": 74,
                "spo2": 97,
            },
            image_tags=[],
        )

        return UITestCase(
            case_id="H12",
            name=(
                "H12 — Runtime System Permissions"
            ),
            description=(
                "Demonstrates runtime authorization for "
                "bed management, staff roster and instrument inventory."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=4,
            ot_total=2,
            ot_available=2,
            ed_visits=300,
            ed_wait=20,
            patients=[patient],
        )

    def _fhir(
        self,
    ) -> UITestCase:

        patient = PatientRecord(
            patient_id="H13-FHIR-01",
            age_years=50,
            sex="M",
            chief_complaint=(
                "Acute abdominal pain"
            ),
            narrative=(
                "FHIR-shaped middleware contract demonstration."
            ),
            history_known=True,
            files_available=True,
            vitals={
                "hr": 94,
                "rr": 20,
                "sbp": 116,
                "dbp": 74,
                "spo2": 97,
            },
            image_tags=[],
        )

        return UITestCase(
            case_id="H13",
            name=(
                "H13 — FHIR Middleware Contract"
            ),
            description=(
                "Demonstrates patient information passing "
                "through the clinical middleware contract."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=4,
            ot_total=2,
            ot_available=2,
            ed_visits=300,
            ed_wait=25,
            patients=[patient],
        )

    def _unseen_stress(
        self,
    ) -> UITestCase:

        patients = [
            PatientRecord(
                patient_id="H14-P01",
                age_years=3,
                sex="F",
                chief_complaint=(
                    "High fever and reduced responsiveness"
                ),
                narrative=(
                    "Previously unseen pediatric scenario."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 148,
                    "rr": 34,
                    "sbp": 90,
                    "dbp": 55,
                    "spo2": 93,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H14-P02",
                age_years=73,
                sex="M",
                chief_complaint=(
                    "Weakness and nausea"
                ),
                narrative=(
                    "Atypical geriatric scenario."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 108,
                    "rr": 23,
                    "sbp": 96,
                    "dbp": 62,
                    "spo2": 94,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H14-P03",
                age_years=34,
                sex="F",
                chief_complaint=(
                    "Minor soft tissue injury"
                ),
                narrative=(
                    "Low-acuity previously unseen scenario."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 78,
                    "rr": 16,
                    "sbp": 122,
                    "dbp": 78,
                    "spo2": 99,
                },
                image_tags=[],
            ),
        ]

        return UITestCase(
            case_id="H14",
            name=(
                "H14 — Unseen / Randomized "
                "Scenario Robustness"
            ),
            description=(
                "Demonstrates that the engine receives a "
                "scenario not dependent on a hardcoded patient ID."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Night",
            er_total=4,
            er_available=2,
            ot_total=2,
            ot_available=1,
            ed_visits=450,
            ed_wait=70,
            patients=patients,
        )

    # =========================================================
    # H15 — MASS CASUALTY
    # =========================================================

    def _mass_casualty(self) -> UITestCase:

        patients = [

            PatientRecord(
                patient_id="H15-P01",
                age_years=42,
                sex="M",
                chief_complaint=(
                    "Severe abdominal trauma"
                ),
                narrative=(
                    "High-speed collision. "
                    "Abdominal pain and dizziness."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 128,
                    "rr": 30,
                    "sbp": 82,
                    "dbp": 52,
                    "spo2": 93,
                },
                image_tags=[
                    "abdominal bruising",
                    "trauma",
                ],
            ),

            PatientRecord(
                patient_id="H15-P02",
                age_years=31,
                sex="M",
                chief_complaint=(
                    "Severe chest trauma "
                    "and difficulty breathing"
                ),
                narrative=(
                    "Motor vehicle collision with "
                    "chest impact and respiratory distress."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 132,
                    "rr": 34,
                    "sbp": 86,
                    "dbp": 54,
                    "spo2": 88,
                },
                image_tags=[
                    "visible chest bruising",
                    "chest asymmetry",
                ],
            ),

            PatientRecord(
                patient_id="H15-P03",
                age_years=24,
                sex="M",
                chief_complaint=(
                    "Severe bleeding from leg"
                ),
                narrative=(
                    "Open traumatic wound."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 118,
                    "rr": 26,
                    "sbp": 94,
                    "dbp": 60,
                    "spo2": 95,
                },
                image_tags=[
                    "visible bleeding",
                    "lower-limb wound",
                ],
            ),

            PatientRecord(
                patient_id="H15-P04",
                age_years=55,
                sex="F",
                chief_complaint=(
                    "Shortness of breath"
                ),
                narrative=(
                    "Smoke inhalation after vehicle fire."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 116,
                    "rr": 32,
                    "sbp": 104,
                    "dbp": 68,
                    "spo2": 89,
                },
                image_tags=[
                    "facial soot",
                ],
            ),

            PatientRecord(
                patient_id="H15-P05",
                age_years=67,
                sex="M",
                chief_complaint="Hip pain",
                narrative=(
                    "Fall from standing height."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 92,
                    "rr": 20,
                    "sbp": 116,
                    "dbp": 74,
                    "spo2": 97,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H15-P06",
                age_years=29,
                sex="F",
                chief_complaint=(
                    "Arm deformity and pain"
                ),
                narrative=(
                    "Suspected closed forearm fracture."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 96,
                    "rr": 19,
                    "sbp": 118,
                    "dbp": 76,
                    "spo2": 98,
                },
                image_tags=[
                    "forearm deformity",
                ],
            ),

            PatientRecord(
                patient_id="H15-P07",
                age_years=44,
                sex="M",
                chief_complaint=(
                    "Severe headache after trauma"
                ),
                narrative=(
                    "Head struck windshield."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 110,
                    "rr": 22,
                    "sbp": 102,
                    "dbp": 64,
                    "spo2": 96,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H15-P08",
                age_years=38,
                sex="F",
                chief_complaint="Ankle injury",
                narrative=(
                    "Stable isolated ankle injury."
                ),
                history_known=True,
                files_available=True,
                vitals={
                    "hr": 78,
                    "rr": 16,
                    "sbp": 124,
                    "dbp": 78,
                    "spo2": 99,
                },
                image_tags=[],
            ),

            PatientRecord(
                patient_id="H15-P09",
                age_years=19,
                sex="M",
                chief_complaint=(
                    "Minor lacerations"
                ),
                narrative=(
                    "Multiple superficial cuts."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 82,
                    "rr": 17,
                    "sbp": 122,
                    "dbp": 78,
                    "spo2": 99,
                },
                image_tags=[
                    "superficial lacerations",
                ],
            ),

            PatientRecord(
                patient_id="H15-P10",
                age_years=7,
                sex="F",
                chief_complaint=(
                    "Difficulty breathing after collision"
                ),
                narrative=(
                    "Pediatric trauma patient with "
                    "increasing respiratory effort."
                ),
                history_known=False,
                files_available=False,
                vitals={
                    "hr": 138,
                    "rr": 34,
                    "sbp": 90,
                    "dbp": 58,
                    "spo2": 92,
                },
                image_tags=[
                    "facial bruising",
                ],
            ),
        ]

        return UITestCase(
            case_id="H15",
            name="H15 — Mass Casualty Surge",
            description=(
                "Ten simultaneous accident victims with "
                "limited emergency-room and OT capacity."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Night",
            er_total=3,
            er_available=3,
            ot_total=3,
            ot_available=3,
            ed_visits=500,
            ed_wait=45,
            patients=patients,
        )

    def _ui_contract(
        self,
    ) -> UITestCase:

        patient = PatientRecord(
            patient_id="H16-P01",
            age_years=40,
            sex="M",
            chief_complaint=(
                "Emergency department presentation"
            ),
            narrative=(
                "Frontend object-name contract demonstration."
            ),
            history_known=True,
            files_available=True,
            vitals={
                "hr": 84,
                "rr": 18,
                "sbp": 120,
                "dbp": 76,
                "spo2": 98,
            },
            image_tags=[],
        )

        return UITestCase(
            case_id="H16",
            name=(
                "H16 — Frontend Object-Name Contract"
            ),
            description=(
                "Demonstrates that the UI widgets required "
                "by the application and test environment are present."
            ),
            hospital_profile=(
                "Multispecialty Tertiary Center"
            ),
            shift="Day",
            er_total=5,
            er_available=5,
            ot_total=2,
            ot_available=2,
            ed_visits=300,
            ed_wait=20,
            patients=[patient],
        )