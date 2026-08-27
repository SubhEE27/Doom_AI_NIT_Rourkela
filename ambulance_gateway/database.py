from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional


class AmbulanceDatabase:
    """Small SQLite-backed telemetry store for the prototype gateway."""

    def __init__(self, db_path: str | Path = "ambulance_gateway/ambulance.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ambulance_telemetry (
                    patient_id TEXT PRIMARY KEY,
                    patient_name TEXT,
                    payload_json TEXT NOT NULL,
                    received_at_utc TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def upsert(self, payload: dict, received_at_utc: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO ambulance_telemetry (
                    patient_id,
                    patient_name,
                    payload_json,
                    received_at_utc
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(patient_id) DO UPDATE SET
                    patient_name = excluded.patient_name,
                    payload_json = excluded.payload_json,
                    received_at_utc = excluded.received_at_utc
                """,
                (
                    payload["patient_id"],
                    payload.get("patient_name"),
                    json.dumps(payload, ensure_ascii=False),
                    received_at_utc,
                ),
            )
            connection.commit()

    def get(self, patient_id: str) -> Optional[dict]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM ambulance_telemetry WHERE patient_id = ?",
                (patient_id,),
            ).fetchone()

        if row is None:
            return None

        return json.loads(row["payload_json"])
