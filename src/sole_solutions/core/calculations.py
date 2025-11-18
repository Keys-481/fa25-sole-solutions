# sole_solutions/core/calculations.py
from __future__ import annotations
from typing import Dict, List, Tuple, TypedDict, Optional
import math
import statistics

# ---- Types ----
class CalcParams(TypedDict):
    fs: float                # Hz (sampling frequency)
    sensel_area_cm2: float   # area of one sensel in cm^2
    contact_kpa: float       # threshold for contact in kPa
    stance_bw_frac: float    # e.g., 0.05 (5% bodyweight)
    body_mass_kg: float
    calibration_scale: float # scale vGRF to match BW if desired
    smooth_win: int          # moving average window (frames)

def _movavg(xs: List[float], w: int) -> List[float]:
    if w <= 1 or not xs:
        return xs[:]
    out, s = [], 0.0
    q = []
    for v in xs:
        q.append(v) 
        s += v
        if len(q) > w:
            s -= q.pop(0)
        out.append(s / len(q))
    return out

def _safe_float(x) -> Optional[float]:
    try:
        v = float(x)
        if math.isfinite(v):
            return v
    except Exception:
        pass
    return None

def extract_per_frame_pressures(
    rows: List[dict],
    sensor_keys: List[str],
) -> List[List[float]]:
    """
    Returns pressures_kpa[frame][sensor_idx].
    Missing/invalid values -> 0.0
    """
    frames: List[List[float]] = []
    if not rows or not sensor_keys:
        return frames
    for r in rows:
        row_vals = []
        for k in sensor_keys:
            v = _safe_float(r.get(k))
            row_vals.append(v if v is not None else 0.0)
        frames.append(row_vals)
    return frames

def compute_contact_area_series(
    pressures_kpa: List[List[float]],
    params: CalcParams
) -> List[float]:
    area = params["sensel_area_cm2"]
    thr = params["contact_kpa"]
    out: List[float] = []
    for frame in pressures_kpa:
        n_contact = sum(1 for p in frame if p >= thr)
        out.append(n_contact * area)
    return out

def compute_avg_pressure_series(
    pressures_kpa: List[List[float]],
    params: CalcParams
) -> List[float]:
    out: List[float] = []
    thr = params["contact_kpa"]
    for frame in pressures_kpa:
        active = [p for p in frame if p >= thr]
        out.append(sum(active)/len(active) if active else 0.0)
    return out

def compute_vgrf_series(
    pressures_kpa: List[List[float]],
    params: CalcParams
) -> List[float]:
    """
    vGRF per frame:
      1 kPa = 0.1 N/cm^2
      vGRF = sum_i (kPa_i * 0.1 * sensel_area_cm2) * calibration_scale
    """
    kpa_to_N_per_cm2 = 0.1
    a = params["sensel_area_cm2"]
    s = params["calibration_scale"]
    out: List[float] = []
    for frame in pressures_kpa:
        F = (sum(frame) * kpa_to_N_per_cm2 * a) * s
        out.append(F)
    return out

def compute_pti_kpas(
    pressures_kpa: List[List[float]],
    params: CalcParams
) -> float:
    """Pressure–Time Integral over the whole stance (kPa·s)."""
    if not pressures_kpa:
        return 0.0
    dt = 1.0 / max(1e-9, params["fs"])
    # Sum of average contact pressure per frame * dt
    avg = compute_avg_pressure_series(pressures_kpa, params)
    return sum(avg) * dt

def compute_cop_path(
    pressures_kpa: List[List[float]],
    sensel_xy_cm: List[Tuple[float, float]]
) -> List[Tuple[float, float]]:
    """
    CoP per frame (x,y) using pressure-weighted centroid.
    If total pressure == 0, returns (nan, nan).
    """
    xy = sensel_xy_cm
    out: List[Tuple[float, float]] = []
    for frame in pressures_kpa:
        tot = sum(frame)
        if tot <= 0:
            out.append((float("nan"), float("nan")))
            continue
        sx = 0.0 
        sy = 0.0
        for p, (x, y) in zip(frame, xy):
            sx += p * x
            sy += p * y
        out.append((sx / tot, sy / tot))
    return out

