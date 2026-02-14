from __future__ import annotations

from typing import Dict, Any, List, Tuple
import numpy as np
import librosa


# -----------------------
# Helpers
# -----------------------
def trim_silence(
    y: np.ndarray,
    sr: int,
    top_db: float = 35.0,
) -> Tuple[np.ndarray, int, int]:
    """Trim leading/trailing silence using librosa's energy-based trimming."""
    if y is None or len(y) == 0 or sr is None:
        return y, 0, 0

    y_trim, idx = librosa.effects.trim(y, top_db=top_db)
    start, end = int(idx[0]), int(idx[1])
    return y_trim, start, end


def _moving_average(x: np.ndarray, w: int) -> np.ndarray:
    if len(x) == 0:
        return x
    if len(x) < w:
        return x.copy()
    kernel = np.ones(w, dtype=float) / float(w)
    return np.convolve(x, kernel, mode="same")


def resample_curve(points: List[dict], t_key: str, y_key: str, grid_t: np.ndarray) -> np.ndarray:
    """Linearly resample curve points to grid_t."""
    if not points:
        return np.array([])

    t = np.array([p[t_key] for p in points], dtype=float)
    y = np.array([p[y_key] for p in points], dtype=float)

    order = np.argsort(t)
    t = t[order]
    y = y[order]

    lo, hi = float(t[0]), float(t[-1])
    grid = np.clip(grid_t, lo, hi)

    return np.interp(grid, t, y)


def _safe_float(x: Any) -> float | None:
    try:
        v = float(x)
        if not np.isfinite(v):
            return None
        return v
    except Exception:
        return None


