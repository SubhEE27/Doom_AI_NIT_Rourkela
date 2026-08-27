from __future__ import annotations

import argparse
import json
import os

import requests


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Send simulated ambulance telemetry to DOOM AI gateway."
    )
    parser.add_argument("--patient-id", default="AMB-1001")
    parser.add_argument("--patient-name", default="Demo Patient")
    parser.add_argument("--base-url", default=os.getenv("DOOM_AI_AMBULANCE_GATEWAY_URL", "http://127.0.0.1:8000"))
    args = parser.parse_args()

    payload = {
        "patient_id": args.patient_id,
        "patient_name": args.patient_name,
        "hr": 128,
        "rr": 31,
        "sbp": 88,
        "dbp": 54,
        "spo2": 90,
        "eta_minutes": 7,
        "notes": "Road traffic accident, chest trauma",
        "source_ambulance": "AMB-07",
    }

    response = requests.post(
        f"{args.base_url.rstrip('/')}/ambulance/telemetry",
        json=payload,
        timeout=5,
    )
    response.raise_for_status()

    print(json.dumps(response.json(), indent=2))
    print("Telemetry uploaded successfully.")


if __name__ == "__main__":
    main()