def detect_stance_windows(
    vgrf_N: List[float],
    params: CalcParams
) -> List[Tuple[int, int]]:
    """
    Returns list of (start_idx, end_idx) for stance windows where vGRF exceeds
    BW * stance_bw_frac. BW = mass * 9.81.
    """
    bw = params["body_mass_kg"] * 9.81
    thr = params["stance_bw_frac"] * bw
    on = False
    start = 0
    spans: List[Tuple[int, int]] = []
    for i, F in enumerate(vgrf_N):
        if not on and F >= thr:
            on = True 
            start = i
        elif on and F < thr:
            on = False
            spans.append((start, i))
    if on:
        spans.append((start, len(vgrf_N)-1))
    return spans

def temporal_spatial_from_spans(
    spans: List[Tuple[int,int]],
    params: CalcParams
) -> Dict[str, float]:
    """
    Basic temporal-spatial: stance time mean, cadence, step/stride time estimates.
    """
    fs = params["fs"]
    if not spans:
        return {
            "stance_time_s": 0.0,
            "swing_time_s": 0.0,
            "step_time_s": 0.0,
            "stride_time_s": 0.0,
            "cadence_spm": 0.0
        }
    stance_times = [(b-a+1)/fs for (a,b) in spans]
    stance_mean = statistics.mean(stance_times)
    # crude step time ~ distance between consecutive onsets
    onsets = [a for (a,_) in spans]
    inter = []
    for i in range(1, len(onsets)):
        inter.append( (onsets[i]-onsets[i-1]) / fs )
    step_time = statistics.mean(inter) if inter else stance_mean
    stride_time = (inter[0]*2.0) if inter else (stance_mean*2.0)
    cadence_spm = 60.0 / step_time if step_time > 0 else 0.0
    # swing ~ stride - stance (single-leg estimate)
    swing_time = max(0.0, stride_time - stance_mean)
    return {
        "stance_time_s": stance_mean,
        "swing_time_s": swing_time,
        "step_time_s": step_time,
        "stride_time_s": stride_time,
        "cadence_spm": cadence_spm
    }

def compute_impulse_Ns(vgrf_N: List[float], params: CalcParams) -> float:
    dt = 1.0 / max(1e-9, params["fs"])
    return sum(vgrf_N) * dt

def compute_load_rate(vgrf_N: List[float], params: CalcParams) -> Dict[str, float]:
    """
    Instantaneous max slope (N/s) and avg slope up to 80% of peak.
    """
    fs = params["fs"]
    if len(vgrf_N) < 3:
        return {"max_dFdt_Ns": 0.0, "avg_up_to_80pct_Ns": 0.0}
    d = []
    for i in range(1, len(vgrf_N)):
        d.append( (vgrf_N[i]-vgrf_N[i-1]) * fs )
    max_slope = max(d) if d else 0.0
    peak = max(vgrf_N) if vgrf_N else 0.0
    target = 0.8 * peak
    idx_t = 0
    for i, F in enumerate(vgrf_N):
        if F >= target:
            idx_t = i
            break
    avg = (vgrf_N[idx_t] - vgrf_N[0]) * fs / max(1, idx_t) if idx_t > 0 else 0.0
    return {"max_dFdt_Ns": max_slope, "avg_up_to_80pct_Ns": avg}

def symmetry_index(a: float, b: float) -> float:
    """SI% = 100 * (R - L) / (0.5*(R + L)); caller passes (L, R) or vice-versa."""
    denom = 0.5 * (a + b)
    return 0.0 if denom == 0 else 100.0 * (b - a) / denom

def compute_per_frame_bundle(
    pressures_kpa: List[List[float]],
    sensel_xy_cm: List[Tuple[float,float]],
    params: CalcParams
) -> Dict[str, List[float] | List[Tuple[float,float]]]:
    vgrf = compute_vgrf_series(pressures_kpa, params)
    vgrf = _movavg(vgrf, params["smooth_win"])
    contact_area = compute_contact_area_series(pressures_kpa, params)
    avg_p = compute_avg_pressure_series(pressures_kpa, params)
    cop = compute_cop_path(pressures_kpa, sensel_xy_cm)
    return {
        "vgrf_N": vgrf,
        "contact_area_cm2": contact_area,
        "avg_pressure_kPa": avg_p,
        "cop_xy_cm": cop
    }
