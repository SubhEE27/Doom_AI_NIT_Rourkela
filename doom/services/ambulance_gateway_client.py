from __future__ import annotations

import os
from typing import Any

import requests


class AmbulanceGatewayClient:
    """Client used by Doom AI UI/service code to retrieve pre-arrival telemetry."""

    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv(
                "DOOM_AI_AMBULANCE_GATEWAY_URL",
                "http://127.0.0.1:8000",
            )
        ).rstrip("/")
        self.token = token or os.getenv("DOOM_AI_AMBULANCE_TOKEN")
        self.timeout_seconds = timeout_seconds

    def _headers(self) -> dict[str, str]:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def get_patient_telemetry(
        self,
        patient_id: str,
    ) -> dict[str, Any]:
        if not patient_id.strip():
            raise ValueError("Patient ID/name cannot be empty.")

        response = requests.get(
            f"{self.base_url}/ambulance/patient/{patient_id.strip()}",
            headers=self._headers(),
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, dict):
            raise RuntimeError("Ambulance gateway returned invalid data.")

        return payload

    def health_check(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/",
                headers=self._headers(),
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False
