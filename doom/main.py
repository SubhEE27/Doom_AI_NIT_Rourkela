from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from doom.config.settings import DeploymentProfile
from doom.services.engine import DoomTriageEngine
from doom.services.demo import base_assets, base_staff
from doom.ui.main_window import MainWindowController


def main() -> int:

    # --------------------------------------------------------
    # Qt application
    # --------------------------------------------------------

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "DOOM AI"
    )

    app.setOrganizationName(
        "DOOM AI Health Systems"
    )

    # --------------------------------------------------------
    # Project root
    # --------------------------------------------------------

    root = Path(
        __file__
    ).resolve().parent

    # --------------------------------------------------------
    # Core OOP triage engine
    # --------------------------------------------------------

    engine = DoomTriageEngine()

    # --------------------------------------------------------
    # Default deployment profile
    #
    # The clinician can change this from the UI.
    # --------------------------------------------------------

    engine.deployment_profile = (
        DeploymentProfile
        .MULTISPECIALTY_TERTIARY_CENTER
        .value
    )

    # --------------------------------------------------------
    # Hospital environment
    # --------------------------------------------------------

    assets = base_assets()

    # Explicit 500-patient/day deployment assumption.
    # This does NOT restrict the actual arrival stream.
    # It represents the hospital-scale configuration.
    assets.daily_ed_visits = 500

    # --------------------------------------------------------
    # Default day-shift staffing
    #
    # The UI allows switching to night shift.
    # --------------------------------------------------------

    staff = base_staff(
        shift="day"
    )

    # --------------------------------------------------------
    # UI controller
    # --------------------------------------------------------

    controller = MainWindowController(

        engine=engine,

        assets=assets,

        staff=staff,

        ui_path=str(
            root
            / "ui"
            / "app.ui"
        ),
    )

    controller.window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
