from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class JobSkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    is_required: bool = True
    importance_weight: float = Field(default=1.0, ge=0.1, le=5.0)

class JobSkillCreate(JobSkillBase):
    pass

class JobSkillResponse(JobSkillBase):
    id: int
    job_id: str
    model_config = ConfigDict(from_attributes=True)


class JobBase(BaseModel):
    company: str = Field(..., min_length=1, max_length=150)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=10)
    role_category: str = Field(..., min_length=1, max_length=100)
    experience_level: str = Field(default="Entry-level")
    experience_years_min: float = Field(default=0.0, ge=0.0)
    location: str = Field(default="Remote")
    work_mode: str = Field(default="Remote")  # Remote, Hybrid, On-site
    employment_type: str = Field(default="Full-time")  # Full-time, Part-time, Internship, Contract
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = Field(default="USD")
    application_url: Optional[str] = None
    is_synthetic: bool = True
    date_posted: Optional[str] = None

class JobCreate(JobBase):
    skills: List[JobSkillCreate] = Field(default_factory=list)

class JobUpdate(BaseModel):
    company: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    role_category: Optional[str] = None
    experience_level: Optional[str] = None
    experience_years_min: Optional[float] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    application_url: Optional[str] = None

class JobResponse(JobBase):
    id: str
    created_at: datetime
    updated_at: datetime
    skills: List[JobSkillResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class JobListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[JobResponse]


class JobFilterParams(BaseModel):
    query: Optional[str] = None
    role_category: Optional[str] = None
    experience_level: Optional[str] = None
    work_mode: Optional[str] = None
    location: Optional[str] = None
    min_salary: Optional[int] = None
    required_skills: Optional[List[str]] = None
    limit: int = 20
    offset: int = 0


class SavedJobResponse(BaseModel):
    id: int
    candidate_id: str
    job_id: str
    notes: Optional[str] = None
    saved_at: datetime
    job: JobResponse
    model_config = ConfigDict(from_attributes=True)


class FeedbackCreate(BaseModel):
    feedback: str = Field(..., pattern="^(Relevant|Not relevant|Already applied|Not interested)$")
    notes: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: int
    candidate_id: str
    job_id: str
    feedback: str
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
