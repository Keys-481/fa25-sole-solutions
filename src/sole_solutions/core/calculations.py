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
    calibration_scale: float  # scale vGRF to match BW if desired
    smooth_win: int          # moving average window (frames)


class SegmentMetrics(TypedDict, total=False):
    """Per-segment summary for an arbitrary frame range."""
    name: str
    start_frame: int
    end_frame: int
    n_frames: int
    duration_s: float

    # Pressure metrics
    peak_pressure_kpa: float
    mean_pressure_kpa: float
    pti_kpa_s: float   # pressure–time integral ("impulse of pressure")

    # Contact area metrics
    mean_contact_area_cm2: float
    max_contact_area_cm2: float

    # Force / load metrics
    peak_vgrf_N: float
    impulse_Ns: float
    load_rate_max_Ns: float
    load_rate_avg80_Ns: float

    # Temporal-spatial metrics
    stance_time_s: float
    step_time_s: float
    cadence_spm: float

    # CoP trajectory
    cop_path_len_cm: float


def _movavg(xs: List[float], w: int) -> List[float]:
    """Simple moving average of width w."""
    if w <= 1 or not xs:
        return xs[:]
    out: List[float] = []
    s = 0.0
    q: List[float] = []
    for v in xs:
        q.append(v)
        s += v
        if len(q) > w:
            s -= q.pop(0)
        out.append(s / len(q))
    return out


def _safe_float(x: object) -> Optional[float]:
    try:
        v = float(x)  # type: ignore[arg-type]
        if math.isfinite(v):
            return v
    except Exception:
        pass
    return None


def extract_per_frame_pressures(
    rows: List[Dict[str, object]],
    sensor_keys: List[str],
) -> List[List[float]]:
    """
    Returns pressures_kpa[frame][sensor_idx] as floats.
    Missing/invalid values -> 0.0.
    """
    frames: List[List[float]] = []
    if not rows or not sensor_keys:
        return frames
    for r in rows:
        row_vals: List[float] = []
        for k in sensor_keys:
            v = _safe_float(r.get(k))
            row_vals.append(v if v is not None else 0.0)
        frames.append(row_vals)
    return frames


def compute_contact_area_series(
    pressures_kpa: List[List[float]],
    params: CalcParams,
) -> List[float]:
    """Contact area per frame in cm², based on contact threshold."""
    area = params["sensel_area_cm2"]
    thr = params["contact_kpa"]
    out: List[float] = []
    for frame in pressures_kpa:
        n_contact = sum(1 for p in frame if p >= thr)
        out.append(n_contact * area)
    return out


def compute_avg_pressure_series(
    pressures_kpa: List[List[float]],
    params: CalcParams,
) -> List[float]:
    """Average pressure over active sensels per frame (kPa)."""
    out: List[float] = []
    thr = params["contact_kpa"]
    for frame in pressures_kpa:
        active = [p for p in frame if p >= thr]
        out.append(sum(active) / len(active) if active else 0.0)
    return out


