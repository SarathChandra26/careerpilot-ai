from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.candidate_repo import CandidateRepository
from app.repositories.job_repo import JobRepository
from app.matching.scorer import MatchingScorer
from app.matching.skill_gap import SkillGapService
from app.matching.semantic_search import SemanticSearchService
from app.services.recommendation_service import RecommendationService
from app.schemas.matching import (
    JobMatchResult,
    RecommendationResponse,
    SkillGapResponse,
)

router = APIRouter(prefix="/api/matching", tags=["Matching & Recommendations"])

@router.get("/{candidate_id}/recommendations", response_model=RecommendationResponse)
def get_recommendations(
    candidate_id: str,
    limit: int = Query(10, ge=1, le=50),
    min_score: float = Query(30.0, ge=0.0, le=100.0),
    db: Session = Depends(get_db)
):
    rec_service = RecommendationService(db)
    return rec_service.get_recommendations(candidate_id, limit=limit, min_score=min_score)

@router.get("/{candidate_id}/compare/{job_id}", response_model=JobMatchResult)
def compare_candidate_with_job(candidate_id: str, job_id: str, db: Session = Depends(get_db)):
    cand_repo = CandidateRepository(db)
    job_repo = JobRepository(db)

    candidate = cand_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    is_saved = job_repo.is_job_saved(candidate_id, job_id)
    result = MatchingScorer.calculate_match(candidate, job, is_saved=is_saved)
    return result

@router.get("/{candidate_id}/skill-gaps/{job_id}", response_model=SkillGapResponse)
def get_skill_gaps(candidate_id: str, job_id: str, db: Session = Depends(get_db)):
    cand_repo = CandidateRepository(db)
    job_repo = JobRepository(db)

    candidate = cand_repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    job = job_repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return SkillGapService.analyze_skill_gap(candidate, job)

@router.get("/semantic-search")
def semantic_search(query: str = Query(..., min_length=2), top_k: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    search_svc = SemanticSearchService.get_instance()
    results = search_svc.search_similar_jobs(query, top_k=top_k)
    job_repo = JobRepository(db)

    output = []
    for jid, score in results:
        j = job_repo.get_by_id(jid)
        if j:
            output.append({
                "job_id": j.id,
                "title": j.title,
                "company": j.company,
                "role_category": j.role_category,
                "location": j.location,
                "work_mode": j.work_mode,
                "similarity_score": score,
            })
    return {"query": query, "total": len(output), "results": output}
