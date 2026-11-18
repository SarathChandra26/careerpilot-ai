import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from app.models.job import Job, JobSkill
from app.repositories.job_repo import JobRepository
from app.matching.semantic_search import SemanticSearchService
from app.schemas.job import JobCreate, JobUpdate, JobSkillCreate
from app.core.logging import logger

class JobService:
    def __init__(self, db: Session):
        self.db = db
        self.job_repo = JobRepository(db)
        self.search_service = SemanticSearchService.get_instance()

    def import_from_csv(self, file_path: str) -> Dict[str, Any]:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Job data file not found: {file_path}")

        inserted_count = 0
        skipped_count = 0
        errors = []
        jobs_to_index = []

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row_idx, row in enumerate(reader, 1):
                try:
                    title = row.get("title", "").strip()
                    company = row.get("company", "").strip()
                    if not title or not company:
                        skipped_count += 1
                        continue

                    # Duplicate check
                    existing = self.job_repo.get_by_title_and_company(title, company)
                    if existing:
                        skipped_count += 1
                        continue

                    # Parse skills
                    skills_list = []
                    req_skills = [s.strip() for s in row.get("required_skills", "").split(",") if s.strip()]
                    for s in req_skills:
                        skills_list.append(JobSkillCreate(skill_name=s, is_required=True, importance_weight=1.5))

                    pref_skills = [s.strip() for s in row.get("preferred_skills", "").split(",") if s.strip()]
                    for s in pref_skills:
                        skills_list.append(JobSkillCreate(skill_name=s, is_required=False, importance_weight=1.0))

                    job_in = JobCreate(
                        company=company,
                        title=title,
                        description=row.get("description", f"Opportunity for {title} at {company}"),
                        role_category=row.get("role_category", "Software Engineer"),
                        experience_level=row.get("experience_level", "Entry-level"),
                        experience_years_min=float(row.get("experience_years_min", 0.0) or 0.0),
                        location=row.get("location", "Remote"),
                        work_mode=row.get("work_mode", "Remote"),
                        employment_type=row.get("employment_type", "Full-time"),
                        salary_min=int(float(row.get("salary_min"))) if row.get("salary_min") else None,
                        salary_max=int(float(row.get("salary_max"))) if row.get("salary_max") else None,
                        salary_currency=row.get("salary_currency", "USD"),
                        application_url=row.get("application_url"),
                        is_synthetic=row.get("is_synthetic", "True").lower() in ["true", "1", "yes"],
                        date_posted=row.get("date_posted", "2026-11-10"),
                        skills=skills_list,
                    )

                    job = self.job_repo.create(job_in)
                    all_skills = [s.skill_name for s in skills_list]
                    jobs_to_index.append({
                        "job_id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "description": job.description,
                        "skills": all_skills,
                    })
                    inserted_count += 1

                except Exception as e:
                    errors.append(f"Row {row_idx}: {str(e)}")

        # Efficient batch index
        if jobs_to_index:
            self.search_service.batch_index_jobs(jobs_to_index)

        return {
            "total_inserted": inserted_count,
            "total_skipped_duplicates": skipped_count,
            "errors": errors[:5],
        }

    def add_single_job(self, job_in: JobCreate) -> Job:
        existing = self.job_repo.get_by_title_and_company(job_in.title, job_in.company)
        if existing:
            raise ValueError(f"Job '{job_in.title}' at '{job_in.company}' already exists.")

        job = self.job_repo.create(job_in)
        all_skills = [s.skill_name for s in job_in.skills]
        self.search_service.index_job(job.id, job.title, job.company, job.description, all_skills, rebuild_tfidf=True)
        return job

    def update_job(self, job_id: str, job_update: JobUpdate) -> Optional[Job]:
        job = self.job_repo.update(job_id, job_update)
        if job:
            all_skills = [s.skill_name for s in job.skills]
            self.search_service.index_job(job.id, job.title, job.company, job.description, all_skills, rebuild_tfidf=True)
        return job

    def delete_job(self, job_id: str) -> bool:
        self.search_service.delete_job(job_id)
        return self.job_repo.delete(job_id)

    def warm_search_index(self):
        """Index all jobs in DB on initial startup efficiently in a batch."""
        jobs = self.db.query(Job).all()
        if not jobs:
            return
        jobs_to_index = []
        for j in jobs:
            skills = [s.skill_name for s in j.skills]
            jobs_to_index.append({
                "job_id": j.id,
                "title": j.title,
                "company": j.company,
                "description": j.description,
                "skills": skills,
            })
        self.search_service.batch_index_jobs(jobs_to_index)
        logger.info(f"Warmed semantic search index with {len(jobs)} jobs in batch.")
