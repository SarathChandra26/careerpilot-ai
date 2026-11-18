import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.candidate_repo import CandidateRepository
from app.schemas.candidate import (
    CandidateCreate,
    CandidateUpdate,
    CandidateResponse,
    SkillCreate,
    SkillResponse,
)

router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

@router.post("", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
def create_candidate(candidate_in: CandidateCreate, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    existing = repo.get_by_email(candidate_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Candidate with email '{candidate_in.email}' already exists."
        )
    candidate = repo.create(candidate_in)
    return candidate

@router.get("", response_model=List[CandidateResponse])
def list_candidates(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    return repo.get_all(skip=skip, limit=limit)

@router.get("/active", response_model=CandidateResponse)
def get_active_candidate(db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    cand = repo.get_first_or_default()
    if not cand:
        # Create a default initial profile for immediate out-of-the-box exploration
        default_candidate = CandidateCreate(
            full_name="Alex Rivera",
            email="alex.rivera@example.com",
            phone="+1 (555) 234-5678",
            education="Bachelor of Science in Computer Science",
            degree="Bachelor's Degree",
            experience_years=0.5,
            experience_level="Internship",
            preferred_roles=["AI Engineer", "Python Developer", "Machine Learning Engineer"],
            preferred_locations=["Remote", "San Francisco, CA"],
            preferred_work_mode="Remote",
            career_interests=["Large Language Models", "Agentic AI", "Automation"],
        )
        cand = repo.create(default_candidate)
        repo.add_skill(cand.id, SkillCreate(skill_name="Python", category="Programming", proficiency="Advanced"))
        repo.add_skill(cand.id, SkillCreate(skill_name="SQL", category="Databases", proficiency="Intermediate"))
        repo.add_skill(cand.id, SkillCreate(skill_name="Machine Learning", category="AI/ML", proficiency="Intermediate"))
        repo.add_skill(cand.id, SkillCreate(skill_name="n8n", category="Tools", proficiency="Intermediate"))
        repo.add_skill(cand.id, SkillCreate(skill_name="FastAPI", category="Frameworks", proficiency="Beginner"))
        cand = repo.get_by_id(cand.id)
    return cand

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    cand = repo.get_by_id(candidate_id)
    if not cand:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return cand

@router.put("/{candidate_id}", response_model=CandidateResponse)
def update_candidate(candidate_id: str, candidate_in: CandidateUpdate, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    updated = repo.update(candidate_id, candidate_in)
    if not updated:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return updated

@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    if not repo.delete(candidate_id):
        raise HTTPException(status_code=404, detail="Candidate not found")
    return None

@router.post("/{candidate_id}/skills", response_model=SkillResponse)
def add_skill(candidate_id: str, skill_in: SkillCreate, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    skill = repo.add_skill(candidate_id, skill_in)
    if not skill:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return skill

@router.delete("/{candidate_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_skill(candidate_id: str, skill_id: int, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    if not repo.remove_skill(candidate_id, skill_id):
        raise HTTPException(status_code=404, detail="Skill not found")
    return None
