from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class AmbulanceTelemetry(BaseModel):
    """Payload sent by an ambulance to the gateway."""

    model_config = ConfigDict(extra="forbid")

    patient_id: str = Field(min_length=1, max_length=128)
    patient_name: Optional[str] = Field(default=None, max_length=200)

    hr: Optional[float] = Field(default=None, ge=0, le=300)
    rr: Optional[float] = Field(default=None, ge=0, le=150)
    sbp: Optional[float] = Field(default=None, ge=0, le=300)
    dbp: Optional[float] = Field(default=None, ge=0, le=250)
    spo2: Optional[float] = Field(default=None, ge=0, le=100)

    eta_minutes: Optional[float] = Field(default=None, ge=0, le=1440)
    notes: Optional[str] = Field(default=None, max_length=2000)
    source_ambulance: str = Field(default="SIMULATED-AMBULANCE", max_length=128)
    timestamp_utc: Optional[str] = None

    def normalized(self) -> dict:
        data = self.model_dump()
        if not data.get("timestamp_utc"):
            data["timestamp_utc"] = datetime.now(timezone.utc).isoformat()
        return data
