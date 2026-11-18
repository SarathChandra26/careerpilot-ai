from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.job import JobResponse

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: bool = False

class TaskCreate(TaskBase):
    application_id: Optional[str] = None
    job_id: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_completed: Optional[bool] = None

class TaskResponse(TaskBase):
    id: str
    candidate_id: str
    application_id: Optional[str] = None
    job_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class ApplicationBase(BaseModel):
    job_id: str
    status: str = Field(default="Saved", pattern="^(Interested|Saved|Preparing|Applied|Interview Scheduled|Rejected|Offer Received)$")
    notes: Optional[str] = None
    applied_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(Interested|Saved|Preparing|Applied|Interview Scheduled|Rejected|Offer Received)$")
    notes: Optional[str] = None
    applied_date: Optional[datetime] = None
    deadline_date: Optional[datetime] = None

class ApplicationResponse(ApplicationBase):
    id: str
    candidate_id: str
    created_at: datetime
    updated_at: datetime
    job: Optional[JobResponse] = None
    tasks: List[TaskResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
