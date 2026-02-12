from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid

from analysis import analyze_tempo
from models import JobCreateResponse, JobResult
import storage

app = FastAPI(title="Classical Performance Diagnostic Tool API")

# Dev CORS: allow local frontend
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
    contents = await file.read()
    audio_path.write_bytes(contents)

    storage.write_status(job_id, "processing")

    try:
        tempo_out = analyze_tempo(str(audio_path))

        # Placeholder for now (we’ll add RMS loudness next)
        loudness_curve = []

        result = {
            "job_id": job_id,
            "duration_sec": tempo_out["duration_sec"],
            "tempo_curve": tempo_out["tempo_curve"],
            "loudness_curve": loudness_curve,
            "tempo_interpretations": tempo_out["tempo_interpretations"],
            "events": tempo_out["events"],
            "summary": {
                "avg_bpm": tempo_out["summary"]["avg_bpm"],
                "bpm_variance": tempo_out["summary"]["bpm_variance"],
                "tempo_stability_cv": tempo_out["summary"]["tempo_stability_cv"],
                "recommended_bpm": tempo_out["tempo_interpretations"]["recommended_bpm"],
                "recommended_label": tempo_out["tempo_interpretations"]["recommended_label"],
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