# -----------------------
# Tempo
# -----------------------
def analyze_tempo(audio_path: str) -> Dict[str, Any]:
    """Tempo analysis (beat-based, then smoothed)."""
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    duration_sec_raw = float(len(y) / sr) if sr else 0.0

    top_db = 35.0
    y_trim, start_samp, end_samp = trim_silence(y, sr, top_db=top_db)
    duration_sec_trimmed = float(len(y_trim) / sr) if sr else 0.0
    start_sec = float(start_samp / sr) if sr else 0.0
    end_sec = float(end_samp / sr) if sr else 0.0

    if sr is None or len(y_trim) < 2048:
        y_trim = y

    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=y_trim, sr=sr, hop_length=hop_length)

    tempo_est, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, hop_length=hop_length
    )
    tempo_est = float(np.atleast_1d(tempo_est)[0])
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    if len(beat_times) < 3:
        return {
            "duration_sec_raw": duration_sec_raw,
            "duration_sec_trimmed": duration_sec_trimmed,
            "trim": {"start_sec": start_sec, "end_sec": end_sec, "top_db": top_db},
            "tempo_curve": [],
            "summary": {"avg_bpm": tempo_est, "bpm_variance": 0.0, "tempo_stability_cv": None},
            "tempo_interpretations": {
                "as_detected_bpm": tempo_est,
                "half_time_bpm": tempo_est / 2.0,
                "double_time_bpm": tempo_est * 2.0,
                "recommended_bpm": tempo_est,
                "recommended_label": "as_detected_bpm",
                "reason": "Not enough beats detected to infer a stable curve.",
            },
            "events": [],
        }

    ibi = np.diff(beat_times)
    bpm_inst = 60.0 / np.clip(ibi, 1e-6, None)
    t_mid = (beat_times[:-1] + beat_times[1:]) / 2.0

    bpm_inst = np.clip(bpm_inst, 40.0, 240.0)

    avg_bpm = float(np.mean(bpm_inst))
    bpm_variance = float(np.var(bpm_inst))
    std_bpm = float(np.std(bpm_inst))
    tempo_stability_cv = float(std_bpm / avg_bpm) if avg_bpm > 1e-9 else None

    as_detected = avg_bpm
    half_time = as_detected / 2.0
    double_time = as_detected * 2.0

    best_name, best_bpm = "as_detected_bpm", as_detected
    reason = "Recommended tempo chosen by heuristic."

    # Prefer half-time if it lands in a more plausible piano tempo range
    if 90.0 <= as_detected <= 180.0 and 40.0 <= half_time <= 110.0:
        best_name, best_bpm = "half_time_bpm", half_time
        reason = "Detected pulse likely reflects subdivisions; half-time lands in a more plausible musical tempo range."
    elif 40.0 <= as_detected <= 120.0:
        best_name, best_bpm = "as_detected_bpm", as_detected
    elif 40.0 <= double_time <= 120.0:
        best_name, best_bpm = "double_time_bpm", double_time

    tempo_interpretations = {
        "as_detected_bpm": float(as_detected),
        "half_time_bpm": float(half_time),
        "double_time_bpm": float(double_time),
        "recommended_bpm": float(best_bpm),
        "recommended_label": best_name,
        "reason": reason,
    }

    scale = 1.0
    if best_name == "half_time_bpm":
        scale = 0.5
    elif best_name == "double_time_bpm":
        scale = 2.0

    tempo_curve: List[dict] = [
        {"t": float(t), "bpm": float(b), "bpm_musical": float(b * scale)}
        for t, b in zip(t_mid, bpm_inst)
    ]

    bpm_arr = np.array([p["bpm"] for p in tempo_curve], dtype=float)
    bpm_mus_arr = np.array([p["bpm_musical"] for p in tempo_curve], dtype=float)

    bpm_smooth = _moving_average(bpm_arr, w=7)
    bpm_mus_smooth = _moving_average(bpm_mus_arr, w=7)

    for i in range(len(tempo_curve)):
        tempo_curve[i]["bpm_smooth"] = float(bpm_smooth[i])
        tempo_curve[i]["bpm_musical_smooth"] = float(bpm_mus_smooth[i])

    events = []
    if len(bpm_inst) >= 3 and avg_bpm > 0:
        dev = np.abs(bpm_inst - avg_bpm) / avg_bpm
        mask = dev > 0.15
        start = None
        for i, is_bad in enumerate(mask):
            if is_bad and start is None:
                start = i
            if (not is_bad or i == len(mask) - 1) and start is not None:
                end = i if not is_bad else i + 1
                if end - start >= 2:
                    events.append(
                        {
                            "t_start": float(t_mid[start]),
                            "t_end": float(t_mid[end - 1]),
                            "type": "tempo_instability",
                            "severity": float(min(1.0, np.mean(dev[start:end]) / 0.30)),
                        }
                    )
                start = None

    return {
        "duration_sec_raw": duration_sec_raw,
        "duration_sec_trimmed": duration_sec_trimmed,
        "trim": {"start_sec": start_sec, "end_sec": end_sec, "top_db": top_db},
        "tempo_curve": tempo_curve,
        "summary": {
            "avg_bpm": avg_bpm if avg_bpm > 0 else tempo_est,
            "bpm_variance": bpm_variance,
            "tempo_stability_cv": tempo_stability_cv,
        },
        "tempo_interpretations": tempo_interpretations,
        "events": events,
    }


# -----------------------
# Loudness (dB)
# -----------------------
def analyze_loudness(audio_path: str) -> Dict[str, Any]:
    """Loudness analysis in dB (relative to loudest moment in THIS recording)."""
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    duration_sec_raw = float(len(y) / sr) if sr else 0.0

    top_db = 35.0
    y_trim, start_samp, end_samp = trim_silence(y, sr, top_db=top_db)
    duration_sec_trimmed = float(len(y_trim) / sr) if sr else 0.0
    start_sec = float(start_samp / sr) if sr else 0.0
    end_sec = float(end_samp / sr) if sr else 0.0

    if sr is None or len(y_trim) < 2048:
        return {
            "duration_sec_raw": duration_sec_raw,
            "duration_sec_trimmed": duration_sec_trimmed,
            "trim": {"start_sec": start_sec, "end_sec": end_sec, "top_db": top_db},
            "loudness_curve": [],
            "loudness_summary": {"mean_db": None, "dynamic_range_db": None},
        }

    hop_length = 512
    frame_length = 2048

    rms = librosa.feature.rms(y=y_trim, frame_length=frame_length, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)

    rms = np.maximum(rms, 1e-12)
    ref = float(np.max(rms)) if float(np.max(rms)) > 0 else 1e-12
    rms_db = librosa.amplitude_to_db(rms, ref=ref)

    loudness_curve = [{"t": float(t), "rms_db": float(db)} for t, db in zip(times, rms_db)]

    mean_db = float(np.mean(rms_db))
    dynamic_range_db = float(np.percentile(rms_db, 95) - np.percentile(rms_db, 5))

    return {
        "duration_sec_raw": duration_sec_raw,
        "duration_sec_trimmed": duration_sec_trimmed,
        "trim": {"start_sec": start_sec, "end_sec": end_sec, "top_db": top_db},
        "loudness_curve": loudness_curve,
        "loudness_summary": {"mean_db": mean_db, "dynamic_range_db": dynamic_range_db},
    }


