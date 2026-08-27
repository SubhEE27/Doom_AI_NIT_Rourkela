from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header

from .database import AmbulanceDatabase
from .schemas import AmbulanceTelemetry


APP_TITLE = "DOOM AI Ambulance Data Gateway"
DB_PATH = Path(
    os.getenv(
        "DOOM_AI_AMBULANCE_DB",
        "ambulance_gateway/ambulance.db",
    )
)

# Optional prototype shared secret. Leave unset for localhost-only demo.
GATEWAY_TOKEN = os.getenv("DOOM_AI_AMBULANCE_TOKEN")

app = FastAPI(
    title=APP_TITLE,
    version="1.0.0",
)

database = AmbulanceDatabase(DB_PATH)


def _check_token(authorization: str | None) -> None:
    """Optional Bearer-token check for a safer prototype deployment."""
    if not GATEWAY_TOKEN:
        return

    expected = f"Bearer {GATEWAY_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=401,
            detail="Invalid ambulance gateway authorization.",
        )


@app.get("/")
def health_check() -> dict:
    return {
        "system": APP_TITLE,
        "status": "online",
        "time_utc": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/ambulance/telemetry")
def receive_telemetry(
    telemetry: AmbulanceTelemetry,
    authorization: str | None = Header(default=None),
) -> dict:
    _check_token(authorization)

    payload = telemetry.normalized()
    received_at = datetime.now(timezone.utc).isoformat()

    database.upsert(
        payload,
        received_at,
    )

    return {
        "status": "received",
        "patient_id": payload["patient_id"],
        "received_at_utc": received_at,
    }


@app.get("/ambulance/patient/{patient_id}")
def get_patient_telemetry(
    patient_id: str,
    authorization: str | None = Header(default=None),
) -> dict:
    _check_token(authorization)

    telemetry = database.get(patient_id)

    if telemetry is None:
        raise HTTPException(
            status_code=404,
            detail=f"No ambulance telemetry found for {patient_id}.",
        )

    return telemetry
