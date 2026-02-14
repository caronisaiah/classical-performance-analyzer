from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid

from analysis import analyze_tempo, analyze_loudness, compare_recordings_dtw, build_insights
from models import JobCreateResponse, JobResult
import storage

app = FastAPI(title="Classical Performance Diagnostic Tool API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload", response_model=JobCreateResponse)
async def upload_audio(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    allowed_ext = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_ext:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    job_id = uuid.uuid4().hex
    job_folder = storage.ensure_job_dir(job_id)

    audio_path = job_folder / f"audio{ext}"
    audio_path.write_bytes(await file.read())

    storage.write_status(job_id, "processing")

    try:
        tempo_out = analyze_tempo(str(audio_path))
        loud_out = analyze_loudness(str(audio_path))

        result = {
            "job_id": job_id,
            "duration_sec": tempo_out.get("duration_sec_trimmed", tempo_out.get("duration_sec_raw")),
            "duration_sec_raw": tempo_out.get("duration_sec_raw"),
            "duration_sec_trimmed": tempo_out.get("duration_sec_trimmed"),
            "trim": tempo_out.get("trim"),
            "tempo_curve": tempo_out.get("tempo_curve", []),
            "loudness_curve": loud_out.get("loudness_curve", []),
            "tempo_interpretations": tempo_out.get("tempo_interpretations", {}),
            "events": tempo_out.get("events", []),
            "summary": {
                "avg_bpm": tempo_out.get("summary", {}).get("avg_bpm"),
                "bpm_variance": tempo_out.get("summary", {}).get("bpm_variance"),
                "tempo_stability_cv": tempo_out.get("summary", {}).get("tempo_stability_cv"),
                "recommended_bpm": tempo_out.get("tempo_interpretations", {}).get("recommended_bpm"),
                "recommended_label": tempo_out.get("tempo_interpretations", {}).get("recommended_label"),
                "loudness_mean_db": loud_out.get("loudness_summary", loud_out.get("summary", {})).get("mean_db"),
                "dynamic_range_db": loud_out.get("loudness_summary", loud_out.get("summary", {})).get("dynamic_range_db"),
            },
            "audio_filename": audio_path.name,
        }

        storage.write_result(job_id, result)
        storage.write_status(job_id, "done")
        return JobCreateResponse(job_id=job_id)

    except Exception as e:
        storage.write_status(job_id, "error", error=str(e))
        raise


@app.get("/jobs/{job_id}", response_model=JobResult)
def get_job(job_id: str):
    status = storage.read_status(job_id)
    if status is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if status["status"] == "done":
        result = storage.read_result(job_id)
        return JobResult(job_id=job_id, status="done", result=result)

    if status["status"] == "error":
        return JobResult(job_id=job_id, status="error", error=status.get("error"))

    return JobResult(job_id=job_id, status=status["status"])


@app.post("/compare")
async def compare(
    student_file: UploadFile = File(...),
    reference_file: UploadFile = File(...),
    full: bool = False,
):
    allowed_ext = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}

    def _ext(name: str) -> str:
        return Path(name).suffix.lower()

    if not student_file.filename or _ext(student_file.filename) not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported or missing student_file")
    if not reference_file.filename or _ext(reference_file.filename) not in allowed_ext:
        raise HTTPException(status_code=400, detail="Unsupported or missing reference_file")

    job_id = uuid.uuid4().hex
    job_folder = storage.ensure_job_dir(job_id)

    s_path = job_folder / f"student{_ext(student_file.filename)}"
    r_path = job_folder / f"reference{_ext(reference_file.filename)}"

    s_path.write_bytes(await student_file.read())
    r_path.write_bytes(await reference_file.read())

    s_tempo = analyze_tempo(str(s_path))
    s_loud = analyze_loudness(str(s_path))
    r_tempo = analyze_tempo(str(r_path))
    r_loud = analyze_loudness(str(r_path))

    student = {
        **s_tempo,
        "loudness_curve": s_loud.get("loudness_curve", []),
        "loudness_summary": s_loud.get("loudness_summary", s_loud.get("summary", {})),
        "audio_filename": s_path.name,
    }
    reference = {
        **r_tempo,
        "loudness_curve": r_loud.get("loudness_curve", []),
        "loudness_summary": r_loud.get("loudness_summary", r_loud.get("summary", {})),
        "audio_filename": r_path.name,
    }

    comp = compare_recordings_dtw(student, reference)

    # ✅ Build insights if comparison succeeded
    if isinstance(comp, dict) and "error" not in comp:
        comp["insights"] = build_insights(student, reference, comp)
    else:
        # still provide insights key so frontend doesn’t break
        if isinstance(comp, dict):
            comp.setdefault("insights", [])

    out = {
        "job_id": job_id,
        "status": "done",
        "student": {
            "audio_filename": student["audio_filename"],
            "duration_sec_raw": student.get("duration_sec_raw"),
            "duration_sec_trimmed": student.get("duration_sec_trimmed"),
            "trim": student.get("trim"),
            "summary": student.get("summary"),
            "tempo_interpretations": student.get("tempo_interpretations"),
            "loudness_summary": student.get("loudness_summary"),
        },
        "reference": {
            "audio_filename": reference["audio_filename"],
            "duration_sec_raw": reference.get("duration_sec_raw"),
            "duration_sec_trimmed": reference.get("duration_sec_trimmed"),
            "trim": reference.get("trim"),
            "summary": reference.get("summary"),
            "tempo_interpretations": reference.get("tempo_interpretations"),
            "loudness_summary": reference.get("loudness_summary"),
        },
        "comparison": comp,
    }

    # Frontend compatibility: expose compare keys at top-level too
    if isinstance(comp, dict):
        for k in ("overlap_sec", "grid_hz", "tempo", "loudness", "curves", "notes", "insights"):
            if k in comp:
                out[k] = comp[k]

    if full:
        out["student"]["tempo_curve"] = student.get("tempo_curve", [])
        out["student"]["loudness_curve"] = student.get("loudness_curve", [])
        out["reference"]["tempo_curve"] = reference.get("tempo_curve", [])
        out["reference"]["loudness_curve"] = reference.get("loudness_curve", [])

    return out
