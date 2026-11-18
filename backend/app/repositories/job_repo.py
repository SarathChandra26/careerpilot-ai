from typing import List, Optional, Tuple
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import Session
from app.models.job import Job, JobSkill, SavedJob, RecommendationFeedback
from app.schemas.job import JobCreate, JobUpdate, JobSkillCreate, JobFilterParams
from app.matching.semantic_search import SemanticSearchService

class JobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, job_id: str) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_by_title_and_company(self, title: str, company: str) -> Optional[Job]:
        return (
            self.db.query(Job)
            .filter(
                func.lower(Job.title) == func.lower(title.strip()),
                func.lower(Job.company) == func.lower(company.strip())
            )
            .first()
        )

    def count(self) -> int:
        return self.db.query(Job).count()

    def create(self, job_in: JobCreate) -> Job:
        job = Job(
            company=job_in.company.strip(),
            title=job_in.title.strip(),
            description=job_in.description.strip(),
            role_category=job_in.role_category.strip(),
            experience_level=job_in.experience_level.strip(),
            experience_years_min=job_in.experience_years_min,
            location=job_in.location.strip(),
            work_mode=job_in.work_mode.strip(),
            employment_type=job_in.employment_type.strip(),
            salary_min=job_in.salary_min,
            salary_max=job_in.salary_max,
            salary_currency=job_in.salary_currency,
            application_url=job_in.application_url,
            is_synthetic=job_in.is_synthetic,
            date_posted=job_in.date_posted,
        )
        self.db.add(job)
        self.db.flush()

        for skill_in in job_in.skills:
            skill = JobSkill(
                job_id=job.id,
                skill_name=skill_in.skill_name.strip(),
                is_required=skill_in.is_required,
                importance_weight=skill_in.importance_weight,
            )
            self.db.add(skill)

        self.db.commit()
        self.db.refresh(job)
        return job

    def update(self, job_id: str, job_in: JobUpdate) -> Optional[Job]:
        job = self.get_by_id(job_id)
        if not job:
            return None

        update_data = job_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(job, field, value)

        self.db.commit()
        self.db.refresh(job)
        return job

    def delete(self, job_id: str) -> bool:
        job = self.get_by_id(job_id)
        if not job:
            return False
        self.db.delete(job)
        self.db.commit()
        return True

    def search_and_filter(self, params: JobFilterParams) -> Tuple[List[Job], int]:
        # Check if semantic search can provide ranking
        semantic_ranked_ids: List[str] = []
        if params.query and params.query.strip():
            try:
                search_svc = SemanticSearchService.get_instance()
                sim_results = search_svc.search_similar_jobs(params.query.strip(), top_k=100)
                semantic_ranked_ids = [jid for jid, score in sim_results]
            except Exception:
                semantic_ranked_ids = []

        query = self.db.query(Job)

        if params.query and params.query.strip():
            if semantic_ranked_ids:
                query = query.filter(Job.id.in_(semantic_ranked_ids))
            else:
                raw_q = params.query.strip().lower()
                words = [w for w in raw_q.split() if len(w) > 1 and w not in ["in", "and", "or", "for", "with", "the", "me", "to"]]
                if words:
                    conditions = []
                    for w in words:
                        term = f"%{w}%"
                        conditions.append(func.lower(Job.title).like(term))
                        conditions.append(func.lower(Job.role_category).like(term))
                        conditions.append(func.lower(Job.description).like(term))
                    query = query.filter(or_(*conditions))

        if params.role_category and params.role_category != "All":
            query = query.filter(func.lower(Job.role_category) == func.lower(params.role_category))

        if params.experience_level and params.experience_level != "All":
            query = query.filter(func.lower(Job.experience_level) == func.lower(params.experience_level))

        if params.work_mode and params.work_mode != "All":
            query = query.filter(func.lower(Job.work_mode) == func.lower(params.work_mode))

        if params.location and params.location != "All":
            query = query.filter(func.lower(Job.location).like(f"%{params.location.lower()}%"))

        if params.min_salary:
            query = query.filter(
                or_(
                    Job.salary_max >= params.min_salary,
                    Job.salary_min >= params.min_salary,
                )
            )

        total = query.count()
        jobs = query.all()

        # If semantic ranked IDs exist, preserve semantic ranking order!
        if semantic_ranked_ids:
            rank_map = {jid: idx for idx, jid in enumerate(semantic_ranked_ids)}
            jobs.sort(key=lambda j: rank_map.get(j.id, 9999))
        else:
            jobs.sort(key=lambda j: j.created_at, reverse=True)

        paginated_jobs = jobs[params.offset : params.offset + params.limit]
        return paginated_jobs, total

    def save_job(self, candidate_id: str, job_id: str, notes: Optional[str] = None) -> SavedJob:
        existing = (
            self.db.query(SavedJob)
            .filter(SavedJob.candidate_id == candidate_id, SavedJob.job_id == job_id)
            .first()
        )
        if existing:
            if notes:
                existing.notes = notes
                self.db.commit()
                self.db.refresh(existing)
            return existing

        saved = SavedJob(candidate_id=candidate_id, job_id=job_id, notes=notes)
        self.db.add(saved)
        self.db.commit()
        self.db.refresh(saved)
        return saved

    def remove_saved_job(self, candidate_id: str, job_id: str) -> bool:
        saved = (
            self.db.query(SavedJob)
            .filter(SavedJob.candidate_id == candidate_id, SavedJob.job_id == job_id)
            .first()
        )
        if not saved:
            return False
        self.db.delete(saved)
        self.db.commit()
        return True

    def get_saved_jobs(self, candidate_id: str) -> List[SavedJob]:
        return (
            self.db.query(SavedJob)
            .filter(SavedJob.candidate_id == candidate_id)
            .order_by(SavedJob.saved_at.desc())
            .all()
        )

    def is_job_saved(self, candidate_id: str, job_id: str) -> bool:
        return (
            self.db.query(SavedJob)
            .filter(SavedJob.candidate_id == candidate_id, SavedJob.job_id == job_id)
            .count()
            > 0
        )

    def add_feedback(
        self, candidate_id: str, job_id: str, feedback: str, notes: Optional[str] = None
    ) -> RecommendationFeedback:
        existing = (
            self.db.query(RecommendationFeedback)
            .filter(
                RecommendationFeedback.candidate_id == candidate_id,
                RecommendationFeedback.job_id == job_id,
            )
            .first()
        )
        if existing:
            existing.feedback = feedback
            existing.notes = notes
            self.db.commit()
            self.db.refresh(existing)
            return existing

        fb = RecommendationFeedback(
            candidate_id=candidate_id, job_id=job_id, feedback=feedback, notes=notes
        )
        self.db.add(fb)
        self.db.commit()
        self.db.refresh(fb)
        return fb

    def get_feedbacks(self, candidate_id: str) -> List[RecommendationFeedback]:
        return (
            self.db.query(RecommendationFeedback)
            .filter(RecommendationFeedback.candidate_id == candidate_id)
            .all()
        )
