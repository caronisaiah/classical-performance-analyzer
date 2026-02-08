from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid
import time

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

    # Dummy analysis for milestone 1 (replace later with real extraction)
    time.sleep(0.2)

    duration_sec = 60.0
    tempo_curve = [{"t": float(t), "bpm": 72.0 + (t % 10) * 0.5} for t in range(0, 60)]
    loudness_curve = [{"t": float(t), "rms": 0.01 + (t % 12) * 0.0008} for t in range(0, 60)]

    result = {
        "job_id": job_id,
        "duration_sec": duration_sec,
        "tempo_curve": tempo_curve,
        "loudness_curve": loudness_curve,
        "events": [
            {"t_start": 12.0, "t_end": 18.0, "type": "tempo_instability", "severity": 0.6},
            {"t_start": 40.0, "t_end": 44.0, "type": "dynamic_peak", "severity": 0.8},
        ],
        "summary": {"avg_bpm": 74.0, "bpm_variance": 9.8, "dynamic_range_proxy": 0.01},
        "audio_filename": audio_path.name,
    }

    storage.write_result(job_id, result)
    storage.write_status(job_id, "done")
    return JobCreateResponse(job_id=job_id)

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