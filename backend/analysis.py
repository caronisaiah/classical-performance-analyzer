from __future__ import annotations

from typing import Dict, Any, List
import numpy as np
import librosa


def analyze_tempo(audio_path: str) -> Dict[str, Any]:
    """
    Returns tempo-related outputs for v1:
      - duration_sec
      - tempo_curve: [{t, bpm, bpm_smooth}, ...]
      - summary: avg_bpm, bpm_variance, tempo_stability_cv
      - tempo_interpretations: detected/half/double + recommended
      - events: simple detection of unstable segments

    Uses beat tracking; curve is instantaneous BPM between consecutive beats.
    """
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    duration_sec = float(len(y) / sr) if sr else 0.0

    hop_length = 512
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)

    tempo_est, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env, sr=sr, hop_length=hop_length
    )
    tempo_est = float(np.atleast_1d(tempo_est)[0])

    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    # If not enough beats detected, return minimal result
    if len(beat_times) < 3:
        return {
            "duration_sec": duration_sec,
            "tempo_curve": [],
            "summary": {
                "avg_bpm": tempo_est,
                "bpm_variance": 0.0,
                "tempo_stability_cv": None,
            },
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

    ibi = np.diff(beat_times)  # inter-beat interval (seconds)
    bpm_inst = 60.0 / np.clip(ibi, 1e-6, None)
    t_mid = (beat_times[:-1] + beat_times[1:]) / 2.0

    # Clamp unrealistic tempo spikes
    bpm_inst = np.clip(bpm_inst, 40.0, 240.0)

    avg_bpm = float(np.mean(bpm_inst))
    bpm_variance = float(np.var(bpm_inst))
    std_bpm = float(np.std(bpm_inst))
    tempo_stability_cv = float(std_bpm / avg_bpm) if avg_bpm > 1e-9 else None

    # ---- Tempo interpretation (half/double time) ----
    as_detected = avg_bpm
    half_time = as_detected / 2.0
    double_time = as_detected * 2.0

    candidates = [
        ("as_detected_bpm", as_detected),
        ("half_time_bpm", half_time),
        ("double_time_bpm", double_time),
    ]

    def in_range(x: float, lo: float, hi: float) -> bool:
        return lo <= x <= hi

    best_name, best_bpm = "as_detected_bpm", as_detected

    # If it looks like a strong double-time case, choose half-time
    if as_detected > 120.0 and (tempo_stability_cv is not None and tempo_stability_cv < 0.06):
        best_name, best_bpm = "half_time_bpm", half_time
    else:
        # Otherwise, pick the first candidate that lands in a "musical" range
        for name, bpm in candidates:
            if in_range(bpm, 40.0, 120.0):
                best_name, best_bpm = name, bpm
                break

    tempo_interpretations = {
        "as_detected_bpm": float(as_detected),
        "half_time_bpm": float(half_time),
        "double_time_bpm": float(double_time),
        "recommended_bpm": float(best_bpm),
        "recommended_label": best_name,
        "reason": (
            "Detected pulse likely reflects subdivisions (double-time) for solo piano; "
            "recommended tempo selects half-time when detected BPM is high and very stable."
            if best_name == "half_time_bpm"
            else "Recommended tempo chosen by simple musical-range heuristic."
        ),
    }

    scale = 1.0
    if tempo_interpretations["recommended_label"] == "half_time_bpm":
        scale = 0.5
    elif tempo_interpretations["recommended_label"] == "double_time_bpm":
        scale = 2.0


    tempo_curve: List[dict] = [
    {"t": float(t), "bpm": float(b), "bpm_musical": float(b * scale)}
    for t, b in zip(t_mid, bpm_inst)
    ]

    # ---- Smooth tempo curve for UI readability (moving average) ----
    bpm_arr = np.array([p["bpm"] for p in tempo_curve], dtype=float)

    if len(bpm_arr) >= 7:
        w = 7
        kernel = np.ones(w) / w
        bpm_smooth = np.convolve(bpm_arr, kernel, mode="same")
        for i in range(len(tempo_curve)):
            tempo_curve[i]["bpm_smooth"] = float(bpm_smooth[i])
            tempo_curve[i]["bpm_musical_smooth"] = float(bpm_smooth[i] * scale)
    else:
        for p in tempo_curve:
            p["bpm_smooth"] = float(p["bpm"])
            p["bpm_musical_smooth"] = float(p["bpm_musical"])

    # Simple "unstable segment" detection:
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
        "duration_sec": duration_sec,
        "tempo_curve": tempo_curve,
        "summary": {
            "avg_bpm": avg_bpm if avg_bpm > 0 else tempo_est,
            "bpm_variance": bpm_variance,
            "tempo_stability_cv": tempo_stability_cv,
        },
        "tempo_interpretations": tempo_interpretations,
        "events": events,
    }