from __future__ import annotations

import csv
import importlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from doom.services.engine import DoomTriageEngine
from doom.services.presentation_result import (
    build_clinical_display_result,
)
from doom.services.result_reporter import (
    ResultReporter,
)

from .common import CaseResult


TEST_MODULES = [
    "test_01_profiles",
    "test_02_history_mix",
    "test_03_dynamic_arrivals_scale",
    "test_04_priority_reshuffle",
    "test_05_capacity_transfer",
    "test_06_layers",
    "test_07_demographic",
    "test_08_safety_floor",
    "test_09_ambulance",
    "test_10_image_pipeline",
    "test_11_override_audit",
    "test_12_permissions",
    "test_13_fhir",
    "test_14_unseen_stress",
    "test_15_mass_casualty",
    "test_16_ui_contract",
]


# ============================================================
# CENTRAL CAPTURE STORE
# ============================================================

_CAPTURED_EVALUATIONS: list[dict[str, Any]] = []


# ============================================================
# ENGINE EVALUATION CAPTURE
# ============================================================

def install_evaluation_capture() -> None:
    """
    Monkey-patch DoomTriageEngine.evaluate so the existing
    test-case files do not need to be modified.

    Every call made by the test suite is captured.

    The actual clinical recommendation is still produced by
    the real DoomTriageEngine.evaluate() method.
    """

    global _CAPTURED_EVALUATIONS

    original_evaluate = (
        DoomTriageEngine.evaluate
    )

    # Prevent double patching.
    if getattr(
        original_evaluate,
        "_doom_test_capture",
        False,
    ):
        return

    def captured_evaluate(
        self,
        patient,
        assets,
        staff,
        *args,
        **kwargs,
    ):
        recommendation = original_evaluate(
            self,
            patient,
            assets,
            staff,
            *args,
            **kwargs,
        )

        _CAPTURED_EVALUATIONS.append(
            {
                "patient": patient,
                "recommendation": recommendation,
                "assets": assets,
                "staff": staff,
            }
        )

        return recommendation

    captured_evaluate._doom_test_capture = True

    DoomTriageEngine.evaluate = (
        captured_evaluate
    )


# ============================================================
# CASE NAME
# ============================================================

def readable_case_name(
    module_name: str,
) -> str:
    """
    Convert:

        test_05_capacity_transfer

    into:

        Test 05 Capacity Transfer
    """

    return (
        module_name
        .replace(
            "_",
            " ",
        )
        .title()
    )


# ============================================================
# EXISTING VALIDATION REPORT
# ============================================================

def write_csv(
    path: Path,
    results: list[CaseResult],
) -> None:

    with path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=[
                "case_id",
                "scenario",
                "status",
                "detail",
                "expected",
            ],
        )

        writer.writeheader()

        for result in results:

            writer.writerow(
                asdict(result)
            )


def write_html(
    path: Path,
    summary: dict[str, Any],
) -> None:

    rows = []

    for result in summary["results"]:

        css_class = (
            result["status"]
            .lower()
        )

        rows.append(
            (
                f"<tr class='{css_class}'>"
                f"<td>{result['case_id']}</td>"
                f"<td>{result['scenario']}</td>"
                f"<td><b>{result['status']}</b></td>"
                f"<td>{result['detail']}</td>"
                f"<td>{result['expected']}</td>"
                f"</tr>"
            )
        )

    html = f"""
<!doctype html>
<html>
<head>

<meta charset="utf-8">

<title>
DOOM AI — Validation Summary
</title>

<style>

body {{
    font-family: Arial, sans-serif;
    margin: 30px;
}}

table {{
    border-collapse: collapse;
    width: 100%;
}}

th,
td {{
    border: 1px solid #bbb;
    padding: 8px;
    text-align: left;
}}

th {{
    background: #222;
    color: white;
}}

.pass {{
    background: #e9f7e9;
}}

.fail {{
    background: #fde9e9;
}}

.skip {{
    background: #fff7d6;
}}

.summary {{
    font-size: 18px;
    margin-bottom: 20px;
}}

</style>

</head>

<body>

<h1>
DOOM AI — Validation Summary
</h1>

<div class="summary">

PASS:
{summary['passed']}

&nbsp;&nbsp;

FAIL:
{summary['failed']}

&nbsp;&nbsp;

SKIP:
{summary['skipped']}

&nbsp;&nbsp;

TOTAL:
{summary['total_cases']}

<br>

Run:
{summary['timestamp_utc']}

</div>

<table>

<tr>
<th>ID</th>
<th>Scenario</th>
<th>Status</th>
<th>Observed</th>
<th>Expected</th>
</tr>

{''.join(rows)}

</table>

</body>
</html>
"""

    path.write_text(
        html,
        encoding="utf-8",
    )


