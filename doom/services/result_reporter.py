from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from doom.services.presentation_result import (
    ClinicalDisplayResult,
)


class ResultReporter:
    """
    Writes the exact ClinicalDisplayResult objects used by
    the UI into human-readable and machine-readable reports.
    """

    def __init__(
        self,
        output_directory: str | Path = "reports",
    ) -> None:

        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    # ========================================================
    # JSON
    # ========================================================

    def write_json(
        self,
        results: Iterable[
            ClinicalDisplayResult
        ],
        filename: str = "ui_results.json",
    ) -> Path:

        result_list = [
            result.to_dict()
            for result in results
        ]

        path = (
            self.output_directory
            / filename
        )

        path.write_text(
            json.dumps(
                result_list,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        return path

    # ========================================================
    # CSV
    # ========================================================

    def write_csv(
        self,
        results: Iterable[
            ClinicalDisplayResult
        ],
        filename: str = "ui_results.csv",
    ) -> Path:

        result_list = list(
            results
        )

        path = (
            self.output_directory
            / filename
        )

        if not result_list:
            path.write_text(
                "",
                encoding="utf-8",
            )
            return path

        rows = [
            result.to_dict()
            for result in result_list
        ]

        fields = list(
            rows[0].keys()
        )

        with path.open(
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fields,
            )

            writer.writeheader()

            for row in rows:
                writer.writerow(
                    row
                )

        return path

    # ========================================================
    # HTML
    # ========================================================

    def write_html(
        self,
        results: Iterable[
            ClinicalDisplayResult
        ],
        filename: str = "ui_results.html",
    ) -> Path:

        result_list = list(
            results
        )

        path = (
            self.output_directory
            / filename
        )

        sections = []

        for result in result_list:

            rationale = "".join(
                f"<li>{item}</li>"
                for item
                in result.rationale
            )

            image_findings = (
                result.image_findings
                .replace(
                    "\n",
                    "<br>",
                )
            )

            transfer_text = (
                "YES"
                if result.transfer_candidate
                else "NO"
            )

            sections.append(
                f"""
                <section class="patient">
                    <h2>
                        Patient {result.patient_id}
                    </h2>

                    <div class="summary">
                        <strong>
                            ESI {result.esi_level}
                        </strong>
                        <span>
                            {result.criticality}
                        </span>
                    </div>

                    <h3>Patient Information</h3>

                    <table>
                        <tr>
                            <td>Patient ID</td>
                            <td>{result.patient_id}</td>
                        </tr>

                        <tr>
                            <td>Patient Name</td>
                            <td>{result.patient_name}</td>
                        </tr>

                        <tr>
                            <td>Age</td>
                            <td>{result.age_years}</td>
                        </tr>

                        <tr>
                            <td>Sex</td>
                            <td>{result.sex}</td>
                        </tr>

                        <tr>
                            <td>History Available</td>
                            <td>{result.history_available}</td>
                        </tr>

                        <tr>
                            <td>Chief Complaint</td>
                            <td>{result.chief_complaint}</td>
                        </tr>
                    </table>

                    <h3>Vital Signs</h3>

                    <table>
                        <tr>
                            <td>HR</td>
                            <td>{result.heart_rate}</td>
                            <td>RR</td>
                            <td>{result.respiratory_rate}</td>
                        </tr>

                        <tr>
                            <td>SBP</td>
                            <td>{result.systolic_bp}</td>
                            <td>DBP</td>
                            <td>{result.diastolic_bp}</td>
                        </tr>

                        <tr>
                            <td>SpO₂</td>
                            <td>{result.spo2}</td>
                            <td>Shock Index</td>
                            <td>{result.shock_index}</td>
                        </tr>

                        <tr>
                            <td>Pulse Pressure</td>
                            <td>{result.pulse_pressure}</td>
                            <td>SIPA</td>
                            <td>{result.sipa}</td>
                        </tr>
                    </table>

                    <h3>Image Findings</h3>

                    <div class="findings">
                        {image_findings or "No image findings."}
                    </div>

                    <h3>AI Triage Result</h3>

                    <table>
                        <tr>
                            <td>ESI</td>
                            <td>{result.esi_level}</td>
                        </tr>

                        <tr>
                            <td>Criticality</td>
                            <td>{result.criticality}</td>
                        </tr>

                        <tr>
                            <td>Confidence</td>
                            <td>
                                {result.system_confidence_pct}%
                            </td>
                        </tr>

                        <tr>
                            <td>Uncertainty</td>
                            <td>
                                {result.uncertainty_indicator}
                            </td>
                        </tr>

                        <tr>
                            <td>Active Layer</td>
                            <td>{result.active_layer}</td>
                        </tr>

                        <tr>
                            <td>Urgency Score</td>
                            <td>{result.urgency_score}</td>
                        </tr>
                    </table>

                    <h3>Rationale</h3>

                    <ul>
                        {rationale}
                    </ul>

                    <h3>Resource Dispatch</h3>

                    <table>
                        <tr>
                            <td>Dispatch</td>
                            <td>{result.resource_dispatch}</td>
                        </tr>

                        <tr>
                            <td>Routing</td>
                            <td>{result.routing_recommendation}</td>
                        </tr>

                        <tr>
                            <td>Transfer Candidate</td>
                            <td>{transfer_text}</td>
                        </tr>

                        <tr>
                            <td>Transfer Destination</td>
                            <td>{result.transfer_destination}</td>
                        </tr>

                        <tr>
                            <td>Specialist</td>
                            <td>{result.specialist_route}</td>
                        </tr>
                    </table>

                    <h3>Environment</h3>

                    <table>
                        <tr>
                            <td>Hospital</td>
                            <td>{result.hospital_profile}</td>
                        </tr>

                        <tr>
                            <td>Shift</td>
                            <td>{result.shift}</td>
                        </tr>

                        <tr>
                            <td>ER</td>
                            <td>
                                {result.emergency_rooms_available}
                                /
                                {result.emergency_rooms_total}
                            </td>
                        </tr>

                        <tr>
                            <td>OT</td>
                            <td>
                                {result.operating_theatres_available}
                                /
                                {result.operating_theatres_total}
                            </td>
                        </tr>
                    </table>
                </section>
                """
            )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>

            <meta charset="utf-8">

            <title>
                DOOM AI — UI Result Report
            </title>

            <style>

                body {{
                    font-family:
                        Arial,
                        sans-serif;

                    background:
                        #f2f4f7;

                    margin: 30px;
                }}

                h1 {{
                    color:
                        #1f2937;
                }}

                .patient {{
                    background:
                        white;

                    padding:
                        24px;

                    margin-bottom:
                        24px;

                    border-radius:
                        10px;
                }}

                .summary {{
                    padding:
                        12px;

                    margin-bottom:
                        16px;

                    background:
                        #eef2ff;
                }}

                table {{
                    width:
                        100%;

                    border-collapse:
                        collapse;

                    margin-bottom:
                        16px;
                }}

                td {{
                    border:
                        1px solid #d1d5db;

                    padding:
                        8px;
                }}

                td:first-child {{
                    font-weight:
                        bold;

                    width:
                        25%;
                }}

                .findings {{
                    white-space:
                        normal;

                    background:
                        #f9fafb;

                    padding:
                        12px;
                }}

            </style>

        </head>

        <body>

            <h1>
                DOOM AI — Clinical UI Result Report
            </h1>

            <p>
                This report reproduces the canonical result
                objects used by the Doom AI application UI.
            </p>

            {''.join(sections)}

        </body>
        </html>
        """

        path.write_text(
            html,
            encoding="utf-8",
        )

        return path