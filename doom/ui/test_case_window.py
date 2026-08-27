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

        try:

            results = []

            for patient in (
                self.current_test_case.patients
            ):

                recommendation = (
                    self.engine.evaluate(
                        patient,
                        self.assets,
                        self.staff,
                    )
                )

                results.append(
                    (
                        patient,
                        recommendation,
                    )
                )

            self.render_results(results)

            self.window.testCaseStatus.setText(
                (
                    f"{self.current_test_case.case_id} "
                    "executed ✓ | "
                    f"{len(results)} patient(s) evaluated"
                )
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Test Case Execution Error",
                str(exc),
            )

    # ======================================================
    # RESULTS
    # ======================================================

    def render_results(
        self,
        results,
    ) -> None:

        table = self.window.testCaseResults

        table.setRowCount(0)

        for row, (
            patient,
            recommendation,
        ) in enumerate(results):

            table.insertRow(row)

            values = [
                str(
                    getattr(
                        recommendation,
                        "rank",
                        row + 1,
                    )
                ),

                patient.patient_id,

                str(
                    getattr(
                        recommendation,
                        "esi_level",
                        "—",
                    )
                ),

                str(
                    getattr(
                        recommendation,
                        "criticality",
                        "—",
                    )
                ),

                (
                    f"{recommendation.confidence_pct:.1f}%"
                    if getattr(
                        recommendation,
                        "confidence_pct",
                        None,
                    )
                    is not None
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
                    getattr(
                        recommendation,
                        "resource_dispatch",
                        "—",
                    )
                ),

                (
                    "YES"
                    if getattr(
                        recommendation,
                        "transfer_candidate",
                        False,
                    )
                    else "NO"
                ),
            ]

            for column, value in enumerate(values):

                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(value),
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