# Development Log (Prototypes, Findings, and Fixes)

This project is built iteratively. I’m documenting prototypes, failure modes, and design decisions so I can explain the evolution clearly in interviews and future development.

---

## v0 — API Skeleton + Job Pipeline (Milestone 1)
**Goal:** Create a backend that accepts an audio upload and returns a job_id that can be polled for results.

**What I built:**
- FastAPI endpoints:
  - `POST /upload` → stores audio, creates job_id, writes status/result
  - `GET /jobs/{job_id}` → returns processing/done/error
- Storage layer to persist results per job_id
- Frontend scaffolding (Vite + React) to support future visualization

**What went right:**
- The job-based API design was correct from the start (upload → status → result).
- This structure makes it easy to run heavier analysis later (async/background work).

**What went wrong:**
- I initially used dummy analysis outputs (fake tempo/loudness curves), which verified plumbing but not correctness.

**Next:**
- Replace dummy analysis with real tempo extraction and validate with known recordings.

---

## v1 — First Real Tempo Prototype (Beat-to-Beat BPM)
**Goal:** Produce a tempo curve from an uploaded performance.

**Implementation:**
- Used librosa beat tracking to get beat timestamps
- Computed instantaneous BPM as: `60 / (t[i+1] - t[i])`
- Returned:
  - `tempo_curve` (t, bpm points)
  - summary stats (avg_bpm, variance, coefficient of variation)
  - naive “tempo_instability” events based on deviation threshold

**Validation Test: Bach Invention in C Major (BWV 772)**
**Expected tempo:** ~72–80 BPM (quarter note)
**Observed output:** avg_bpm ≈ 140.53 BPM :contentReference[oaicite:1]{index=1}

**Key observation:**
- The tempo curve was very stable around ~139.67 BPM for most of the clip :contentReference[oaicite:2]{index=2}.
- This indicates the algorithm is consistently tracking a *subdivision* (double-time), not randomly failing.

**Conclusion:**
- This is not “off by a bit.” It’s a known beat-tracking failure mode for solo piano:
  - beat detector often locks onto subdivisions (eighth-note pulse instead of quarter-note pulse),
  - especially with legato articulation and weak percussive transients.

**What went right:**
- End-to-end system works: upload → analysis → persisted results → job fetch.
- The tempo extractor is consistent and produces meaningful stability signals (CV was low, indicating steady playing) :contentReference[oaicite:3]{index=3}.

**What went wrong:**
- Musical interpretation is incorrect: “beat” ≠ “intended tempo unit.”

---

## Planned Fix — Tempo Interpretation Layer (Half/Double-Time Resolution)
**Goal:** Convert algorithm pulse into musically meaningful tempo.

**Approach (v2 plan):**
- Return multiple tempo interpretations:
  - `as_detected_bpm`
  - `half_time_bpm`
  - `double_time_bpm`
  - `recommended_bpm` chosen by heuristic
- Heuristic candidates:
  1) pick the tempo closest to the global tempo estimate from librosa
  2) prefer tempos within a typical musical range for solo piano (e.g., 40–120 for quarter-note)
  3) allow user to select “beat unit” (quarter vs eighth) in UI

**Why this matters:**
- Makes the tool honest: it distinguishes “detected pulse” from “musical tempo.”
- Prevents mislabeling steady performances as “140 BPM” when the musician intended ~70–80.

---

## Next Steps
- v2: implement half/double-time resolution + smoothing of tempo curve for readability
- v3: add loudness/RMS curve (dynamic contour)
- v4: improve event detection (“most unstable section”, rubato score) and front-end plots
