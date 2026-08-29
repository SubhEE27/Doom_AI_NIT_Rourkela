from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QFile
from PySide6.QtWidgets import (
    QMessageBox,
    QTableWidgetItem,
)
from PySide6.QtUiTools import QUiLoader

from doom.services.test_case_ui_service import (
    TestCaseUIService,
)
from doom.core.routing import TransferPlanner
from doom.services.batch_triage import BatchTriageService

class TestCaseWindowController:
    """Controller for the isolated DOOM AI Test Case Lab."""

    def __init__(
        self,
        parent=None,
        engine=None,
        batch_service=None,
        assets=None,
        staff=None,
    ) -> None:

        self.parent = parent
        self.engine = engine
        self.batch_service = batch_service
        self.assets = assets
        self.staff = staff
        self.transfer_planner = TransferPlanner()
        self.batch_service = BatchTriageService(self.engine)

        self.window = None
        self.current_test_case = None

        self.service = TestCaseUIService()

        self.load_ui()

    # ======================================================
    # UI
    # ======================================================

    def load_ui(self) -> None:

        loader = QUiLoader()

        ui_path = (
            Path(__file__).resolve().parent
            / "test_case_window.ui"
        )

        ui_file = QFile(str(ui_path))

        if not ui_file.open(QFile.ReadOnly):
            raise RuntimeError(
                f"Could not open test case UI: {ui_path}"
            )

        self.window = loader.load(
            ui_file,
            self.parent,
        )

        ui_file.close()

        if self.window is None:
            raise RuntimeError(
                "Could not load Test Case Lab window."
            )

        self.populate_cases()

        self.window.loadTestCaseButton.clicked.connect(
            self.load_selected_case
        )

        self.window.runTestCaseButton.clicked.connect(
            self.run_selected_case
        )

        self.window.clearTestCaseButton.clicked.connect(
            self.clear_case
        )

    # ======================================================
    # CASE DROPDOWN
    # ======================================================

    def populate_cases(self) -> None:

        self.window.testCaseCombo.clear()

        for case in self.service.list_cases():

            self.window.testCaseCombo.addItem(
                case["name"],
                case["id"],
            )

    # ======================================================
    # LOAD CASE
    # ======================================================

    def load_selected_case(self) -> None:

        case_id = (
            self.window.testCaseCombo.currentData()
        )

        if not case_id:
            return

        try:

            case = self.service.load(case_id)

            self.current_test_case = case

            self.render_patients(
                case.patients
            )

            self.window.testCaseDescription.setText(
                case.description
            )

            self.window.testCaseStatus.setText(
                (
                    f"{case.case_id} loaded ✓ | "
                    f"{len(case.patients)} simulated patient(s)"
                )
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Test Case Error",
                str(exc),
            )

    # ======================================================
    # PATIENT TABLE
    # ======================================================

    def render_patients(
        self,
        patients,
    ) -> None:

        table = self.window.testCasePatients

        table.setRowCount(0)

        for row, patient in enumerate(patients):

            table.insertRow(row)

            values = [
                patient.patient_id,
                str(patient.age_years),
                patient.sex,
                patient.chief_complaint,
                patient.narrative,
                (
                    "YES"
                    if patient.history_known
                    else "NO"
                ),
                str(
                    patient.vitals.get(
                        "hr",
                        "—",
                    )
                ),
                str(
                    patient.vitals.get(
                        "rr",
                        "—",
                    )
                ),
                str(
                    patient.vitals.get(
                        "sbp",
                        "—",
                    )
                ),
                str(
                    patient.vitals.get(
                        "dbp",
                        "—",
                    )
                ),
                str(
                    patient.vitals.get(
                        "spo2",
                        "—",
                    )
                ),
            ]

            for column, value in enumerate(values):

                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
                )

    # ======================================================
    # RUN
    # ======================================================

    def run_selected_case(self) -> None:

        if self.current_test_case is None:
            QMessageBox.information(
                self.window,
                "Test Case Lab",
                "Load a test case first.",
            )
            return

        if self.engine is None:
            QMessageBox.critical(
                self.window,
                "Test Case Lab",
                "DOOM AI engine is not available.",
            )
            return

        if self.assets is None:
            QMessageBox.critical(
                self.window,
                "Test Case Lab",
                "Hospital resource configuration is not available.",
            )
            return

        if self.staff is None:
            QMessageBox.critical(
                self.window,
                "Test Case Lab",
                "Staff configuration is not available.",
            )
            return

        try:

            patients = list(
                self.current_test_case.patients
            )

            # --------------------------------------------------
            # STEP 1: use the SAME batch triage pipeline
            # used by the automated test suite
            # --------------------------------------------------

            batch_service = BatchTriageService(
                self.engine
            )

            batch_result = batch_service.evaluate_batch(
                patients,
                self.assets,
                self.staff,
            )

            # --------------------------------------------------
            # STEP 2: recommendations returned by the
            # existing batch pipeline already contain:
            # ESI, confidence, layer, routing/transfer data
            # --------------------------------------------------

            recommendations = list(
                batch_result.recommendations
            )

            # --------------------------------------------------
            # STEP 3: connect each recommendation back
            # to the simulated patient
            # --------------------------------------------------

            patients_by_id = {
                str(patient.patient_id): patient
                for patient in patients
            }

            ranked = []

            for recommendation in recommendations:

                patient_id = str(
                    getattr(
                        recommendation,
                        "patient_id",
                        "",
                    )
                )

                patient = patients_by_id.get(
                    patient_id
                )

                if patient is not None:
                    ranked.append(
                        (
                            patient,
                            recommendation,
                        )
                    )

            # --------------------------------------------------
            # STEP 4: the BatchTriageService has already
            # performed the real queue/routing logic.
            # Do NOT sort again here.
            # --------------------------------------------------

            routes = {}

            self.render_results(
                ranked,
                routes,
            )

            self.window.testCaseStatus.setText(
                (
                    f"{self.current_test_case.case_id} "
                    "executed ✓ | "
                    f"{len(ranked)} patient(s) evaluated "
                    "| priority queue generated"
                )
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Test Case Execution Error",
                str(exc),
            )

    def priority_sort_key(
        self,
        item,
    ):
        patient, recommendation = item

        risk = getattr(
            recommendation,
            "risk_assessment",
            None,
        )

        shock_index = getattr(
            risk,
            "shock_index",
            None,
        )

        critical_flags = getattr(
            risk,
            "critical_flags",
            [],
        )

        # Lower ESI number = higher priority.
        esi = getattr(
            recommendation,
            "esi_level",
            5,
        )

        # More physiological instability should come earlier.
        shock_value = (
            float(shock_index)
            if shock_index is not None
            else -1.0
        )

        criticality_score = len(
            critical_flags or []
        )

        # Stable deterministic tie-breaker.
        patient_id = str(
            getattr(
                patient,
                "patient_id",
                "",
            )
        )

        return (
            int(esi),
            -criticality_score,
            -shock_value,
            patient_id,
        )

    # ======================================================
    # RESULTS
    # ======================================================

    def get_criticality_label(
        self,
        recommendation,
    ) -> str:

        risk = getattr(
            recommendation,
            "risk_assessment",
            None,
        )

        # Use an explicit criticality field if the engine provides one.
        explicit = getattr(
            recommendation,
            "criticality",
            None,
        )

        if explicit:
            return str(explicit)

        # Otherwise use existing risk flags.
        critical_flags = getattr(
            risk,
            "critical_flags",
            [],
        )

        if critical_flags:
            return "HIGH"

        # Fall back to the actual ESI level rather than
        # incorrectly calling every non-flagged patient NORMAL.
        esi = getattr(
            recommendation,
            "esi_level",
            None,
        )

        mapping = {
            1: "CRITICAL",
            2: "HIGH",
            3: "MODERATE",
            4: "LOW",
            5: "MINIMAL",
        }

        return mapping.get(
            esi,
            "UNSPECIFIED",
        )

    def render_results(
        self,
        results,
        routes=None,
    ) -> None:

        routes = routes or {}

        table = self.window.testCaseResults

        table.setRowCount(0)

        for row, (
            patient,
            recommendation,
        ) in enumerate(results):

            table.insertRow(row)

            route = routes.get(
                patient.patient_id,
                getattr(
                    recommendation,
                    "dispatch_route",
                    "—",
                ),
            )

            transfer_candidate = bool(
                getattr(
                    recommendation,
                    "transfer_candidate",
                    False,
                )
            )

            values = [
                str(row + 1),

                patient.patient_id,

                str(
                    getattr(
                        recommendation,
                        "esi_level",
                        "—",
                    )
                ),

                self.get_criticality_label(
                    recommendation
                ),

                (
                    f"{recommendation.confidence_pct:.1f}%"
                    if getattr(
                        recommendation,
                        "confidence_pct",
                        None,
                    ) is not None
                    else "—"
                ),

                str(
                    getattr(
                        recommendation,
                        "operational_layer",
                        "—",
                    )
                ),

                str(
                    routes.get(
                        patient.patient_id,
                        "-"
                    )
                ),

                "YES" if transfer_candidate else "NO",
            ]

            for column, value in enumerate(values):

                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        value
                    ),
                )

    # ======================================================
    # CLEAR
    # ======================================================

    def clear_case(self) -> None:

        self.current_test_case = None

        self.window.testCaseDescription.setText(
            "No test case loaded."
        )

        self.window.testCaseStatus.setText(
            "Ready."
        )

        self.window.testCasePatients.setRowCount(
            0
        )

        self.window.testCaseResults.setRowCount(
            0
        )
