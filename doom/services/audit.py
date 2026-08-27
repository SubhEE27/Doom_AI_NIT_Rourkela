from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Dict, List

@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    timestamp_utc: str
    patient_id: str
    actor_type: str
    action: str
    payload: Dict[str, Any]
    previous_hash: str
    event_hash: str

class AuditLog:
    def __init__(self, system_id="DOOM AI"):
        self.system_id = system_id; self._events: List[AuditEvent] = []; self._last_hash = "GENESIS"
    @property
    def events(self): return tuple(self._events)
    def append(self, patient_id, actor_type, action, payload):
        import uuid
        event_id = str(uuid.uuid4()); timestamp = datetime.now(timezone.utc).isoformat()
        canonical = json.dumps({"system_id":self.system_id,"event_id":event_id,"timestamp_utc":timestamp,"patient_id":patient_id,"actor_type":actor_type,"action":action,"payload":payload,"previous_hash":self._last_hash}, sort_keys=True, separators=(",",":"))
        event_hash = sha256(canonical.encode()).hexdigest()
        event = AuditEvent(event_id,timestamp,patient_id,actor_type,action,payload,self._last_hash,event_hash)
        self._events.append(event); self._last_hash=event_hash; return event
    def verify_chain(self):
        previous="GENESIS"
        for event in self._events:
            canonical=json.dumps({"system_id":self.system_id,"event_id":event.event_id,"timestamp_utc":event.timestamp_utc,"patient_id":event.patient_id,"actor_type":event.actor_type,"action":event.action,"payload":event.payload,"previous_hash":previous}, sort_keys=True, separators=(",",":"))
            if event.previous_hash != previous or event.event_hash != sha256(canonical.encode()).hexdigest(): return False
            previous=event.event_hash
        return True