def compute_vgrf_series(
    pressures_kpa: List[List[float]],
    params: CalcParams,
) -> List[float]:
    """
    vGRF per frame in Newtons:

      1 kPa = 0.1 N/cm²
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
    params: CalcParams,
) -> float:
    """
    Pressure–Time Integral over the whole segment (kPa·s).

    This is effectively the "impulse of pressure" for the selected
    frame range: sum_t( average_contact_pressure(t) * dt ).
    """
    if not pressures_kpa:
        return 0.0
    dt = 1.0 / max(1e-9, params["fs"])
    avg = compute_avg_pressure_series(pressures_kpa, params)
    return sum(avg) * dt


def compute_cop_path(
    pressures_kpa: List[List[float]],
    sensel_xy_cm: List[Tuple[float, float]],
) -> List[Tuple[float, float]]:
    """
    CoP per frame (x,y) using pressure-weighted centroid in cm.

    If total pressure == 0, returns (nan, nan) for that frame.
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
    params: CalcParams,
) -> List[Tuple[int, int]]:
    """
    Returns list of (start_idx, end_idx) for stance windows where vGRF exceeds
    BW * stance_bw_frac. BW = body_mass_kg * 9.81.
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
        spans.append((start, len(vgrf_N) - 1))
    return spans


def temporal_spatial_from_spans(
    spans: List[Tuple[int, int]],
    params: CalcParams,
) -> Dict[str, float]:
    """
    Basic temporal-spatial metrics derived from stance windows:
    stance time, swing, step/stride time, cadence.
    """
    fs = params["fs"]
    if not spans:
        return {
            "stance_time_s": 0.0,
            "swing_time_s": 0.0,
            "step_time_s": 0.0,
            "stride_time_s": 0.0,
            "cadence_spm": 0.0,
        }

    stance_times = [(b - a + 1) / fs for (a, b) in spans]
    stance_mean = statistics.mean(stance_times)

    # step time ~ distance between consecutive onsets
    onsets = [a for (a, _) in spans]
    inter: List[float] = []
    for i in range(1, len(onsets)):
        inter.append((onsets[i] - onsets[i - 1]) / fs)

    step_time = statistics.mean(inter) if inter else stance_mean
    stride_time = (inter[0] * 2.0) if inter else (stance_mean * 2.0)
    cadence_spm = 60.0 / step_time if step_time > 0 else 0.0

    # swing ~ stride - stance (single-leg estimate)
    swing_time = max(0.0, stride_time - stance_mean)

    return {
        "stance_time_s": stance_mean,
        "swing_time_s": swing_time,
        "step_time_s": step_time,
        "stride_time_s": stride_time,
        "cadence_spm": cadence_spm,
    }


def compute_impulse_Ns(vgrf_N: List[float], params: CalcParams) -> float:
    """Force impulse over the segment: ∑ F(t) dt (N·s)."""
    dt = 1.0 / max(1e-9, params["fs"])
    return sum(vgrf_N) * dt


def compute_load_rate(
    vgrf_N: List[float],
    params: CalcParams,
) -> Dict[str, float]:
    """
    Load rate metrics:
      * max_dFdt_Ns        – instantaneous maximum slope (N/s)
      * avg_up_to_80pct_Ns – average slope from onset to 80% of peak (N/s)
    """
    fs = params["fs"]
    if len(vgrf_N) < 3:
        return {"max_dFdt_Ns": 0.0, "avg_up_to_80pct_Ns": 0.0}
    # finite differences
    d: List[float] = []
    for i in range(1, len(vgrf_N)):
        d.append((vgrf_N[i] - vgrf_N[i - 1]) * fs)
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
    """
    Symmetry index in percent:

      SI% = 100 * (R - L) / (0.5 * (R + L))

    Caller decides which side is a / b.
    """
    denom = 0.5 * (a + b)
    return 0.0 if denom == 0 else 100.0 * (b - a) / denom


def compute_per_frame_bundle(
    pressures_kpa: List[List[float]],
    sensel_xy_cm: List[Tuple[float, float]],
    params: CalcParams,
) -> Dict[str, List[float] | List[Tuple[float, float]]]:
    """
    Convenience helper: compute all per-frame series needed by the
    Calculations tab and segment metrics.
    """
    vgrf = compute_vgrf_series(pressures_kpa, params)
    vgrf_smooth = _movavg(vgrf, params["smooth_win"])
    contact_area = compute_contact_area_series(pressures_kpa, params)
    avg_p = compute_avg_pressure_series(pressures_kpa, params)
    cop = compute_cop_path(pressures_kpa, sensel_xy_cm)
    return {
        "vgrf_N": vgrf_smooth,
        "contact_area_cm2": contact_area,
        "avg_pressure_kPa": avg_p,
        "cop_xy_cm": cop,
    }


def compute_segment_metrics(
    pressures_kpa: List[List[float]],
    sensel_xy_cm: List[Tuple[float, float]],
    params: CalcParams,
    start_frame: int,
    end_frame: int,
    name: Optional[str] = None,
) -> SegmentMetrics:
    """
    Compute all key plantar-loading / force / temporal metrics for a specific
    frame range [start_frame, end_frame], inclusive.
    """
    n_total = len(pressures_kpa)
    if n_total == 0:
        return SegmentMetrics(
            name=name or "",
            start_frame=0,
            end_frame=-1,
            n_frames=0,
            duration_s=0.0,
            peak_pressure_kpa=0.0,
            mean_pressure_kpa=0.0,
            pti_kpa_s=0.0,
            mean_contact_area_cm2=0.0,
            max_contact_area_cm2=0.0,
            peak_vgrf_N=0.0,
            impulse_Ns=0.0,
            load_rate_max_Ns=0.0,
            load_rate_avg80_Ns=0.0,
            stance_time_s=0.0,
            step_time_s=0.0,
            cadence_spm=0.0,
            cop_path_len_cm=0.0,
        )

    start = max(0, int(start_frame))
    end = min(n_total - 1, int(end_frame))
    if end < start:
        end = start

    seg_pressures = pressures_kpa[start : end + 1]
    if not seg_pressures:
        return SegmentMetrics(
            name=name or "",
            start_frame=start,
            end_frame=end,
            n_frames=0,
            duration_s=0.0,
            peak_pressure_kpa=0.0,
            mean_pressure_kpa=0.0,
            pti_kpa_s=0.0,
            mean_contact_area_cm2=0.0,
            max_contact_area_cm2=0.0,
            peak_vgrf_N=0.0,
            impulse_Ns=0.0,
            load_rate_max_Ns=0.0,
            load_rate_avg80_Ns=0.0,
            stance_time_s=0.0,
            step_time_s=0.0,
            cadence_spm=0.0,
            cop_path_len_cm=0.0,
        )

    # Per-frame bundle within the segment
    per_frame = compute_per_frame_bundle(seg_pressures, sensel_xy_cm, params)
    vgrf = list(per_frame["vgrf_N"])                    # type: ignore[index]
    contact_area = list(per_frame["contact_area_cm2"])  # type: ignore[index]
    avg_p = list(per_frame["avg_pressure_kPa"])         # type: ignore[index]
    cop_xy = list(per_frame["cop_xy_cm"])               # type: ignore[index]

    n_frames = len(vgrf)
    dt = 1.0 / max(1e-9, params["fs"])
    duration_s = n_frames * dt

    # Pressure metrics
    peak_pressure_kpa = max(avg_p) if avg_p else 0.0
    mean_pressure_kpa = statistics.mean(avg_p) if avg_p else 0.0
    pti_kpa_s = compute_pti_kpas(seg_pressures, params)

    # Contact area metrics
    mean_contact_area_cm2 = statistics.mean(contact_area) if contact_area else 0.0
    max_contact_area_cm2 = max(contact_area) if contact_area else 0.0

    # Force/impulse metrics
    peak_vgrf_N = max(vgrf) if vgrf else 0.0
    impulse_Ns = compute_impulse_Ns(vgrf, params)
    rates = compute_load_rate(vgrf, params)

    # Stance / temporal-spatial metrics based on vGRF stance windows
    spans = detect_stance_windows(vgrf, params)
    tempo = temporal_spatial_from_spans(spans, params)

    # CoP path length (cm)
    cop_path_len_cm = 0.0
    last: Optional[Tuple[float, float]] = None
    for (x, y) in cop_xy:
        if not (math.isfinite(x) and math.isfinite(y)):
            last = None
            continue
        if last is not None:
            dx = x - last[0]
            dy = y - last[1]
            cop_path_len_cm += math.hypot(dx, dy)
        last = (x, y)

    return SegmentMetrics(
        name=name or "",
        start_frame=start,
        end_frame=end,
        n_frames=n_frames,
        duration_s=duration_s,
        peak_pressure_kpa=peak_pressure_kpa,
        mean_pressure_kpa=mean_pressure_kpa,
        pti_kpa_s=pti_kpa_s,
        mean_contact_area_cm2=mean_contact_area_cm2,
        max_contact_area_cm2=max_contact_area_cm2,
        peak_vgrf_N=peak_vgrf_N,
        impulse_Ns=impulse_Ns,
        load_rate_max_Ns=rates["max_dFdt_Ns"],
        load_rate_avg80_Ns=rates["avg_up_to_80pct_Ns"],
        stance_time_s=tempo["stance_time_s"],
        step_time_s=tempo["step_time_s"],
        cadence_spm=tempo["cadence_spm"],
        cop_path_len_cm=cop_path_len_cm,
    )
