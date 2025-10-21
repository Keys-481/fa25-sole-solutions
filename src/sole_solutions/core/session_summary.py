from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Sequence, Optional
import math
import re


@dataclass
class SessionSummary:
    frames: int
    sensors: int
    avg_pressure_per_frame: List[float]
    estimated_vgrf_per_frame: List[float]  # sum of sensor values per frame
    global_min: float
    global_max: float
    contact_time_frames: int
    contact_threshold: float
    pti: float  # pressure–time integral using avg_pressure * dt
    dt: float


def _safe_float(x) -> Optional[float]:
    try:
        v = float(x)
        if not math.isfinite(v):
            return None
        return v
    except Exception:
        return None


# columns to avoid when inferring sensors
KNOWN_META = {
    "frame",
    "subject",
    "trial",
    "insole",
    "foot",
    "side",
    "peak",
    "avg",
    "average",
    "contact",
    "area",
    "time",
    "threshold",
}

SENSOR_NAME_PAT = re.compile(r"^(sensor(_|\s)?\d+|s\d+|\d+)$", re.IGNORECASE)


def infer_sensor_keys(
    data_storage: List[Dict[str, object]],
    min_numeric_ratio: float = 0.9,
    sample_rows: int = 200,
) -> List[str]:
    """Infer which columns are sensels/sensors."""
    if not data_storage:
        return []
    cols = list(data_storage[0].keys())
    n = min(len(data_storage), sample_rows)

    def is_meta(name: str) -> bool:
        low = name.lower()
        if low in KNOWN_META:
            return True
        # obvious non-sensor descriptors
        return any(k in low for k in ("units", "left", "right", "median", "mean"))

    candidates: List[str] = []

    # try by name first
    for c in cols:
        if is_meta(c):
            continue
        if SENSOR_NAME_PAT.match(c.replace(" ", "_")):
            candidates.append(c)

    # fallback: numeric columns test
    if not candidates:
        for c in cols:
            if is_meta(c):
                continue
            numeric_hits = 0
            checks = 0
            for i in range(n):
                v = data_storage[i].get(c, None)
                if v is None or v == "":
                    continue
                checks += 1
                if _safe_float(v) is not None:
                    numeric_hits += 1
            if checks > 0 and numeric_hits / checks >= min_numeric_ratio:
                candidates.append(c)

    # keep stable ordering as they appear in the file
    ordered = [c for c in cols if c in set(candidates)]
    return ordered


def compute_session_summary(
    data_storage: List[Dict[str, object]],
    sensor_keys: Sequence[str],
    contact_threshold: float = 20.0,
    dt: float = 1.0,
) -> SessionSummary:
    """Lightweight summary independent of the main calc module."""
    if not data_storage or not sensor_keys:
        return SessionSummary(
            frames=0,
            sensors=0,
            avg_pressure_per_frame=[],
            estimated_vgrf_per_frame=[],
            global_min=0.0,
            global_max=0.0,
            contact_time_frames=0,
            contact_threshold=contact_threshold,
            pti=0.0,
            dt=dt,
        )

    frames = len(data_storage)
    sensors = len(sensor_keys)

    avg_pf: List[float] = []
    vgrf_pf: List[float] = []
    gmin = float("inf")
    gmax = float("-inf")
    contact_frames = 0
    pti_accum = 0.0

    for row in data_storage:
        vals: List[float] = []
        for k in sensor_keys:
            v = _safe_float(row.get(k))
            if v is not None:
                vals.append(v)

        if vals:
            fsum = sum(vals)
            favg = fsum / len(vals)
        else:
            fsum = 0.0
            favg = 0.0

        avg_pf.append(favg)
        vgrf_pf.append(fsum)
        pti_accum += favg * dt

        if any(v >= contact_threshold for v in vals):
            contact_frames += 1

        for v in vals:
            if v < gmin:
                gmin = v
            if v > gmax:
                gmax = v

    if gmin == float("inf"):
        gmin = 0.0
        gmax = 0.0

    return SessionSummary(
        frames=frames,
        sensors=sensors,
        avg_pressure_per_frame=avg_pf,
        estimated_vgrf_per_frame=vgrf_pf,
        global_min=gmin,
        global_max=gmax,
        contact_time_frames=contact_frames,
        contact_threshold=contact_threshold,
        pti=pti_accum,
        dt=dt,
    )
