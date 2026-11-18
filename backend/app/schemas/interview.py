from typing import List, Optional
from pydantic import BaseModel, Field

class InterviewQuestion(BaseModel):
    category: str = Field(..., description="Technical, Project-based, Behavioral, or Situational")
    question: str
    why_asked: str
    suggested_answer_framework: str
    key_skills_evaluated: List[str] = Field(default_factory=list)

class InterviewGenerateRequest(BaseModel):
    candidate_id: str
    job_id: str

class InterviewResponse(BaseModel):
    candidate_id: str
    job_id: str
    job_title: str
    company: str
    questions: List[InterviewQuestion] = Field(default_factory=list)
    preparation_checklist: List[str] = Field(default_factory=list)
    source: str
    disclaimer: str = (
        "These questions and checklist items are AI-assisted preparation suggestions based on role "
        "requirements and candidate background. They do not represent official proprietary company questions."
    )
