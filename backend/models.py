from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any

JobStatus = Literal["processing", "done", "error"]

class JobCreateResponse(BaseModel):
    job_id: str

class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
