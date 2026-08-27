from __future__ import annotations

import importlib
import os
import random
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Callable


@dataclass
class CaseResult:
    case_id: str
    scenario: str
    status: str  # PASS / FAIL / SKIP
    detail: str
    expected: str = ""


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def find_project_root() -> Path:
    """Find the real application project root above this suite."""
    candidates = [
        project_root().parent,
        Path.cwd(),
    ]
    for root in candidates:
        for pkg in ("doom_ai", "doom", "safeguard"):
            if (root / pkg).is_dir():
                return root
    return Path.cwd()


def ensure_sys_path() -> Path:
    root = find_project_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def import_first(*module_names: str):
    last = None
    for name in module_names:
        try:
            return importlib.import_module(name)
        except ImportError as exc:
            last = exc
    raise ImportError(f"Could not import any of: {module_names}") from last


def load_modules():
    ensure_sys_path()
    prefixes = ["doom_ai", "doom", "safeguard"]
    package = None
    for prefix in prefixes:
        try:
            importlib.import_module(prefix)
            package = prefix
            break
        except ImportError:
            continue
    if package is None:
        raise ImportError("No supported Doom AI package found (doom_ai/doom/safeguard).")

    models = importlib.import_module(f"{package}.models.domain")
    engine_mod = importlib.import_module(f"{package}.services.engine")
    demo_mod = importlib.import_module(f"{package}.services.demo")
    root = find_project_root()

    def optional_import(module_name: str, file_path: Path):
        if not file_path.exists():
            return None
        try:
            return importlib.import_module(module_name)
        except ImportError:
            return None

    batch_mod = optional_import(
        f"{package}.services.batch_triage",
        root / package / "services" / "batch_triage.py",
    )
    hospital_mod = optional_import(
        f"{package}.services.hospital_resources",
        root / package / "services" / "hospital_resources.py",
    )
    ambulance_mod = optional_import(
        f"{package}.services.ambulance_feed",
        root / package / "services" / "ambulance_feed.py",
    )
    image_mod = optional_import(
        f"{package}.services.image_parser",
        root / package / "services" / "image_parser.py",
    )
    priority_mod = optional_import(
        f"{package}.services.priority_queue",
        root / package / "services" / "priority_queue.py",
    )
    fhir_mod = optional_import(
        f"{package}.api.fhir",
        root / package / "api" / "fhir.py",
    )
    return {
        "package": package,
        "models": models,
        "engine": engine_mod,
        "demo": demo_mod,
        "batch": batch_mod,
        "hospital": hospital_mod,
        "ambulance": ambulance_mod,
        "image": image_mod,
        "priority": priority_mod,
        "fhir": fhir_mod,
    }


def make_patient(mods, pid: str, age: float, sex: str, complaint: str, narrative: str = "", **kwargs):
    return mods["models"].PatientRecord(
        patient_id=pid,
        age_years=age,
        sex=sex,
        chief_complaint=complaint,
        narrative=narrative,
        **kwargs,
    )


