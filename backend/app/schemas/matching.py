from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from app.schemas.job import JobResponse

class MatchBreakdown(BaseModel):
    required_skill_overlap_ratio: float
    preferred_skill_overlap_ratio: float
    experience_compatibility_ratio: float
    role_relevance_ratio: float
    work_mode_compatibility_ratio: float
    location_compatibility_ratio: float
    career_interest_ratio: float
    formula_weights: Dict[str, float]

class JobMatchResult(BaseModel):
    job: JobResponse
    overall_score: float = Field(..., ge=0.0, le=100.0)
    matched_required_skills: List[str] = Field(default_factory=list)
    matched_preferred_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    experience_compatible: bool
    location_compatible: bool
    work_mode_compatible: bool
    breakdown: MatchBreakdown
    explanation: str
    is_saved: bool = False
    application_status: Optional[str] = None
    disclaimer: str = "Match score represents estimated profile alignment and does not guarantee interview or hiring selection."

class RecommendationResponse(BaseModel):
    candidate_id: str
    total_recommendations: int
    recommendations: List[JobMatchResult]

class SkillGapResponse(BaseModel):
    candidate_id: str
    job_id: str
    job_title: str
    company: str
    overall_match_score: float
    missing_required_skills: List[str]
    missing_preferred_skills: List[str]
    recommended_learning_topics: List[str]
    detailed_guidance: str
