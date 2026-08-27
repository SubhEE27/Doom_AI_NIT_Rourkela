from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QFile, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QDialogButtonBox,
    QTableWidgetItem,
)
from PySide6.QtUiTools import QUiLoader

from doom.config.settings import DeploymentProfile

from doom.services.ambulance_feed import (
    AmbulanceFeedService,
)

from doom.services.test_case_ui_service import (
    TestCaseUIService,
)

from doom.services.ambulance_gateway_client import (
    AmbulanceGatewayClient,
)

from doom.services.vision_analysis import ( 
    GeminiVisionAnalysisService, 
)

from doom.services.presentation_result import (
    build_clinical_display_result,
)

from doom.models.domain import (
    PatientRecord,
    HospitalAssets,
    StaffRoster,
)

from doom.services.batch_triage import (
    BatchTriageService,
    CRITICALITY_LABELS,
)

from doom.services.hospital_resources import (
    HospitalDatabaseAdapter,
)

from doom.services.image_parser import ImageParser

from doom.ui.test_case_window import (
    TestCaseWindowController,
)

# ============================================================
# FIVE-LEVEL SEVERITY DEFINITIONS
# ============================================================

ESI_LABELS = {
    1: "ESI 1 â€” IMMEDIATE RESUSCITATION",
    2: "ESI 2 â€” EMERGENCY / HIGH RISK",
    3: "ESI 3 â€” URGENT",
    4: "ESI 4 â€” LESS URGENT",
    5: "ESI 5 â€” NON-URGENT",
}

ESI_DESCRIPTIONS = {
    1: (
        "Immediate life-saving intervention required. "
        "Examples include cardiac arrest, airway catastrophe "
        "or profound physiologic collapse."
    ),
    2: (
        "High-risk emergency. Patient requires immediate "
        "clinical assessment and rapid intervention."
    ),
    3: (
        "Urgent condition requiring prompt assessment, "
        "investigation or treatment."
    ),
    4: (
        "Less urgent presentation. Patient is currently "
        "stable but may require limited intervention."
    ),
    5: (
        "Non-urgent presentation with no immediate "
        "life-threatening feature detected."
    ),
}


# ============================================================
# DEPLOYMENT PROFILE MAPPING
# ============================================================

PROFILE_VALUES = {
    "Multispecialty Tertiary Center":
        DeploymentProfile.MULTISPECIALTY_TERTIARY_CENTER.value,

    "Rural Primary Health Centre":
        DeploymentProfile.RURAL_PRIMARY_HEALTH_CENTRE.value,
}


