import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict, field_validator

class SkillBase(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=100)
    category: str = Field(default="Technical", max_length=80)
    proficiency: str = Field(default="Intermediate", max_length=50)
    verified: bool = True

class SkillCreate(SkillBase):
    pass

class SkillResponse(SkillBase):
    id: int
    candidate_id: str
    model_config = ConfigDict(from_attributes=True)


class PreferenceBase(BaseModel):
    preference_key: str = Field(..., min_length=1, max_length=100)
    preference_value: str = Field(..., min_length=1)

class PreferenceCreate(PreferenceBase):
    pass

class PreferenceResponse(PreferenceBase):
    id: int
    candidate_id: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CandidateBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=120)
    email: str = Field(..., min_length=3, max_length=120)
    phone: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    experience_years: float = Field(default=0.0, ge=0.0)
    experience_level: str = Field(default="Entry-level")
    preferred_roles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    preferred_work_mode: str = Field(default="Any")
    salary_expectation_min: Optional[int] = None
    salary_expectation_max: Optional[int] = None
    career_interests: List[str] = Field(default_factory=list)

    @field_validator("preferred_roles", "preferred_locations", "career_interests", mode="before")
    @classmethod
    def parse_json_lists(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [v]
            except Exception:
                return [s.strip() for s in v.split(",") if s.strip()]
        elif isinstance(v, list):
            return v
        return []

class CandidateCreate(CandidateBase):
    pass

class CandidateUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    experience_years: Optional[float] = None
    experience_level: Optional[str] = None
    preferred_roles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    preferred_work_mode: Optional[str] = None
    salary_expectation_min: Optional[int] = None
    salary_expectation_max: Optional[int] = None
    career_interests: Optional[List[str]] = None

    @field_validator("preferred_roles", "preferred_locations", "career_interests", mode="before")
    @classmethod
    def parse_update_json_lists(cls, v: Any) -> Optional[List[str]]:
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                return parsed if isinstance(parsed, list) else [v]
            except Exception:
                return [s.strip() for s in v.split(",") if s.strip()]
        return v

class CandidateResponse(CandidateBase):
    id: str
    profile_completeness: float
    created_at: datetime
    updated_at: datetime
    skills: List[SkillResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class ResumeParsedData(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    education: Optional[str] = None
    degree: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    tools_and_frameworks: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)
    work_experience: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    career_interests: List[str] = Field(default_factory=list)
    raw_summary: Optional[str] = None

class ResumeResponse(BaseModel):
    id: str
    candidate_id: str
    filename: str
    file_type: str
    uploaded_at: datetime
    parsed_data: Dict[str, Any]
    model_config = ConfigDict(from_attributes=True)
