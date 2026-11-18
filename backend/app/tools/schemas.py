from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SearchJobsArgs(BaseModel):
    query: Optional[str] = Field(None, description="Search term, title, or keywords e.g. 'AI Engineer', 'Python'")
    role_category: Optional[str] = Field(None, description="Role category filter e.g. 'AI Engineer', 'Software Engineer'")
    experience_level: Optional[str] = Field(None, description="Experience level e.g. 'Internship', 'Entry-level', 'Mid-level'")
    work_mode: Optional[str] = Field(None, description="'Remote', 'Hybrid', 'On-site'")
    location: Optional[str] = Field(None, description="Location filter e.g. 'Remote', 'New York'")
    min_salary: Optional[int] = Field(None, description="Minimum salary expectation")
    limit: int = Field(5, ge=1, le=20, description="Number of job records to return")

class GetCandidateProfileArgs(BaseModel):
    candidate_id: Optional[str] = Field(None, description="ID of the candidate. Defaults to active profile if omitted.")

class UpdateCandidatePreferencesArgs(BaseModel):
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    preferred_roles: Optional[List[str]] = Field(None, description="List of preferred job roles")
    preferred_locations: Optional[List[str]] = Field(None, description="List of preferred locations")
    preferred_work_mode: Optional[str] = Field(None, description="'Remote', 'Hybrid', 'On-site', 'Any'")
    salary_expectation_min: Optional[int] = Field(None, description="Minimum expected salary")
    career_interests: Optional[List[str]] = Field(None, description="List of career focus areas or interests")

class CompareJobWithCandidateArgs(BaseModel):
    job_id: str = Field(..., description="ID of the job to compare against candidate profile")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")

class SaveJobArgs(BaseModel):
    job_id: str = Field(..., description="ID of the job to save")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    notes: Optional[str] = Field(None, description="Optional notes for saving this opportunity")

class RemoveSavedJobArgs(BaseModel):
    job_id: str = Field(..., description="ID of the job to remove from saved list")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")

class GetSavedJobsArgs(BaseModel):
    candidate_id: Optional[str] = Field(None, description="Candidate ID")

class CreateApplicationTaskArgs(BaseModel):
    title: str = Field(..., description="Actionable title for the application preparation task")
    job_id: Optional[str] = Field(None, description="Associated job ID")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    due_date: Optional[str] = Field(None, description="Due date string e.g. '2026-12-01'")
    description: Optional[str] = Field(None, description="Detailed task description")

class GetApplicationTasksArgs(BaseModel):
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    is_completed: Optional[bool] = Field(None, description="Filter by completion status")

class UpdateApplicationStatusArgs(BaseModel):
    job_id: str = Field(..., description="Job ID")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
    status: str = Field(
        ...,
        pattern="^(Interested|Saved|Preparing|Applied|Interview Scheduled|Rejected|Offer Received)$",
        description="Application status"
    )
    notes: Optional[str] = Field(None, description="Notes on status update")

class GenerateInterviewQuestionsArgs(BaseModel):
    job_id: Optional[str] = Field(None, description="Job ID to generate targeted questions for")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")

class IdentifySkillGapsArgs(BaseModel):
    job_id: Optional[str] = Field(None, description="Job ID to inspect skill gaps for")
    candidate_id: Optional[str] = Field(None, description="Candidate ID")