# -----------------------
# DTW-aligned Comparison
# -----------------------
def compare_recordings_dtw(student: Dict[str, Any], reference: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two recordings using DTW on loudness to align time.
    Then compute aligned tempo/loudness deltas.
    """
    s_loud_curve = student.get("loudness_curve", [])
    r_loud_curve = reference.get("loudness_curve", [])
    if not s_loud_curve or not r_loud_curve:
        return {"error": "Missing loudness curves for DTW alignment."}

    ds = 0.1  # seconds
    s_dur = float(student.get("duration_sec_trimmed", 0.0) or 0.0)
    r_dur = float(reference.get("duration_sec_trimmed", 0.0) or 0.0)
    if s_dur <= 0 or r_dur <= 0:
        return {"error": "Non-positive trimmed durations."}

    s_times = np.arange(0.0, s_dur, ds)
    r_times = np.arange(0.0, r_dur, ds)

    s_l = resample_curve(s_loud_curve, "t", "rms_db", s_times)
    r_l = resample_curve(r_loud_curve, "t", "rms_db", r_times)
    if len(s_l) == 0 or len(r_l) == 0:
        return {"error": "Failed to resample loudness curves."}

    # DTW path on loudness
    _, wp = librosa.sequence.dtw(X=s_l.reshape(1, -1), Y=r_l.reshape(1, -1), metric="euclidean")
    wp = wp[::-1]  # forward order (i, j)

    idx_s = np.array([i for i, _ in wp], dtype=int)
    idx_r = np.array([j for _, j in wp], dtype=int)

    # Reduce path to unique student indices (first match)
    seen = set()
    pairs = []
    for i, j in zip(idx_s, idx_r):
        if i not in seen:
            pairs.append((i, j))
            seen.add(i)

    if len(pairs) < 10:
        return {"error": "DTW path too short to compare reliably."}

    s_idx = np.array([p[0] for p in pairs], dtype=int)
    r_idx = np.array([p[1] for p in pairs], dtype=int)

    s_times_ds = s_times[s_idx]
    r_times_ds = r_times[r_idx]

    # Tempo curves
    s_tempo_curve = student.get("tempo_curve", [])
    r_tempo_curve = reference.get("tempo_curve", [])

    def pick_tempo_key(curve: List[dict]) -> str:
        if curve and "bpm_musical_smooth" in curve[0]:
            return "bpm_musical_smooth"
        if curve and "bpm_musical" in curve[0]:
            return "bpm_musical"
        if curve and "bpm_smooth" in curve[0]:
            return "bpm_smooth"
        return "bpm"

    s_key = pick_tempo_key(s_tempo_curve)
    r_key = pick_tempo_key(r_tempo_curve)

    s_t = resample_curve(s_tempo_curve, "t", s_key, s_times)
    r_t = resample_curve(r_tempo_curve, "t", r_key, r_times)

    if len(s_t) == 0 or len(r_t) == 0:
        return {"error": "Missing tempo curves for DTW comparison."}

    tempo_diff_ds = (s_t[s_idx] - r_t[r_idx])
    loud_diff_ds = (s_l[s_idx] - r_l[r_idx])

    mean_abs_bpm_diff = float(np.mean(np.abs(tempo_diff_ds)))
    mean_abs_loud_db_diff = float(np.mean(np.abs(loud_diff_ds)))

    s_rec = student.get("tempo_interpretations", {}).get("recommended_bpm")
    r_rec = reference.get("tempo_interpretations", {}).get("recommended_bpm")
    rec_diff = float(s_rec - r_rec) if (s_rec is not None and r_rec is not None) else None

    # overlap should never exceed either trimmed duration
    overlap_sec = float(min(s_dur, r_dur))

    return {
        "overlap_sec": overlap_sec,
        "grid_hz": int(round(1.0 / ds)),
        "tempo": {
            "student_key": s_key,
            "reference_key": r_key,
            "mean_abs_bpm_diff": mean_abs_bpm_diff,
            "recommended_bpm_diff": rec_diff,
        },
        "loudness": {
            "mean_abs_db_diff": mean_abs_loud_db_diff,
            "student_mean_db": student.get("loudness_summary", {}).get("mean_db"),
            "reference_mean_db": reference.get("loudness_summary", {}).get("mean_db"),
        },
        "curves": {
            "t": s_times_ds.tolist(),          # frontend x-axis
            "student_t": s_times_ds.tolist(),   # keep for debugging
            "ref_t": r_times_ds.tolist(),
            "tempo_diff": tempo_diff_ds.tolist(),
            "loudness_diff_db": loud_diff_ds.tolist(),
        },
        "notes": [
            "DTW alignment uses loudness as a proxy for musical progress (v1).",
            "Differences may still be skewed by pedaling/room noise and long sustains.",
        ],
    }


# -----------------------
# Insights
# -----------------------
def build_insights(student: Dict[str, Any], reference: Dict[str, Any], comp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Build human-readable insights from summaries + comparison metrics.
    Returns a list of insight cards for the frontend.
    """
    insights: List[Dict[str, Any]] = []

    s_rec = _safe_float(student.get("tempo_interpretations", {}).get("recommended_bpm"))
    r_rec = _safe_float(reference.get("tempo_interpretations", {}).get("recommended_bpm"))
    rec_diff = _safe_float(comp.get("tempo", {}).get("recommended_bpm_diff"))

    mean_abs_bpm = _safe_float(comp.get("tempo", {}).get("mean_abs_bpm_diff"))
    mean_abs_db = _safe_float(comp.get("loudness", {}).get("mean_abs_db_diff"))

    # This is “coefficient of variation” internally, but we’ll present it plainly.
    s_consistency = _safe_float(student.get("summary", {}).get("tempo_stability_cv"))
    r_consistency = _safe_float(reference.get("summary", {}).get("tempo_stability_cv"))

    s_mean_db = _safe_float(student.get("loudness_summary", {}).get("mean_db"))
    r_mean_db = _safe_float(reference.get("loudness_summary", {}).get("mean_db"))

    s_dr = _safe_float(student.get("loudness_summary", {}).get("dynamic_range_db"))
    r_dr = _safe_float(reference.get("loudness_summary", {}).get("dynamic_range_db"))

    # 1) Overall tempo level
    if s_rec is not None and r_rec is not None:
        faster = "faster" if s_rec > r_rec else "slower"
        pct = abs(s_rec - r_rec) / max(r_rec, 1e-9) * 100.0
        severity = "good" if pct <= 5 else ("warn" if pct <= 12 else "bad")
        insights.append(
            {
                "title": "Overall tempo vs reference",
                "severity": severity,
                "detail": f"Student recommended tempo is {s_rec:.1f} BPM vs reference {r_rec:.1f} BPM ({faster} by {abs(s_rec-r_rec):.1f} BPM, ~{pct:.0f}%).",
                "suggestion": "If you want to match the reference feel, aim to close the BPM gap gradually (e.g., +2 BPM per run-through) rather than jumping straight to target.",
            }
        )

    # 2) Tempo consistency (rubato vs instability proxy)
    if s_consistency is not None:
        # Lower = steadier (less relative variation)
        if s_consistency <= 0.06:
            sev = "good"
            msg = "Tempo is quite steady overall."
        elif s_consistency <= 0.10:
            sev = "warn"
            msg = "Tempo varies moderately (could be rubato or mild instability)."
        else:
            sev = "bad"
            msg = "Tempo varies a lot (often reads as instability more than intentional rubato)."

        insights.append(
            {
                "title": "Tempo consistency",
                "severity": sev,
                "detail": f"{msg} Tempo consistency score ≈ {s_consistency:.3f} (lower = steadier).",
                "suggestion": "Try recording with a soft metronome on big beats only, then re-record without it and see if the consistency score improves.",
            }
        )

    # 3) Mean absolute tempo tracking difference (DTW-aligned)
    if mean_abs_bpm is not None:
        if mean_abs_bpm <= 4:
            sev = "good"
        elif mean_abs_bpm <= 10:
            sev = "warn"
        else:
            sev = "bad"
        insights.append(
            {
                "title": "Tempo tracking vs reference (aligned)",
                "severity": sev,
                "detail": f"Average aligned tempo difference |ΔBPM| ≈ {mean_abs_bpm:.1f}.",
                "suggestion": "If this feels too high, focus on matching the reference’s phrase pacing: compare 10–15s segments rather than the whole piece.",
            }
        )

    # 4) Loudness level
    if s_mean_db is not None and r_mean_db is not None:
        diff = s_mean_db - r_mean_db
        if abs(diff) <= 2:
            sev = "good"
            msg = "Overall loudness level is close to the reference."
        elif abs(diff) <= 5:
            sev = "warn"
            msg = "Overall loudness level differs noticeably from the reference."
        else:
            sev = "bad"
            msg = "Overall loudness level differs a lot from the reference."
        louder = "louder" if diff > 0 else "softer"
        insights.append(
            {
                "title": "Overall loudness vs reference",
                "severity": sev,
                "detail": f"{msg} Student is {louder} by ~{abs(diff):.1f} dB (relative scale).",
                "suggestion": "If you’re softer, experiment with closer mic placement and more intentional voicing before just ‘playing harder’.",
            }
        )

    # 5) Dynamic range comparison
    if s_dr is not None and r_dr is not None:
        diff = s_dr - r_dr
        if abs(diff) <= 2:
            sev = "good"
        elif abs(diff) <= 6:
            sev = "warn"
        else:
            sev = "bad"
        more = "more" if diff > 0 else "less"
        insights.append(
            {
                "title": "Dynamic range",
                "severity": sev,
                "detail": f"Student dynamic range ≈ {s_dr:.1f} dB vs reference {r_dr:.1f} dB (student has {more} range by ~{abs(diff):.1f} dB).",
                "suggestion": "If range is low: exaggerate pp vs mf contrast in practice. If range is high: check if peaks are unintended accents.",
            }
        )

    # 6) Loudness tracking difference
    if mean_abs_db is not None:
        if mean_abs_db <= 1.5:
            sev = "good"
        elif mean_abs_db <= 3.5:
            sev = "warn"
        else:
            sev = "bad"
        insights.append(
            {
                "title": "Dynamics tracking vs reference (aligned)",
                "severity": sev,
                "detail": f"Average aligned loudness difference |ΔdB| ≈ {mean_abs_db:.2f}.",
                "suggestion": "If this is high, match the reference’s ‘shape’ more than absolute level: crescendos/decrescendos should line up in time.",
            }
        )

    # Sanity check (optional)
    if rec_diff is not None and s_rec is not None and r_rec is not None:
        if abs((s_rec - r_rec) - rec_diff) > 1e-3:
            insights.append(
                {
                    "title": "Sanity check",
                    "severity": "warn",
                    "detail": "Recommended BPM diff in comp doesn’t exactly match student/reference values (minor inconsistency).",
                    "suggestion": "Not critical, but worth checking keys if you refactor tempo_interpretations.",
                }
            )

    return insights
