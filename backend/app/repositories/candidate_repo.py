import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.candidate import Candidate, Resume, CandidateSkill, CandidatePreference
from app.schemas.candidate import CandidateCreate, CandidateUpdate, SkillCreate

def calculate_completeness(candidate: Candidate) -> float:
    score = 0.0
    total_weights = 100.0
    
    # Basic Info (30%)
    if candidate.full_name:
        score += 10.0
    if candidate.email:
        score += 10.0
    if candidate.phone:
        score += 10.0
        
    # Education & Experience (25%)
    if candidate.education or candidate.degree:
        score += 15.0
    if candidate.experience_years is not None and candidate.experience_years >= 0:
        score += 10.0
        
    # Skills (25%)
    skill_count = len(candidate.skills) if candidate.skills else 0
    if skill_count >= 5:
        score += 25.0
    elif skill_count > 0:
        score += (skill_count / 5.0) * 25.0
        
    # Preferences (20%)
    roles = json.loads(candidate.preferred_roles or "[]")
    if roles:
        score += 10.0
    if candidate.preferred_work_mode and candidate.preferred_work_mode != "Any":
        score += 5.0
    locations = json.loads(candidate.preferred_locations or "[]")
    if locations:
        score += 5.0
        
    return min(100.0, round(score, 1))

class CandidateRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, candidate_id: str) -> Optional[Candidate]:
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()

    def get_by_email(self, email: str) -> Optional[Candidate]:
        return self.db.query(Candidate).filter(Candidate.email == email).first()

    def get_first_or_default(self) -> Optional[Candidate]:
        return self.db.query(Candidate).order_by(Candidate.created_at.asc()).first()

    def get_all(self, skip: int = 0, limit: int = 20) -> List[Candidate]:
        return self.db.query(Candidate).offset(skip).limit(limit).all()

    def create(self, candidate_in: CandidateCreate) -> Candidate:
        candidate = Candidate(
            full_name=candidate_in.full_name,
            email=candidate_in.email,
            phone=candidate_in.phone,
            education=candidate_in.education,
            degree=candidate_in.degree,
            experience_years=candidate_in.experience_years,
            experience_level=candidate_in.experience_level,
            preferred_roles=json.dumps(candidate_in.preferred_roles),
            preferred_locations=json.dumps(candidate_in.preferred_locations),
            preferred_work_mode=candidate_in.preferred_work_mode,
            salary_expectation_min=candidate_in.salary_expectation_min,
            salary_expectation_max=candidate_in.salary_expectation_max,
            career_interests=json.dumps(candidate_in.career_interests),
        )
        candidate.profile_completeness = calculate_completeness(candidate)
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def update(self, candidate_id: str, candidate_in: CandidateUpdate) -> Optional[Candidate]:
        candidate = self.get_by_id(candidate_id)
        if not candidate:
            return None

        update_data = candidate_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field in ["preferred_roles", "preferred_locations", "career_interests"] and isinstance(value, list):
                setattr(candidate, field, json.dumps(value))
            else:
                setattr(candidate, field, value)

        candidate.profile_completeness = calculate_completeness(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def delete(self, candidate_id: str) -> bool:
        candidate = self.get_by_id(candidate_id)
        if not candidate:
            return False
        self.db.delete(candidate)
        self.db.commit()
        return True

    def add_skill(self, candidate_id: str, skill_in: SkillCreate) -> Optional[CandidateSkill]:
        candidate = self.get_by_id(candidate_id)
        if not candidate:
            return None
            
        existing = (
            self.db.query(CandidateSkill)
            .filter(
                CandidateSkill.candidate_id == candidate_id,
                CandidateSkill.skill_name.ilike(skill_in.skill_name.strip())
            )
            .first()
        )
        if existing:
            existing.proficiency = skill_in.proficiency
            existing.category = skill_in.category
            self.db.commit()
            self.db.refresh(existing)
            return existing

        skill = CandidateSkill(
            candidate_id=candidate_id,
            skill_name=skill_in.skill_name.strip(),
            category=skill_in.category,
            proficiency=skill_in.proficiency,
            verified=skill_in.verified,
        )
        self.db.add(skill)
        candidate.profile_completeness = calculate_completeness(candidate)
        self.db.commit()
        self.db.refresh(skill)
        return skill

    def remove_skill(self, candidate_id: str, skill_id: int) -> bool:
        skill = (
            self.db.query(CandidateSkill)
            .filter(CandidateSkill.candidate_id == candidate_id, CandidateSkill.id == skill_id)
            .first()
        )
        if not skill:
            return False
        self.db.delete(skill)
        candidate = self.get_by_id(candidate_id)
        if candidate:
            candidate.profile_completeness = calculate_completeness(candidate)
        self.db.commit()
        return True

    def save_resume(
        self,
        candidate_id: str,
        filename: str,
        file_path: str,
        file_type: str,
        raw_text: str,
        parsed_data: Dict[str, Any],
    ) -> Resume:
        resume = Resume(
            candidate_id=candidate_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            raw_text=raw_text,
            parsed_data=json.dumps(parsed_data),
        )
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_resumes(self, candidate_id: str) -> List[Resume]:
        return (
            self.db.query(Resume)
            .filter(Resume.candidate_id == candidate_id)
            .order_by(Resume.uploaded_at.desc())
            .all()
        )

    def delete_resume(self, resume_id: str) -> bool:
        resume = self.db.query(Resume).filter(Resume.id == resume_id).first()
        if not resume:
            return False
        self.db.delete(resume)
        self.db.commit()
        return True