class MainWindowController:
    """
    Presentation/controller layer.

    The UI does not perform clinical scoring itself.
    It gathers information, sends it to DoomTriageEngine,
    and renders the returned recommendation.
    """

    def __init__(
        self,
        engine,
        assets: HospitalAssets,
        staff: StaffRoster,
        ui_path: str,
    ):
        
        self.engine = engine
        self.assets = assets
        self.staff = staff

        self.batch_service = BatchTriageService(
            self.engine
        )

        self.hospital_db = HospitalDatabaseAdapter()

        self.ambulance_feed = (
            AmbulanceFeedService()
        )

        self.batch_recommendations = {}

        self.batch_image_paths = {}

        self.current_recommendation = None
        self.current_patient: Optional[PatientRecord] = None
        self.current_display_result = None
        self.batch_display_results = []
        
        try:
            self.vision_service = (
                GeminiVisionAnalysisService()
            )

            self.image_parser = ImageParser(
                vision_service=self.vision_service
            )

            self.vision_status = (
                "AI vision analysis: READY"
            )

        except Exception as exc:

            # The UI remains usable even without an API key.
            self.vision_service = None

            self.image_parser = ImageParser()

            self.vision_status = (
                "AI vision analysis: "
                f"UNAVAILABLE ({exc})"
            )

        self.last_image_path: Optional[str] = None
        self.last_image_metadata = None

        # ----------------------------------------------------
        # Load Qt Designer UI
        # ----------------------------------------------------

        loader = QUiLoader()

        ui_file = QFile(
            str(
                Path(ui_path).resolve()
            )
        )

        if not ui_file.open(
            QFile.ReadOnly
        ):
            raise RuntimeError(
                f"Unable to open UI: {ui_path}"
            )

        self.window = loader.load(
            ui_file
        )

        ui_file.close()

        self.test_case_ui_service = (
                TestCaseUIService()
            )
        
        self.current_ui_test_case = None

        self.ambulance_gateway_client = (
            AmbulanceGatewayClient(
                base_url="http://127.0.0.1:8000"
            )
        )

        self.latest_ambulance_data = None

        self.setup_ambulance_triage_controls()

        self.window.profileCombo.currentIndexChanged.connect(
            self.update_profile_dependent_features
        )

        self.test_case_window_controller = None

        self.window.openTestCaseLabButton.clicked.connect(
            self.open_test_case_lab
        )

        if self.window is None:
            raise RuntimeError(
                "Qt could not load app.ui"
            )

        # ----------------------------------------------------
        # Button connections
        # ----------------------------------------------------

        self.window.permissionButton.clicked.connect(
            self.on_permissions
        )

        self.window.evaluateButton.clicked.connect(
            self.on_evaluate
        )

        self.window.overrideButton.clicked.connect(
            self.on_override
        )

        self.window.uploadImageButton.clicked.connect(
            self.on_upload_image
        )

        self.window.clearButton.clicked.connect(
            self.on_clear
        )

        self.window.addPatientButton.clicked.connect(
            self.add_batch_patient
        )

        self.window.removePatientButton.clicked.connect(
            self.remove_batch_patient
        )

        self.window.clearBatchButton.clicked.connect(
            self.clear_batch
        )

        self.window.evaluateBatchButton.clicked.connect(
            self.evaluate_batch
        )

        self.window.uploadBatchImageButton.clicked.connect(
            self.upload_batch_image
        )

        self.window.importCsvButton.clicked.connect(
            self.import_batch_csv
        )

        self.window.hospitalDatabaseCombo.currentIndexChanged.connect(
            self.on_hospital_database_changed
        )

        self.window.applyCapacityButton.clicked.connect(
            self.on_apply_manual_capacity
        )

        self.window.ambulanceLookupButton.clicked.connect(
            self.load_ambulance_data
        )

        # ----------------------------------------------------
        # Environment selectors
        # ----------------------------------------------------

        self.window.profileCombo.currentTextChanged.connect(
            self.on_profile_changed
        )

        self.window.shiftCombo.currentTextChanged.connect(
            self.on_shift_changed
        )

        # ----------------------------------------------------
        # Initial UI state
        # ----------------------------------------------------

        self.refresh_environment()
        self.reset_result_panel()
        self.update_profile_dependent_features()
        self.update_triage_input_state()

    # ========================================================
    # SYSTEM PERMISSIONS
    # ========================================================

    def on_permissions(self):

        try:

            self.engine.request_system_access_permissions(
                [
                    "BED_MANAGEMENT_SYSTEM",
                    "STAFF_ROSTER_DB",
                    "INSTRUMENT_INVENTORY",
                ]
            )

            self.window.permissionStatus.setText(
                "Access: AUTHORIZED âœ“"
            )

            self.window.permissionStatus.setStyleSheet(
                "color: green; font-weight: bold;"
            )

            self.window.auditLabel.setText(
                "Audit: infrastructure access permissions "
                "granted and logged."
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Permission Error",
                str(exc),
            )

    # ========================================================
    # HOSPITAL PROFILE
    # ========================================================

    def on_profile_changed(
        self,
        text: str,
    ):

        if text not in PROFILE_VALUES:
            return

        selected_profile = (
            PROFILE_VALUES[text]
        )

        self.apply_deployment_profile(
            selected_profile
        )

    # ========================================================
    # DAY / NIGHT SHIFT
    # ========================================================

    def apply_deployment_profile(
        self,
        profile: str,
    ) -> None:
        """
        Apply a complete deployment configuration.

        Every property is explicitly restored when switching
        profiles so that rural mode cannot leave the system
        partially locked when returning to tertiary mode.
        """

        self.engine.deployment_profile = (
            profile
        )

        is_rural = (
            profile
            == DeploymentProfile
            .RURAL_PRIMARY_HEALTH_CENTRE
            .value
        )

        if is_rural:

            # ====================================================
            # RURAL PRIMARY HEALTH CENTRE
            # ====================================================

            self.assets.high_speed_bandwidth = False
            self.assets.five_g_telemetry = False
            self.assets.pocus_online = False
            self.assets.imaging_pipeline_online = False

            self.window.imageStatus.setText(
                "Advanced imaging disabled â€” "
                "Rural Primary Health Centre"
            )

            self.window.layerLabel.setText(
                "Operational Layer: L2 "
                "LOW-RESOURCE SHIELD"
            )

            # Disable tertiary-only ambulance controls.
            if hasattr(
                self.window,
                "ambulanceGroup",
            ):

                self.window.ambulanceGroup.setEnabled(
                    False
                )

            # Do not allow tertiary telemetry controls.
            if hasattr(
                self.window,
                "ambulanceLookupButton",
            ):

                self.window.ambulanceLookupButton.setEnabled(
                    False
                )

            if hasattr(
                self.window,
                "ambulancePatientLookup",
            ):

                self.window.ambulancePatientLookup.clear()
                self.window.ambulancePatientLookup.setEnabled(
                    False
                )

        else:

            # ====================================================
            # MULTISPECIALTY TERTIARY CENTER
            # ====================================================

            # Explicitly restore all tertiary capabilities.
            self.assets.high_speed_bandwidth = True
            self.assets.five_g_telemetry = True
            self.assets.pocus_online = True
            self.assets.imaging_pipeline_online = True

            self.window.imageStatus.setText(
                "POCUS/eFAST + ambulance telemetry "
                "available"
            )

            self.window.layerLabel.setText(
                "Operational Layer: "
                "L1 FULL-RESOURCE OMNI"
            )

            # Enable tertiary-only ambulance controls.
            if hasattr(
                self.window,
                "ambulanceGroup",
            ):

                self.window.ambulanceGroup.setEnabled(
                    True
                )

            if hasattr(
                self.window,
                "ambulanceLookupButton",
            ):

                self.window.ambulanceLookupButton.setEnabled(
                    True
                )

            if hasattr(
                self.window,
                "ambulancePatientLookup",
            ):

                self.window.ambulancePatientLookup.setEnabled(
                    True
                )

    def on_shift_changed(
        self,
        text: str,
    ):

        self.staff.shift_name = (
            "night"
            if text.lower() == "night"
            else "day"
        )

        self.refresh_environment()

    def lookup_ambulance_patient(
        self,
    ) -> None:
        """
        Look up pre-arrival ambulance information using
        patient ID or patient name and preload the data
        into the single-patient triage form.

        Ambulance telemetry is available only for the
        Multispecialty Tertiary Center profile.
        """

        # --------------------------------------------------------
        # Only tertiary hospitals get the advanced
        # ambulance telemetry workflow.
        # --------------------------------------------------------

        if (
            self.engine.deployment_profile
            != DeploymentProfile
            .MULTISPECIALTY_TERTIARY_CENTER
            .value
        ):

            QMessageBox.information(
                self.window,
                "Ambulance Telemetry",
                (
                    "Ambulance pre-arrival telemetry is "
                    "available only in Multispecialty "
                    "Tertiary Center mode."
                ),
            )

            return

        # --------------------------------------------------------
        # Read patient name / ID entered by user.
        # --------------------------------------------------------

        query = (
            self.window.ambulancePatientLookup
            .text()
            .strip()
        )

        if not query:

            QMessageBox.warning(
                self.window,
                "Ambulance Lookup",
                "Enter a patient name or patient ID.",
            )

            return

        # --------------------------------------------------------
        # Search ambulance feed.
        # --------------------------------------------------------

        record = (
            self.ambulance_feed.find(
                query
            )
        )

        if record is None:

            if hasattr(
                self.window,
                "ambulanceStatus",
            ):

                self.window.ambulanceStatus.setText(
                    "No ambulance pre-arrival record found."
                )

            QMessageBox.information(
                self.window,
                "No Ambulance Data",
                (
                    "No pre-arrival ambulance record "
                    "was found for this patient."
                ),
            )

            return

        # --------------------------------------------------------
        # Convert record to preload payload.
        # --------------------------------------------------------

        payload = (
            self.ambulance_feed
            .build_preload_payload(
                record
            )
        )

        # --------------------------------------------------------
        # Patient identity
        # --------------------------------------------------------

        self.window.patientId.setText(
            str(
                payload["patient_id"]
            )
        )

        if hasattr(
            self.window,
            "patientName",
        ):

            self.window.patientName.setText(
                str(
                    payload["patient_name"]
                )
            )

        # --------------------------------------------------------
        # VITALS
        # --------------------------------------------------------

        if payload["hr"] is not None:

            self.window.hr.setValue(
                int(
                    payload["hr"]
                )
            )

        if payload["rr"] is not None:

            self.window.rr.setValue(
                int(
                    payload["rr"]
                )
            )

        if payload["sbp"] is not None:

            self.window.sbp.setValue(
                int(
                    payload["sbp"]
                )
            )

        if payload["dbp"] is not None:

            self.window.dbp.setValue(
                int(
                    payload["dbp"]
                )
            )

        if payload["spo2"] is not None:

            self.window.spo2.setValue(
                int(
                    payload["spo2"]
                )
            )

        # --------------------------------------------------------
        # Chief complaint
        # --------------------------------------------------------

        if payload["chief_complaint"]:

            self.window.complaint.setPlainText(
                payload["chief_complaint"]
            )

        # --------------------------------------------------------
        # Narrative
        # --------------------------------------------------------

        if payload["narrative"]:

            existing = (
                self.window.narrative
                .toPlainText()
                .strip()
            )

            ambulance_text = (
                "[AMBULANCE PRE-ARRIVAL DATA]\n"
                + payload["narrative"]
            )

            if existing:

                existing += (
                    "\n\n"
                    + ambulance_text
                )

            else:

                existing = ambulance_text

            self.window.narrative.setPlainText(
                existing
            )

        # --------------------------------------------------------
        # Visible UI confirmation
        # --------------------------------------------------------

        if hasattr(
            self.window,
            "ambulanceStatus",
        ):

            self.window.ambulanceStatus.setText(
                (
                    "Ambulance data preloaded âœ“ | "
                    f"Source: "
                    f"{payload['source']} | "
                    f"Recorded: "
                    f"{payload['recorded_at']}"
                )
            )

        # --------------------------------------------------------
        # Store the source against current patient
        # for audit/UI purposes.
        # --------------------------------------------------------

        self.current_ambulance_record = (
            record
        )

    # ========================================================
    # REFRESH HOSPITAL ENVIRONMENT
    # ========================================================

    def refresh_environment(self):

        profile = (
            self.engine.deployment_profile
        )

        # ----------------------------------------------------
        # Shift
        # ----------------------------------------------------

        self.staff.shift_name = (
            "night"
            if self.window.shiftCombo.currentText().lower()
            == "night"
            else "day"
        )
    
        # ----------------------------------------------------
        # Rural PHC
        # ----------------------------------------------------

        if (
            profile
            == DeploymentProfile.RURAL_PRIMARY_HEALTH_CENTRE.value
        ):

            self.assets.high_speed_bandwidth = False
            self.assets.five_g_telemetry = False
            self.assets.pocus_online = False
            self.assets.imaging_pipeline_online = False

            self.window.imageStatus.setText(
                "Image parser: L1 imaging dependency "
                "disabled â€” Rural PHC"
            )

            self.window.layerLabel.setText(
                "Active Layer: L2 HARD-LOCK â€” Rural PHC"
            )

        # ----------------------------------------------------
        # Tertiary center
        # ----------------------------------------------------

        else:

            self.assets.high_speed_bandwidth = True
            self.assets.five_g_telemetry = True
            self.assets.pocus_online = True
            self.assets.imaging_pipeline_online = True

            self.window.imageStatus.setText(
                "Image parser: ready for POCUS/eFAST "
                "metadata ingestion"
            )

            current_shift = (
                self.staff.shift_name.upper()
            )

            self.window.layerLabel.setText(
                f"Operational profile: "
                f"MULTISPECIALTY TERTIARY | "
                f"{current_shift} SHIFT"
            )

        # ----------------------------------------------------
        # Environment summary
        # ----------------------------------------------------

        self.window.historyRatioLabel.setText(
            "Expected ED data mix: "
            "approximately 50% with prior history / "
            "50% without prior history"
        )

    # ========================================================
    # HOSPITAL DATABASE / CAPACITY
    # ========================================================

    def on_hospital_database_changed(
    self,
    index: int,
    ) -> None:

        hospital_id = (
        self.window.hospitalDatabaseCombo
        .currentData()
        )

        if not hospital_id:
            return

        try:

            self.hospital_db.apply_profile(
                self.assets,
                hospital_id,
            )

            self._sync_capacity_controls()

            self.window.batchHospitalStatus.setText(
            (
                    f"Hospital DB synced: "
                    f"ER "
                    f"{self.assets.emergency_rooms_available}/"
                    f"{self.assets.emergency_rooms_total} | "
                    f"OT "
                    f"{self.assets.operating_theatres_available}/"
                    f"{self.assets.operating_theatres_total} | "
                    f"ED/day "
                    f"{self.assets.daily_ed_visits}"
                )
            )

        except Exception as exc:

            QMessageBox.critical(
            self.window,
            "Hospital Database Error",
            str(exc),
        )


    def on_apply_manual_capacity(
        self,
    ) -> None:

        try:

            self.hospital_db.apply_manual_capacity(
                self.assets,

                emergency_total=(
                    self.window.erTotal.value()
                ),

                emergency_available=(
                    self.window.erAvailable.value()
                ),

                ot_total=(
                    self.window.otTotal.value()
                ),

                ot_available=(
                    self.window.otAvailable.value()
                ),

                ed_wait_minutes=(
                    self.window.edWait.value()
                ),

                daily_ed_visits=(
                    self.window.edVisits.value()
                ),
            )

            self.window.batchHospitalStatus.setText(
                (
                    "Manual capacity applied: "
                    f"ER "
                    f"{self.assets.emergency_rooms_available}/"
                    f"{self.assets.emergency_rooms_total} | "
                    f"OT "
                    f"{self.assets.operating_theatres_available}/"
                    f"{self.assets.operating_theatres_total}"
                )
            )

        except Exception as exc:

            QMessageBox.warning(
            self.window,
            "Capacity Error",
            str(exc),
            )


    def _sync_capacity_controls(
        self,
    ) -> None:

        self.window.erTotal.setValue(
            self.assets.emergency_rooms_total
        )

        self.window.erAvailable.setMaximum(
            self.assets.emergency_rooms_total
        )

        self.window.erAvailable.setValue(
            self.assets.emergency_rooms_available
        )

        self.window.otTotal.setValue(
            self.assets.operating_theatres_total
        )

        self.window.otAvailable.setMaximum(
            self.assets.operating_theatres_total
        )

        self.window.otAvailable.setValue(
            self.assets.operating_theatres_available
        )

        self.window.edVisits.setValue(
            self.assets.daily_ed_visits
        )

        self.window.edWait.setValue(
            self.assets.ed_wait_minutes
        )

    # ========================================================
    # DYNAMIC PATIENT ARRIVAL TABLE
    # ========================================================

    def add_batch_patient(
        self,
        values=None,
    ) -> None:

        table = self.window.batchTable

        row = table.rowCount()

        table.insertRow(row)

        defaults = values or [
            f"P{row + 1:03d}",
            "35",
            "U",
            "",
            "",
            "YES",
            "80",
            "18",
            "120",
            "75",
            "98",
        ]

        for column, value in enumerate(
            defaults
        ):

            if column == 5:

                combo = QComboBox()

                combo.addItems(
                    [
                        "YES",
                        "NO",
                    ]
                )

                combo.setCurrentText(
                    str(value).upper()
                )

                table.setCellWidget(
                    row,
                    column,
                    combo,
                )

            else:

                table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        str(value)
                    )
                )

    def remove_batch_patient(
        self,
    ) -> None:

        table = self.window.batchTable

        row = table.currentRow()

        if row < 0:

            QMessageBox.information(
                self.window,
                "Remove Patient",
                "Select a patient row first.",
            )

            return

        table.removeRow(
            row
        )


    def clear_batch(
        self,
    ) -> None:

        self.window.batchTable.setRowCount(
            0
        )

        self.window.batchResults.setRowCount(
            0
        )

        self.window.batchSummary.setText(
            "No batch evaluated."
        )

        self.batch_recommendations.clear()

        self.batch_image_paths.clear()

    
    def _cell_text(
        self,
        row: int,
        column: int,
        default: str = "",
    ) -> str:

        item = (
            self.window.batchTable
            .item(row, column)
        )

        if item is None:

            return default

        return item.text().strip()


    def _cell_float(
        self,
        row: int,
        column: int,
    ):

        text = self._cell_text(
            row,
            column,
        )

        if not text:

            return None

        try:

            return float(text)

        except ValueError:

            return None

    def _rows_to_patients(
        self,
    ) -> list[PatientRecord]:

        patients = []

        table = self.window.batchTable

        for row in range(
            table.rowCount()
        ):

            patient_id = self._cell_text(
                row,
                0,
                f"P{row + 1:03d}",
            )

            age = self._cell_float(
                row,
                1,
            )

            if age is None:

                raise ValueError(
                    f"Row {row + 1}: age is required"
                )

            complaint = self._cell_text(
                row,
                3,
            )

            if not complaint:

                raise ValueError(
                    f"Row {row + 1}: "
                    f"chief complaint is required"
                )

            history_widget = (
                table.cellWidget(
                    row,
                    5,
                )
            )

            history_available = (
                history_widget.currentText()
                == "YES"
                if history_widget
                else True
            )

            patient = PatientRecord(

                patient_id=patient_id,

                age_years=age,

                sex=self._cell_text(
                    row,
                    2,
                    "U",
                ),

                chief_complaint=complaint,

                narrative=self._cell_text(
                    row,
                    4,
                ),

                history_known=(
                    history_available
                ),

                files_available=(
                    history_available
                ),

                vitals={
                    "hr": self._cell_float(
                        row,
                        6,
                    ),

                    "rr": self._cell_float(
                        row,
                        7,
                    ),

                    "sbp": self._cell_float(
                        row,
                        8,
                    ),

                    "dbp": self._cell_float(
                        row,
                        9,
                    ),

                    "spo2": self._cell_float(
                        row,
                        10,
                    ),
                },
            )

            patients.append(
                patient
            )

        return patients

    def upload_batch_image(self) -> None:
        """
        Upload a POCUS/eFAST image for the currently
        selected patient in the batch table.

        The image is stored against the selected patient ID.
        The current image parser performs metadata validation;
        it does not make an autonomous clinical diagnosis.
        """

        table = self.window.batchTable

        row = table.currentRow()

        if row < 0:
            QMessageBox.information(
                self.window,
                "Upload Image",
                "Select a patient row first.",
            )
            return

        patient_id = self._cell_text(
            row,
            0,
        )

        if not patient_id:
            QMessageBox.warning(
                self.window,
                "Upload Image",
                "The selected patient has no Patient ID.",
            )
            return

        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Upload POCUS / eFAST Image",
            "",
            (
                "Medical Images "
                "(*.png *.jpg *.jpeg *.bmp *.webp);;"
                "All Files (*)"
            ),
        )

        if not path:
            return

        try:
            parsed = self.image_parser.parse(
                path
            )

            if not parsed["readable"]:
                raise ValueError(
                    "The selected image could not be read."
                )

            # Store the image against the selected patient.
            self.batch_image_paths[
                patient_id
            ] = {
                "path": path,
                "metadata": parsed,
            }

            # Show status in the UI.
            self.window.batchHospitalStatus.setText(
                (
                    f"Image attached to {patient_id}: "
                    f"{parsed['filename']} | "
                    f"{parsed['format']} | "
                    f"{parsed['width']}Ã—"
                    f"{parsed['height']} | "
                    f"{parsed['size_kb']} KB"
                )
            )

            QMessageBox.information(
                self.window,
                "Image Attached",
                (
                    f"POCUS/eFAST image attached to "
                    f"{patient_id}.\n\n"
                    "The image is available for clinician "
                    "review and metadata ingestion."
                ),
            )

        except Exception as exc:
            QMessageBox.warning(
                self.window,
                "Image Upload Error",
                str(exc),
            )

    def evaluate_batch(
        self,
    ) -> None:

        try:

            patients = (
                self._rows_to_patients()
            )

            if not patients:

                QMessageBox.information(
                    self.window,
                    "Batch Triage",
                    "No patient arrivals entered.",
                )

                return

            result = (
                self.batch_service
                .evaluate_batch(
                    patients,
                    self.assets,
                    self.staff,
                )
            )

            self._render_batch_results(
                result
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Batch Evaluation Error",
                str(exc),
            )

    
    def import_batch_csv(
        self,
    ) -> None:
        """
        Import multiple ED arrivals from a CSV file.

        Expected columns:

            patient_id
            age
            sex
            chief_complaint
            narrative
            history
            hr
            rr
            sbp
            dbp
            spo2

        Example:

            patient_id,age,sex,chief_complaint,narrative,history,hr,rr,sbp,dbp,spo2
            P001,65,M,chest pain,Pressure for 20 minutes,YES,112,22,94,60,91
            P002,24,F,ankle sprain,Minor sports injury,NO,78,16,120,75,99

        The CSV import only populates the arrival table.
        Clinical triage is performed later by
        Evaluate All Arrivals.
        """

        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Import ED Patient CSV",
            "",
            "CSV Files (*.csv);;All Files (*)",
        )

        if not path:
            return

        required_columns = {
            "patient_id",
            "age",
            "sex",
            "chief_complaint",
            "narrative",
            "history",
            "hr",
            "rr",
            "sbp",
            "dbp",
            "spo2",
        }

        imported_count = 0

        try:
            with open(
                path,
                "r",
                encoding="utf-8-sig",
                newline="",
            ) as csv_file:

                reader = csv.DictReader(
                    csv_file
                )

                if reader.fieldnames is None:
                    raise ValueError(
                        "CSV file does not contain a header row."
                    )

                # Normalize headers.
                actual_headers = {
                    header.strip().lower()
                    for header in reader.fieldnames
                    if header is not None
                }

                missing_headers = (
                    required_columns
                    - actual_headers
                )

                if missing_headers:
                    raise ValueError(
                        "CSV is missing required columns: "
                        + ", ".join(
                            sorted(missing_headers)
                        )
                    )

                for csv_row in reader:

                    # Ignore completely empty rows.
                    if not any(
                        str(value).strip()
                        for value in csv_row.values()
                        if value is not None
                    ):
                        continue

                    history_value = (
                        str(
                                csv_row.get(
                                "history",
                                "",
                            )
                        )
                        .strip()
                        .upper()
                    )

                    if history_value not in {
                        "YES",
                        "NO",
                    }:
                        history_value = (
                            "YES"
                            if history_value
                            in {
                                "Y",
                                "TRUE",
                                "1",
                            }
                            else "NO"
                        )

                    values = [
                        str(
                            csv_row.get(
                                "patient_id",
                                "",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "age",
                                "",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "sex",
                                "U",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "chief_complaint",
                                "",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "narrative",
                                "",
                            )
                        ).strip(),

                        history_value,

                        str(
                            csv_row.get(
                                "hr",
                                "",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "rr",
                                "",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "sbp",
                                "",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "dbp",
                                "",
                            )
                        ).strip(),

                        str(
                            csv_row.get(
                                "spo2",
                                "",
                            )
                        ).strip(),
                    ]

                    self.add_batch_patient(
                        values
                    )

                    imported_count += 1

            self.window.batchHospitalStatus.setText(
                (
                    f"CSV import complete: "
                    f"{imported_count} patient(s) added."
                )
            )

            QMessageBox.information(
                self.window,
                "CSV Import Complete",
                (
                    f"{imported_count} patient(s) "
                    f"added to the live ED arrival queue."
                ),
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "CSV Import Error",
                str(exc),
            )


    def _render_batch_results(
        self,
        batch_result,
    ) -> None:

        table = self.window.batchResults

        table.setRowCount(0)

        self.batch_recommendations = {
            recommendation.patient_id:
                recommendation
            for recommendation
            in batch_result.recommendations
        }

        self.batch_display_results = []

        patient_map = {
            patient.patient_id: patient
            for patient in batch_result.patients
        }
                    
        for row_index, recommendation in enumerate(
            batch_result.recommendations
        ):

            patient = patient_map[
                recommendation.patient_id
            ]

            display_result = (
                build_clinical_display_result(
                    patient,
                    recommendation,
                    self.assets,
                    self.staff,
                )
            )

            self.batch_display_results.append(
                display_result
            )

            table.insertRow(
                row_index
            )

            values = [

                str(
                    recommendation.rank
                ),

                recommendation.patient_id,

                str(
                    recommendation.esi_level
                ),

                recommendation.criticality,

                    (
                    f"{recommendation.confidence_pct:.1f}%"
                ),

                recommendation.operational_layer,

                recommendation.resource_dispatch,

                (
                    "YES â€” CLINICIAN APPROVAL"
                    if recommendation.transfer_candidate
                    else "NO"
                ),
            ]

            for column, value in enumerate(
                values
            ):

                table.setItem(
                    row_index,
                    column,
                    QTableWidgetItem(
                        value
                    ),
                )

        transfer_count = sum(
            recommendation.transfer_candidate
            for recommendation
            in batch_result.recommendations
        )

        self.window.batchSummary.setText(
            (
                f"Patients processed: "
                f"{len(batch_result.patients)} | "
                f"History: "
                f"{batch_result.history_with} | "
                f"No history: "
                f"{batch_result.history_without} | "
                f"Surge ratio: "
                f"{batch_result.surge_ratio:.2f}Ã— | "
                f"ER full: "
                f"{'YES' if batch_result.rooms_full else 'NO'} | "
                f"OT full: "
                f"{'YES' if batch_result.ots_full else 'NO'} | "
                f"Transfer candidates: "
                f"{transfer_count}"
            )
        )

    # ========================================================
    # BUILD PATIENT FROM FORM
    # ========================================================

    
    def build_patient_from_form(
        self,
    ) -> PatientRecord:

        history_available = (
            self.window.historyMode.currentIndex()
            == 0
        )

        # --------------------------------------------------------
        # Image findings are now treated as INPUT EVIDENCE.
        #
        # They do not independently assign ESI.
        # --------------------------------------------------------

        image_findings = (
            self.window.imageFindings
            .toPlainText()
            .strip()
        )

        clinical_narrative = (
            self.window.narrative
            .toPlainText()
            .strip()
        )

        if image_findings:

            clinical_narrative += (
                "\n\n"
                "[CLINICIAN-REVIEWED IMAGE FINDINGS]\n"
                + image_findings
            )

        return PatientRecord(

            patient_id=(
                self.window.patientId
                .text()
                .strip()
                or "MANUAL-001"
            ),

            age_years=float(
                self.window.age.value()
            ),

            sex=(
                self.window.sex
                .currentText()
            ),

            chief_complaint=(
                self.window.complaint
                .toPlainText()
                .strip()
            ),

            narrative=clinical_narrative,

            history_known=(
                history_available
            ),

            files_available=(
                history_available
            ),

            vitals={
                "hr":
                    self.window.hr.value(),

                "rr":
                    self.window.rr.value(),

                "sbp":
                    self.window.sbp.value(),

                "dbp":
                    self.window.dbp.value(),

                "spo2":
                    self.window.spo2.value(),
            },

            image_tags=[],
        )


    def on_evaluate(
        self,
    ) -> None:
        """
        Evaluate one patient from the single-patient panel.
        """

        try:

            # ------------------------------------------------
            # Build PatientRecord
            # ------------------------------------------------

            patient = self.build_patient_from_form()

            self.current_patient = patient

            # ------------------------------------------------
            # Runtime infrastructure permission check
            # ------------------------------------------------

            permission_state = getattr(
                self.engine,
                "system_permissions",
                {},
            )

            required_permissions = {
                "BED_MANAGEMENT_SYSTEM",
                "STAFF_ROSTER_DB",
                "INSTRUMENT_INVENTORY",
            }

            authorized = required_permissions.issubset(
                {
                    key
                    for key, value in permission_state.items()
                    if value
                }
            )

            if not authorized:

                QMessageBox.warning(
                    self.window,
                    "System Access Required",
                    (
                        "Authorize hospital infrastructure "
                        "access before evaluating the patient."
                    ),
                )

                return

            # ------------------------------------------------
            # Optional manual image findings
            # ------------------------------------------------

            image_text = (
                self.window.imageFindings
                .toPlainText()
                .strip()
            )

            if image_text:

                findings = [
                    line.strip()
                    for line
                    in image_text.splitlines()
                    if line.strip()
                ]

                if findings:

                    try:

                        self.engine.process_manual_clinician_entry(
                            patient,
                            "IMAGING_METADATA",
                            {
                                "findings": findings
                            },
                        )

                    except AttributeError:
                        # Older backend compatibility.
                        pass

            # ------------------------------------------------
            # Clinical evaluation
            # ------------------------------------------------

            patient = (
                self.apply_ambulance_data_for_triage(
                    patient
                )
            )

            recommendation = self.engine.evaluate(
                patient,
                self.assets,
                self.staff,
            )

            self.current_recommendation = recommendation

            self.current_display_result = (
                build_clinical_display_result(
                    patient,
                    recommendation,
                    self.assets,
                    self.staff,
                    patient_name=(
                        self.window.patientName.text().strip()
                        if hasattr(
                            self.window,
                            "patientName",
                        )
                        else ""
                    ),
                    image_findings=(
                        self.window.imageFindings
                        .toPlainText()
                        .strip()
                    ),
                    image_review_required=(
                        bool(
                            self.window.imageFindings
                            .toPlainText()
                            .strip()
                        )
                    ),
                )
            )

            self.render_display_result(
                self.current_display_result
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Triage Evaluation Error",
                str(exc),
            )


    # ========================================================
    # IMAGE UPLOAD
    # ========================================================


    def on_upload_image(
        self,
    ) -> None:

        path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Upload Clinical / Trauma Image",
            "",
            (
                "Medical / Image Files "
                "(*.png *.jpg *.jpeg *.bmp *.webp);;"
                "All Files (*)"
            ),
        )

        if not path:
            return

        # --------------------------------------------------------
        # Preview
        # --------------------------------------------------------

        pixmap = QPixmap(path)

        if pixmap.isNull():

            QMessageBox.warning(
                self.window,
                "Image Error",
                "The selected image could not be loaded.",
            )

            return

        self.last_image_path = path

        self.window.imagePreview.setPixmap(
            pixmap.scaled(
                420,
                300,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

        # --------------------------------------------------------
        # Local image parsing
        # --------------------------------------------------------

        try:

            metadata = (
                self.image_parser.parse(
                    path
                )
            )

            self.last_image_metadata = (
                metadata
            )

            self.window.imageStatus.setText(
                (
                    "Image received ✓ | "
                    f"{metadata['format']} | "
                    f"{metadata['width']}×"
                    f"{metadata['height']} | "
                    f"{metadata['size_kb']} KB"
                )
            )

        except Exception as exc:

            QMessageBox.warning(
                self.window,
                "Image Parser Error",
                str(exc),
            )

            return

        # --------------------------------------------------------
        # AI analysis
        #
        # This produces FINDINGS only.
        # It does NOT assign ESI.
        # --------------------------------------------------------

        if self.vision_service is None:

            self.window.imageFindings.setPlainText(
                (
                    "AI image analysis is not configured.\n\n"
                    "The image has been uploaded successfully, "
                    "but no AI findings were generated.\n\n"
                    "Configure GEMINI_API_KEY to enable "
                    "multimodal image analysis."
                )
            )

            return

        try:

            result = (
                self.image_parser.analyze(
                    path
                )
            )

            self.last_image_analysis = (
                result
            )

            formatted_findings = (
                self.image_parser
                .format_findings(
                    result
                )
            )

            # ----------------------------------------------------
            # IMPORTANT:
            # Findings go ONLY into the image findings box.
            # No ESI calculation happens here.
            # ----------------------------------------------------

            self.window.imageFindings.setPlainText(
                formatted_findings
            )

            self.window.imageStatus.setText(
                (
                    "AI image findings generated ✓ | "
                    f"Model: {result.model_name} | "
                    "Clinician confirmation required"
                )
            )

        except Exception as exc:

            self.window.imageFindings.setPlainText(
                (
                    "Image uploaded successfully, "
                    "but AI visual analysis failed.\n\n"
                    f"Reason: {exc}\n\n"
                    "Clinician may enter findings manually."
                )
            )

            self.window.imageStatus.setText(
                "AI image analysis unavailable"
            )

    # ========================================================
    # EVALUATE
    # ========================================================

    
    def render_recommendation(
        self,
        rec,
    ):
        display_result = (
            self.current_display_result
        )
         
        level = rec.esi_level

        # ----------------------------------------------------
        # Main severity
        # ----------------------------------------------------

        self.window.criticalityLabel.setText(
            f"CRITICALITY: "
            f"{ESI_LABELS[level]}"
        )

        self.window.resultLabel.setText(
            f"ASSIGNED ESI LEVEL: {level}"
        )

        # ----------------------------------------------------
        # Severity explanation
        # ----------------------------------------------------

        self.window.severityGuide.setText(
            ESI_DESCRIPTIONS[level]
        )

        # ----------------------------------------------------
        # Visual severity hierarchy
        # ----------------------------------------------------

        severity_styles = {

            1:
                (
                    "background:#8B0000;"
                    "color:white;"
                    "font-weight:bold;"
                    "padding:10px;"
                ),

            2:
                (
                    "background:#D35400;"
                    "color:white;"
                    "font-weight:bold;"
                    "padding:10px;"
                ),

            3:
                (
                    "background:#E6A700;"
                    "color:white;"
                    "font-weight:bold;"
                    "padding:10px;"
                ),

            4:
                (
                    "background:#2E8B57;"
                    "color:white;"
                    "font-weight:bold;"
                    "padding:10px;"
                ),

            5:
                (
                    "background:#2F6DA1;"
                    "color:white;"
                    "font-weight:bold;"
                    "padding:10px;"
                ),
        }

        self.window.resultLabel.setStyleSheet(
            severity_styles[level]
        )

        self.window.criticalityLabel.setStyleSheet(
            severity_styles[level]
        )

        # ----------------------------------------------------
        # Operational layer
        # ----------------------------------------------------

        self.window.layerLabel.setText(
            f"ACTIVE OPERATIONAL LAYER: "
            f"{rec.operational_layer}"
        )

        # ----------------------------------------------------
        # Confidence / uncertainty
        # ----------------------------------------------------

        self.window.confidenceLabel.setText(
            (
                f"SYSTEM CONFIDENCE: "
                f"{rec.confidence_pct:.1f}% | "
                f"UNCERTAINTY: "
                f"{rec.uncertainty_indicator:.3f}"
            )
        )

        # ----------------------------------------------------
        # Clinical indices
        # ----------------------------------------------------

        si = (
            "â€”"
            if rec.risk_assessment.shock_index
            is None
            else
            f"{rec.risk_assessment.shock_index:.2f}"
        )

        pp = (
            "â€”"
            if rec.risk_assessment.pulse_pressure
            is None
            else
            (
                f"{rec.risk_assessment.pulse_pressure:.0f}"
                " mmHg"
            )
        )

        completeness = (
            f"{rec.risk_assessment.data_completeness * 100:.0f}%"
        )

        self.window.indicesLabel.setText(
            (
                f"SI: {si} | "
                f"Pulse Pressure: {pp} | "
                f"Data Completeness: {completeness}"
            )
        )

        # ----------------------------------------------------
        # Three-bullet rationale
        # ----------------------------------------------------

        rationale = "\n".join(
            f"â€¢ {line}"
            for line in rec.rationale
        )

        self.window.rationale.setPlainText(
            rationale
        )

        # ----------------------------------------------------
        # Dispatch
        # ----------------------------------------------------

        self.window.dispatchLabel.setText(
            (
                "RESOURCE DISPATCH / ROUTING:\n"
                f"{rec.routing_recommendation}"
            )
        )

        # ----------------------------------------------------
        # Audit status
        # ----------------------------------------------------

        if rec.clinician_override:

            self.window.auditLabel.setText(
                "AUDIT: CLINICIAN OVERRIDE RECORDED âœ“"
            )

        else:

            self.window.auditLabel.setText(
                (
                    "AUDIT: AI RECOMMENDATION "
                    "RECORDED â€¢ CLINICIAN REVIEW REQUIRED"
                )
            )

    # ========================================================
    # MANUAL CLINICIAN OVERRIDE
    # ========================================================

    def render_display_result(
        self,
        result,
    ) -> None:
        """
        Render the canonical ClinicalDisplayResult.

        This is the same object later written to the
        UI-equivalent report.
        """

        # --------------------------------------------------------
        # ESI
        # --------------------------------------------------------

        if result.esi_level is not None:

            self.window.resultLabel.setText(
                f"ASSIGNED ESI LEVEL: "
                f"{result.esi_level}"
            )

            self.window.criticalityLabel.setText(
                (
                    "CRITICALITY: "
                    f"{result.criticality}"
                )
            )

        # --------------------------------------------------------
        # Confidence
        # --------------------------------------------------------

        confidence = (
            "—"
            if result.system_confidence_pct is None
            else f"{result.system_confidence_pct:.1f}%"
        )

        uncertainty = (
            "—"
            if result.uncertainty_indicator is None
            else f"{result.uncertainty_indicator:.3f}"
        )

        self.window.confidenceLabel.setText(
            (
                f"SYSTEM CONFIDENCE: {confidence} | "
                f"UNCERTAINTY: {uncertainty}"
            )
        )

        # --------------------------------------------------------
        # Operational layer
        # --------------------------------------------------------

        self.window.layerLabel.setText(
            (
                "ACTIVE OPERATIONAL LAYER: "
                f"{result.active_layer}"
            )
        )

        # --------------------------------------------------------
        # Clinical indices
        # --------------------------------------------------------

        shock_index = (
            "—"
            if result.shock_index is None
            else f"{result.shock_index:.2f}"
        )

        pulse_pressure = (
            "—"
            if result.pulse_pressure is None
            else f"{result.pulse_pressure:.0f} mmHg"
        )

        sipa = (
            "—"
            if result.sipa is None
            else f"{result.sipa:.2f}"
        )

        self.window.indicesLabel.setText(
            (
                f"SI: {shock_index} | "
                f"SIPA: {sipa} | "
                f"Pulse Pressure: {pulse_pressure}"
            )
        )

        # --------------------------------------------------------
        # Rationale
        # --------------------------------------------------------

        self.window.rationale.setPlainText(
            "\n".join(
                f"• {item}"
                for item in result.rationale
            )
        )

        # --------------------------------------------------------
        # Resource dispatch
        # --------------------------------------------------------

        self.window.dispatchLabel.setText(
            (
                "RESOURCE DISPATCH / ROUTING:\n"
                f"{result.resource_dispatch}\n\n"
                f"{result.routing_recommendation}"
            )
        )

        # --------------------------------------------------------
        # Image findings
        # --------------------------------------------------------

        if result.image_findings:

            self.window.imageFindings.setPlainText(
                result.image_findings
            )

        # --------------------------------------------------------
        # Audit
        # --------------------------------------------------------

        if result.clinician_override:

            self.window.auditLabel.setText(
                "AUDIT: CLINICIAN OVERRIDE RECORDED ✓"
            )

        else:

            self.window.auditLabel.setText(
                (
                    "AUDIT: AI RECOMMENDATION RECORDED "
                    "• CLINICIAN REVIEW REQUIRED"
                )
            )
    
    def on_override(self):

        if (
            self.current_recommendation
            is None
            or self.current_patient
            is None
        ):

            QMessageBox.information(
                self.window,
                "Manual Override",
                (
                    "Evaluate a patient before "
                    "performing a clinician override."
                ),
            )

            return

        dialog = QDialog(
            self.window
        )

        dialog.setWindowTitle(
            "Clinician Manual Override"
        )

        dialog.resize(
            500,
            220,
        )

        form = QFormLayout(
            dialog
        )

        # ----------------------------------------------------
        # ESI dropdown
        # ----------------------------------------------------

        esi_combo = QComboBox()

        for level, text in ESI_LABELS.items():

            esi_combo.addItem(
                text,
                level,
            )

        esi_combo.setCurrentIndex(
            self.current_recommendation.esi_level
            - 1
        )

        # ----------------------------------------------------
        # Structured reason
        # ----------------------------------------------------

        reason_combo = QComboBox()

        reason_combo.addItems(
            [
                "CLINICAL_EXAM_OVERRIDES_AI",
                "NEW_VITAL_SIGN_CHANGE",
                "NEW_IMAGING_FINDING",
                "NEW_HISTORY_INFORMATION",
                "PATIENT_DETERIORATION",
                "AI_DATA_QUALITY_CONCERN",
                "OTHER_CLINICAL_REASON",
            ]
        )

        # ----------------------------------------------------
        # Clinician ID
        # ----------------------------------------------------

        clinician_id = QLineEdit()

        clinician_id.setPlaceholderText(
            "Enter clinician ID"
        )

        # ----------------------------------------------------
        # Justification
        # ----------------------------------------------------

        narrative = QLineEdit()

        narrative.setPlaceholderText(
            "Mandatory clinical justification"
        )

        form.addRow(
            "New severity:",
            esi_combo,
        )

        form.addRow(
            "Clinician ID:",
            clinician_id,
        )

        form.addRow(
            "Structured reason:",
            reason_combo,
        )

        form.addRow(
            "Justification:",
            narrative,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
        )

        form.addRow(
            buttons
        )

        buttons.accepted.connect(
            dialog.accept
        )

        buttons.rejected.connect(
            dialog.reject
        )

        if (
            dialog.exec()
            != QDialog.Accepted
        ):
            return

        if not clinician_id.text().strip():

            QMessageBox.warning(
                self.window,
                "Override rejected",
                "Clinician ID is mandatory.",
            )

            return

        if (
            len(
                narrative.text().strip()
            )
            < 12
        ):

            QMessageBox.warning(
                self.window,
                "Override rejected",
                (
                    "Provide a meaningful clinical "
                    "justification of at least 12 characters."
                ),
            )

            return

        try:

            updated = (
                self.engine.clinician_override(
                    self.current_patient,
                    self.current_recommendation,
                    clinician_id=(
                        clinician_id.text()
                        .strip()
                    ),
                    new_esi=int(
                        esi_combo.currentData()
                    ),
                    justification_code=(
                        reason_combo.currentText()
                    ),
                    free_text=(
                        narrative.text()
                        .strip()
                    ),
                )
            )

            self.current_recommendation = (
                updated
            )

            self.render_recommendation(
                updated
            )

            self.window.auditLabel.setText(
                (
                    "AUDIT: CLINICIAN OVERRIDE "
                    "RECORDED WITH STRUCTURED REASON âœ“"
                )
            )

        except Exception as exc:

            QMessageBox.critical(
                self.window,
                "Override Error",
                str(exc),
            )

    # ========================================================
    # CLEAR FORM
    # ========================================================

    def on_clear(self):

        self.current_patient = None
        self.current_ambulance_record = None
        self.current_recommendation = None
        self.last_image_path = None
        self.last_image_metadata = None

        self.window.patientId.clear()
        self.window.complaint.clear()
        self.window.narrative.clear()

        self.window.imageFindings.clear()

        self.window.imagePreview.clear()

        self.window.imagePreview.setText(
            "No image loaded"
        )

        self.window.imageStatus.setText(
            "Image parser: waiting"
        )

        self.reset_result_panel()

    # ========================================================
    # RESET RESULT PANEL
    # ========================================================

    def reset_result_panel(self):

        self.window.criticalityLabel.setText(
            "CRITICALITY: Awaiting evaluation"
        )

        self.window.criticalityLabel.setStyleSheet(
            ""
        )

        self.window.resultLabel.setText(
            "ASSIGNED ESI LEVEL: â€”"
        )

        self.window.resultLabel.setStyleSheet(
            ""
        )

        self.window.severityGuide.setText(
            (
                "The five-level severity system will "
                "appear after triage evaluation."
            )
        )

        self.window.layerLabel.setText(
            "ACTIVE OPERATIONAL LAYER: â€”"
        )

        self.window.confidenceLabel.setText(
            "SYSTEM CONFIDENCE: â€”"
        )

        self.window.indicesLabel.setText(
            "SI: â€” | Pulse Pressure: â€” | "
            "Data Completeness: â€”"
        )

        self.window.rationale.clear()

        self.window.dispatchLabel.setText(
            "RESOURCE DISPATCH / ROUTING: â€”"
        )

        self.window.auditLabel.setText(
            "AUDIT: Awaiting evaluation"
        )

    def load_ambulance_data(self) -> None:
        patient_key = (
            self.window.ambulancePatientLookup
            .text()
            .strip()
        )

        if not patient_key:
            QMessageBox.warning(
                self.window,
                "Ambulance Data",
                "Enter a patient name or patient ID first.",
            )
            return

        try:
            # Current gateway lookup is by patient ID.
            # We will add name lookup immediately after
            # this basic end-to-end path is verified.
            data = (
                self.ambulance_gateway_client
                .get_patient_telemetry(
                    patient_key
                )
            )

            self.latest_ambulance_data = data

            self.window.ambulanceHRValue.setText(
                str(data.get("hr", "—"))
            )

            self.window.ambulanceRRValue.setText(
                str(data.get("rr", "—"))
            )

            self.window.ambulanceSBPValue.setText(
                str(data.get("sbp", "—"))
            )

            self.window.ambulanceDBPValue.setText(
                str(data.get("dbp", "—"))
            )

            self.window.ambulanceSpO2Value.setText(
                str(data.get("spo2", "—"))
            )

            self.window.ambulanceSourceValue.setText(
                (
                    f"{data.get('source_ambulance', 'Unknown')}"
                    f" | ETA: "
                    f"{data.get('eta_minutes', '—')} min"
                )
            )

            self.window.ambulanceStatus.setText(
                (
                    "Ambulance pre-arrival telemetry "
                    "loaded ✓"
                )
            )

        except Exception as exc:
            self.window.ambulanceStatus.setText(
                "No ambulance pre-arrival data loaded"
            )

            QMessageBox.warning(
                self.window,
                "Ambulance Data",
                (
                    "Could not retrieve ambulance telemetry.\n\n"
                    f"{exc}"
                ),
            )

    def update_profile_dependent_features(
        self,
    ) -> None:

        profile = (
            self.window.profileCombo
            .currentText()
            .strip()
            .lower()
        )

        is_multispecialty = (
            "multispecialty" in profile
            or "tertiary" in profile
        )

        if is_multispecialty:

            self.window.ambulanceGroup.setEnabled(
                True
            )

            self.window.ambulancePatientLookup.setEnabled(
                True
            )

            self.window.ambulanceLookupButton.setEnabled(
                True
            )

            self.window.useAmbulanceForTriageCheckBox.setEnabled(
                True
            )

            # Combo enabled/disabled based ONLY on checkbox.
            self.window.ambulanceTriageModeCombo.setEnabled(
                self.window
                .useAmbulanceForTriageCheckBox
                .isChecked()
            )

        else:

            self.window.ambulanceGroup.setEnabled(
                False
            )

            self.window.useAmbulanceForTriageCheckBox.setChecked(
                False
            )

            self.window.useAmbulanceForTriageCheckBox.setEnabled(
                False
            )

            self.window.ambulanceTriageModeCombo.setCurrentIndex(
                0
            )

            self.window.ambulanceTriageModeCombo.setEnabled(
                False
            )

            self.latest_ambulance_data = None

            self.window.ambulanceStatus.setText(
                "Ambulance integration unavailable "
                "in Rural Primary Health Centre mode."
            )

        self.update_triage_input_state()
    
    def on_ambulance_triage_toggle(
        self,
        enabled: bool,
    ) -> None:

        profile = (
            self.window.profileCombo
            .currentText()
            .strip()
            .lower()
        )

        is_multispecialty = (
            "multispecialty" in profile
            or "tertiary" in profile
        )

        # Rural mode must never enable ambulance triage.
        if not is_multispecialty:

            self.window.useAmbulanceForTriageCheckBox.setChecked(
                False
            )

            self.window.ambulanceTriageModeCombo.setEnabled(
                False
            )

            self.update_triage_input_state()
            return

        # Multispecialty mode:
        self.window.ambulanceTriageModeCombo.setEnabled(
            enabled
        )

        if enabled:
            self.window.ambulanceStatus.setText(
                "Ambulance telemetry enabled for triage."
            )
        else:
            self.window.ambulanceStatus.setText(
                "Ambulance telemetry loaded — "
                "not included in triage."
            )

        self.update_triage_input_state()

    def on_ambulance_triage_mode_changed(
        self,
        index: int,
    ) -> None:

        mode = (
            self.window
            .ambulanceTriageModeCombo
            .itemData(index)
        )

        if mode == "ignore":

            self.window.ambulanceStatus.setText(
                "Ambulance data will be ignored by triage."
            )

        elif mode == "ambulance_only":

            self.window.ambulanceStatus.setText(
                "PROVISIONAL PRE-ARRIVAL TRIAGE — "
                "ambulance data only."
            )

        elif mode == "combined":

            self.window.ambulanceStatus.setText(
                "Ambulance + hospital data will be "
                "combined for final evaluation."
            )

        self.update_triage_input_state()

    def apply_ambulance_data_for_triage(
        self,
        patient,
    ):
        """
        Applies ambulance telemetry according to the
        clinician-selected mode.

        Modes:

            ignore
                Ambulance telemetry is not used.

            ambulance_only
                Ambulance data becomes the provisional
                patient vital source.

            combined
                Existing hospital values take precedence;
                ambulance values fill only missing fields.
        """

        if self.latest_ambulance_data is None:
            return patient

        mode = (
            self.window.ambulanceTriageModeCombo
            .currentData()
        )

        enabled = (
            self.window
            .useAmbulanceForTriageCheckBox
            .isChecked()
        )

        if not enabled:
            return patient

        ambulance = (
            self.latest_ambulance_data
        )

        # --------------------------------------------------------
        # Ambulance-only provisional triage
        # --------------------------------------------------------

        if mode == "ambulance_only":

            patient.vitals["hr"] = (
                ambulance.get("hr")
            )

            patient.vitals["rr"] = (
                ambulance.get("rr")
            )

            patient.vitals["sbp"] = (
                ambulance.get("sbp")
            )

            patient.vitals["dbp"] = (
                ambulance.get("dbp")
            )

            patient.vitals["spo2"] = (
                ambulance.get("spo2")
            )

            return patient

        # --------------------------------------------------------
        # Combined mode
        # --------------------------------------------------------

        if mode == "combined":

            existing = dict(
                patient.vitals or {}
            )

            for key in (
                "hr",
                "rr",
                "sbp",
                "dbp",
                "spo2",
            ):

                hospital_value = (
                    existing.get(key)
                )

                ambulance_value = (
                    ambulance.get(key)
                )

                # Hospital measurement wins because it is
                # the newer in-hospital measurement.
                if (
                    hospital_value is None
                    and ambulance_value is not None
                ):

                    existing[key] = (
                        ambulance_value
                    )

            patient.vitals = existing

        # --------------------------------------------------------
        # ignore / unknown
        # --------------------------------------------------------

        return patient

    def update_triage_input_state(
        self,
    ) -> None:

        combo = self.window.ambulanceTriageModeCombo

        ambulance_enabled = (
            self.window
            .useAmbulanceForTriageCheckBox
            .isChecked()
        )

        mode = combo.currentData()

        is_ambulance_only = (
            ambulance_enabled
            and mode == "ambulance_only"
        )

        # --------------------------------------------------------
        # Enable/disable the mode dropdown
        # --------------------------------------------------------

        combo.setEnabled(
            ambulance_enabled
        )

        # --------------------------------------------------------
        # Manual hospital controls
        # --------------------------------------------------------

        hospital_controls = [
            self.window.age,
            self.window.sex,
            self.window.historyMode,
            self.window.complaint,
            self.window.narrative,
            self.window.hr,
            self.window.rr,
            self.window.sbp,
            self.window.dbp,
            self.window.spo2,
            self.window.uploadImageButton,
        ]

        for widget in hospital_controls:
            widget.setEnabled(
                not is_ambulance_only
            )

        # Patient identity always remains editable.
        self.window.patientName.setEnabled(True)
        self.window.patientId.setEnabled(True)

        # --------------------------------------------------------
        # Evaluation button
        # --------------------------------------------------------

        if is_ambulance_only:

            self.window.evaluateButton.setEnabled(True)

            self.window.evaluateButton.setText(
                "Run Provisional Pre-Arrival Triage"
            )

        else:

            self.window.evaluateButton.setEnabled(True)

            self.window.evaluateButton.setText(
                "Evaluate Patient"
            )

    def setup_ambulance_triage_controls(self) -> None:
        combo = self.window.ambulanceTriageModeCombo

        # Prevent duplicate items if this is called more than once.
        combo.blockSignals(True)
        combo.clear()

        combo.addItem(
            "Ignore ambulance data",
            "ignore",
        )

        combo.addItem(
            "Ambulance-only provisional triage",
            "ambulance_only",
        )

        combo.addItem(
            "Combine ambulance + hospital data",
            "combined",
        )

        combo.setCurrentIndex(0)
        combo.setEnabled(False)

        combo.blockSignals(False)

        # Connect ONCE.
        self.window.useAmbulanceForTriageCheckBox.toggled.connect(
            self.on_ambulance_triage_toggle
        )

        combo.currentIndexChanged.connect(
            self.on_ambulance_triage_mode_changed
        )

        combo.currentIndexChanged.connect(
            self.update_triage_input_state
        )

        self.window.useAmbulanceForTriageCheckBox.toggled.connect(
            self.update_triage_input_state
        )

    def open_test_case_lab(self) -> None:

        if (
            self.test_case_window_controller is None
            or self.test_case_window_controller.window
            is None
        ):

            self.test_case_window_controller = (
                TestCaseWindowController(
                    parent=self.window,
                    engine=self.engine,
                    batch_service=self.batch_service,
                    assets=self.assets,
                    staff=self.staff,
                )
            )

        self.test_case_window_controller.window.show()
        self.test_case_window_controller.window.raise_()
        self.test_case_window_controller.window.activateWindow()