def make_assets(mods, **kwargs):
    """Create HospitalAssets while supporting older/newer helper signatures."""
    HospitalAssets = mods["models"].HospitalAssets
    base_assets = mods["demo"].base_assets

    # Friendly aliases used by the harness.
    aliases = {
        "bed_occupancy_pct": "occupancy",
        "ot_occupancy_pct": "ot_occupancy",
        "current_ed_volume": "volume",
        "ed_wait_minutes": "ed_wait",
    }

    try:
        return base_assets(**kwargs)
    except TypeError:
        converted = dict(kwargs)
        for new, old in aliases.items():
            if new in converted and old not in converted:
                converted[old] = converted.pop(new)
        # Some older helpers do not accept imaging/bandwidth/5G or capacity fields.
        try:
            return base_assets(**converted)
        except TypeError:
            pass

    # Final compatibility path: construct the domain object directly.
    bed_occ = float(kwargs.get("bed_occupancy_pct", kwargs.get("occupancy", 82.0)))
    ot_occ = float(kwargs.get("ot_occupancy_pct", kwargs.get("ot_occupancy", 75.0)))
    volume = int(kwargs.get("current_ed_volume", kwargs.get("volume", 100)))
    normal = int(kwargs.get("normal_ed_volume", kwargs.get("normal_volume", 100)))
    daily = int(kwargs.get("daily_ed_visits", 100))
    wait = float(kwargs.get("ed_wait_minutes", kwargs.get("ed_wait", 35.0)))
    imaging = bool(kwargs.get("imaging", True))
    bandwidth = bool(kwargs.get("bandwidth", True))
    fiveg = bool(kwargs.get("fiveg", True))
    er_total = int(kwargs.get("emergency_rooms_total", 3))
    er_avail = int(kwargs.get("emergency_rooms_available", max(0, round(er_total * (1-bed_occ/100)))))
    ot_total = int(kwargs.get("operating_theatres_total", 3))
    ot_avail = int(kwargs.get("operating_theatres_available", max(0, round(ot_total * (1-ot_occ/100)))))
    return HospitalAssets(
        hospital_id="TEST-HOSPITAL",
        high_speed_bandwidth=bandwidth,
        five_g_telemetry=fiveg,
        pocus_online=imaging,
        imaging_pipeline_online=imaging,
        bed_occupancy_pct=bed_occ,
        ot_occupancy_pct=ot_occ,
        ed_wait_minutes=wait,
        local_bed_capacity=er_total,
        current_ed_volume=volume,
        normal_ed_volume=normal,
        network_latency_ms=20.0,
        daily_ed_visits=daily,
        nearby_facilities=[
            {
                "name": "Nearby Hospital 3.5km",
                "distance_km": 3.5,
                "available_beds": 10,
                "travel_minutes": 15,
                "dispatch_minutes": 5,
                "receiving_wait_minutes": 5,
            }
        ],
        emergency_rooms_total=er_total,
        emergency_rooms_available=er_avail,
        operating_theatres_total=ot_total,
        operating_theatres_available=ot_avail,
    )


def make_staff(mods, **kwargs):
    base_staff = mods["demo"].base_staff
    try:
        return base_staff(**kwargs)
    except TypeError:
        if "shift_name" in kwargs and "shift" not in kwargs:
            kwargs["shift"] = kwargs.pop("shift_name")
        return base_staff(**kwargs)


def new_engine(mods, profile: str | None = None):
    cls = getattr(mods["engine"], "DoomAITriageEngine", None) or getattr(mods["engine"], "DoomTriageEngine")
    return cls(profile) if profile is not None else cls()


def authorize(engine):
    tokens = [
        "BED_MANAGEMENT_SYSTEM",
        "STAFF_ROSTER_DB",
        "INSTRUMENT_INVENTORY",
    ]
    engine.request_system_access_permissions(tokens)


def set_if(obj, name, value):
    if hasattr(obj, name):
        setattr(obj, name, value)


def expect(condition: bool, detail: str, expected: str = ""):
    if condition:
        return CaseResult("", "", "PASS", detail, expected)
    return CaseResult("", "", "FAIL", detail, expected)


def run_case(case_id: str, scenario: str, fn: Callable[[], tuple[bool, str]], expected: str = "") -> CaseResult:
    try:
        ok, detail = fn()
        return CaseResult(case_id, scenario, "PASS" if ok else "FAIL", detail, expected)
    except Exception as exc:
        return CaseResult(case_id, scenario, "FAIL", f"{type(exc).__name__}: {exc}", expected)


def skip_case(case_id: str, scenario: str, detail: str):
    return CaseResult(case_id, scenario, "SKIP", detail, "")


def is_api_configured() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def random_patient(mods, pid: str, rng: random.Random):
    age = rng.choice([
        rng.uniform(0.05, 0.9),
        rng.randint(1, 12),
        rng.randint(13, 64),
        rng.randint(65, 95),
    ])
    complaint_choices = [
        "chest pain", "shortness of breath", "abdominal pain",
        "fever", "vomiting", "fall", "sore throat", "ankle sprain",
        "confusion", "headache", "trauma", "back pain", "nausea",
    ]
    complaint = rng.choice(complaint_choices)
    history = rng.random() < 0.5
    hr = rng.randint(55, 165)
    rr = rng.randint(8, 38)
    sbp = rng.randint(75, 180)
    dbp = rng.randint(40, 105)
    spo2 = rng.randint(84, 100)
    return make_patient(
        mods,
        pid,
        float(age),
        rng.choice(["M", "F", "U"]),
        complaint,
        narrative=f"Synthetic unseen scenario: {complaint}.",
        history_known=history,
        files_available=history,
        vitals={"hr": hr, "rr": rr, "sbp": sbp, "dbp": dbp, "spo2": spo2},
    )