# ============================================================
# MAIN TEST RUNNER
# ============================================================

def main() -> int:

    global _CAPTURED_EVALUATIONS

    # --------------------------------------------------------
    # Reset capture store
    # --------------------------------------------------------

    _CAPTURED_EVALUATIONS = []

    # --------------------------------------------------------
    # Install capture BEFORE importing/running test modules
    # --------------------------------------------------------

    install_evaluation_capture()

    # --------------------------------------------------------
    # Existing PASS / FAIL / SKIP results
    # --------------------------------------------------------

    all_results: list[CaseResult] = []

    # --------------------------------------------------------
    # New canonical UI-equivalent results
    # --------------------------------------------------------

    display_results = []

    print()
    print("=" * 110)
    print("DOOM AI — TEST CASE VALIDATION SUITE")
    print("=" * 110)

    # ========================================================
    # RUN EACH TEST CASE
    # ========================================================

    for module_name in TEST_MODULES:

        print(
            f"\nRunning: {module_name}"
        )

        # ----------------------------------------------------
        # Import test module
        # ----------------------------------------------------

        try:

            module = importlib.import_module(
                f"test_cases.{module_name}"
            )

        except Exception as exc:

            case_result = CaseResult(
                case_id=(
                    module_name
                    .replace(
                        "test_",
                        "H",
                    )
                    .replace(
                        "_",
                        "",
                    )
                ),
                scenario=readable_case_name(
                    module_name
                ),
                status="FAIL",
                detail=(
                    "Unable to import test module: "
                    f"{exc}"
                ),
                expected=(
                    "Test module imports successfully"
                ),
            )

            all_results.append(
                case_result
            )

            print(
                f"[FAIL] {module_name}"
            )

            continue

        # ----------------------------------------------------
        # Capture count BEFORE this test case
        # ----------------------------------------------------

        before_count = len(
            _CAPTURED_EVALUATIONS
        )

        # ----------------------------------------------------
        # Existing test execution
        #
        # IMPORTANT:
        # This is the SAME module.run() that your current
        # runner already uses.
        # ----------------------------------------------------

        try:

            module_results = module.run()

            if module_results:
                all_results.extend(
                    module_results
                )

        except Exception as exc:

            case_result = CaseResult(
                case_id=(
                    module_name
                    .replace(
                        "test_",
                        "H",
                    )
                    .replace(
                        "_",
                        "",
                    )
                ),
                scenario=readable_case_name(
                    module_name
                ),
                status="FAIL",
                detail=(
                    f"Unhandled test exception: "
                    f"{type(exc).__name__}: {exc}"
                ),
                expected=(
                    "Scenario executes without unhandled exception"
                ),
            )

            all_results.append(
                case_result
            )

            print(
                f"[FAIL] {module_name}"
            )

        # ----------------------------------------------------
        # Capture evaluations belonging ONLY to this module
        # ----------------------------------------------------

        after_count = len(
            _CAPTURED_EVALUATIONS
        )

        new_evaluations = (
            _CAPTURED_EVALUATIONS[
                before_count:after_count
            ]
        )

        # ====================================================
        # BUILD UI-EQUIVALENT RESULTS
        # ====================================================

        for captured in new_evaluations:

            patient = captured.get(
                "patient"
            )

            recommendation = captured.get(
                "recommendation"
            )

            assets = captured.get(
                "assets"
            )

            staff = captured.get(
                "staff"
            )

            if (
                patient is None
                or recommendation is None
            ):
                continue

            try:

                display_result = (
                    build_clinical_display_result(

                        patient,

                        recommendation,

                        assets,

                        staff,

                        test_case_id=(
                            module_name
                        ),

                        test_case_name=(
                            readable_case_name(
                                module_name
                            )
                        ),
                    )
                )

                display_results.append(
                    display_result
                )

            except Exception as exc:

                print(
                    "\n[WARNING] Could not build "
                    "UI-equivalent result for "
                    f"{patient.patient_id}: "
                    f"{exc}"
                )

    # ========================================================
    # TIMESTAMP / REPORT DIRECTORY
    # ========================================================

    now = (
        datetime
        .now(timezone.utc)
        .isoformat()
    )

    root = (
        Path(__file__)
        .resolve()
        .parents[1]
    )

    reports = (
        root
        / "reports"
    )

    reports.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # EXISTING VALIDATION SUMMARY
    # ========================================================

    summary = {

        "timestamp_utc":
            now,

        "total_cases":
            len(all_results),

        "passed":
            sum(
                result.status == "PASS"
                for result
                in all_results
            ),

        "failed":
            sum(
                result.status == "FAIL"
                for result
                in all_results
            ),

        "skipped":
            sum(
                result.status == "SKIP"
                for result
                in all_results
            ),

        "results":
            [
                asdict(result)
                for result
                in all_results
            ],
    }

    # ========================================================
    # EXISTING REPORTS
    # ========================================================

    (
        reports
        / "hackathon_latest.json"
    ).write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    write_csv(
        reports
        / "hackathon_latest.csv",
        all_results,
    )

    write_html(
        reports
        / "hackathon_latest.html",
        summary,
    )

    # ========================================================
    # NEW UI-EQUIVALENT REPORTS
    # ========================================================

    try:

        reporter = ResultReporter(
            output_directory=reports
        )

        reporter.write_json(
            display_results,
            "ui_results.json",
        )

        reporter.write_csv(
            display_results,
            "ui_results.csv",
        )

        reporter.write_html(
            display_results,
            "ui_results.html",
        )

    except Exception as exc:

        print()
        print(
            "[WARNING] UI-equivalent report generation "
            f"failed: {exc}"
        )

    # ========================================================
    # TERMINAL SUMMARY
    # ========================================================

    print()
    print(
        "=" * 110
    )

    print(
        "DOOM AI — TEST CASE VALIDATION RESULTS"
    )

    print(
        "=" * 110
    )

    for result in all_results:

        print(
            f"[{result.status:<4}] "
            f"{result.case_id} | "
            f"{result.scenario}"
        )

        print(
            f"       {result.detail}"
        )

    print(
        "-" * 110
    )

    print(
        f"PASS={summary['passed']} | "
        f"FAIL={summary['failed']} | "
        f"SKIP={summary['skipped']} | "
        f"TOTAL={summary['total_cases']}"
    )

    print(
        f"Clinical UI-equivalent results captured: "
        f"{len(display_results)}"
    )

    print(
        f"Reports: {reports}"
    )

    print(
        "UI-equivalent report:"
    )

    print(
        reports
        / "ui_results.html"
    )

    print(
        "=" * 110
    )

    # --------------------------------------------------------
    # Maintain original behavior:
    #
    # non-zero exit code if any validation case failed.
    # --------------------------------------------------------

    return (
        1
        if summary["failed"]
        else 0
    )


if __name__ == "__main__":

    raise SystemExit(
        main()
    )