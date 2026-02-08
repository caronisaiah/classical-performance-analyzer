import json
from pathlib import Path
from typing import Any, Dict, Optional

DATA_DIR = Path(__file__).parent / "data"

def job_dir(job_id: str) -> Path:
    return DATA_DIR / job_id

def ensure_job_dir(job_id: str) -> Path:
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    return d

def write_status(job_id: str, status: str, error: Optional[str] = None) -> None:
    d = ensure_job_dir(job_id)
    payload = {"job_id": job_id, "status": status, "error": error}
    (d / "status.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

def read_status(job_id: str) -> Optional[Dict[str, Any]]:
    p = job_dir(job_id) / "status.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))

def write_result(job_id: str, result: Dict[str, Any]) -> None:
    d = ensure_job_dir(job_id)
    (d / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

def read_result(job_id: str) -> Optional[Dict[str, Any]]:
    p = job_dir(job_id) / "result.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))
