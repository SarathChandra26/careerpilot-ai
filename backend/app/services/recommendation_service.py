import json
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.candidate import Candidate
from app.models.job import Job
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.repositories.application_repo import ApplicationRepository
from app.matching.scorer import MatchingScorer
from app.schemas.matching import JobMatchResult, RecommendationResponse

class RecommendationService:
    def __init__(self, db: Session):
        self.db = db
        self.cand_repo = CandidateRepository(db)
        self.job_repo = JobRepository(db)
        self.app_repo = ApplicationRepository(db)

    def get_recommendations(
        self, candidate_id: str, limit: int = 10, min_score: float = 30.0
    ) -> RecommendationResponse:
        candidate = self.cand_repo.get_by_id(candidate_id)
        if not candidate:
            return RecommendationResponse(candidate_id=candidate_id, total_recommendations=0, recommendations=[])

        # 1. Fetch all candidate feedback
        feedbacks = self.job_repo.get_feedbacks(candidate_id)
        disliked_job_ids = {fb.job_id for fb in feedbacks if fb.feedback in ["Not relevant", "Not interested"]}
        already_applied_ids = {fb.job_id for fb in feedbacks if fb.feedback == "Already applied"}
        
        # 2. Fetch saved jobs and applications
        saved_jobs = self.job_repo.get_saved_jobs(candidate_id)
        saved_job_ids = {s.job_id for s in saved_jobs}
        
        applications = self.app_repo.get_by_candidate(candidate_id)
        app_status_by_job = {a.job_id: a.status for a in applications}
        for jid in app_status_by_job:
            if app_status_by_job[jid] in ["Applied", "Offer Received", "Rejected"]:
                already_applied_ids.add(jid)

        # 3. Retrieve all candidate jobs
        all_jobs = self.db.query(Job).all()
        scored_results: List[JobMatchResult] = []

        for job in all_jobs:
            # Filter out rejected or already applied opportunities unless specifically requested
            if job.id in disliked_job_ids:
                continue

            # Calculate deterministic match
            match = MatchingScorer.calculate_match(
                candidate=candidate,
                job=job,
                is_saved=(job.id in saved_job_ids),
                application_status=app_status_by_job.get(job.id),
            )

            # Boost score slightly if user marked as Relevant previously
            user_fb = next((fb for fb in feedbacks if fb.job_id == job.id), None)
            if user_fb and user_fb.feedback == "Relevant":
                match.overall_score = min(100.0, match.overall_score + 5.0)

            if match.overall_score >= min_score:
                scored_results.append(match)

        # 4. Sort by overall_score descending
        scored_results.sort(key=lambda x: x.overall_score, reverse=True)
        top_results = scored_results[:limit]

        return RecommendationResponse(
            candidate_id=candidate_id,
            total_recommendations=len(scored_results),
            recommendations=top_results,
        )
