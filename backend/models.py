from pydantic import BaseModel
from typing import Literal, Optional, Dict, Any

JobStatus = Literal["processing", "done", "error"]


class CompareRequest(BaseModel):
    student_job_id: str
    reference_job_id: str
    
class JobCreateResponse(BaseModel):
    job_id: str

class JobResult(BaseModel):
    job_id: str
    status: JobStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
