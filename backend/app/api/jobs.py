import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.job_repo import JobRepository
from app.services.job_service import JobService
from app.schemas.job import (
    JobCreate,
    JobUpdate,
    JobResponse,
    JobListResponse,
    JobFilterParams,
    SavedJobResponse,
    FeedbackCreate,
    FeedbackResponse,
)

router = APIRouter(prefix="/api/jobs", tags=["Jobs"])

@router.get("", response_model=JobListResponse)
def list_jobs(
    query: Optional[str] = Query(None),
    role_category: Optional[str] = Query(None),
    experience_level: Optional[str] = Query(None),
    work_mode: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    min_salary: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    repo = JobRepository(db)
    offset = (page - 1) * page_size
    params = JobFilterParams(
        query=query,
        role_category=role_category,
        experience_level=experience_level,
        work_mode=work_mode,
        location=location,
        min_salary=min_salary,
        limit=page_size,
        offset=offset,
    )
    jobs, total = repo.search_and_filter(params)
    return JobListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=jobs,
    )

@router.post("", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(job_in: JobCreate, db: Session = Depends(get_db)):
    svc = JobService(db)
    try:
        job = svc.add_single_job(job_in)
        return job
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    job = repo.get_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: str, job_update: JobUpdate, db: Session = Depends(get_db)):
    svc = JobService(db)
    job = svc.update_job(job_id, job_update)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: str, db: Session = Depends(get_db)):
    svc = JobService(db)
    if not svc.delete_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    return None

@router.post("/import/sample")
def import_sample_jobs(db: Session = Depends(get_db)):
    svc = JobService(db)
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "sample_jobs.csv")
    try:
        result = svc.import_from_csv(csv_path)
        return {"message": "Sample job catalogue imported successfully", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{job_id}/save")
def save_job(job_id: str, candidate_id: str = Query(...), notes: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = JobRepository(db)
    saved = repo.save_job(candidate_id, job_id, notes)
    return {"message": "Job saved successfully", "saved_id": saved.id}

@router.delete("/{job_id}/save", status_code=status.HTTP_204_NO_CONTENT)
def remove_saved_job(job_id: str, candidate_id: str = Query(...), db: Session = Depends(get_db)):
    repo = JobRepository(db)
    if not repo.remove_saved_job(candidate_id, job_id):
        raise HTTPException(status_code=404, detail="Saved job not found")
    return None

@router.get("/saved/{candidate_id}")
def get_saved_jobs(candidate_id: str, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    saved = repo.get_saved_jobs(candidate_id)
    return [
        {
            "id": s.id,
            "job_id": s.job_id,
            "title": s.job.title,
            "company": s.job.company,
            "location": s.job.location,
            "work_mode": s.job.work_mode,
            "salary": f"${s.job.salary_min:,} - ${s.job.salary_max:,}" if s.job.salary_min and s.job.salary_max else "Competitive",
            "saved_at": s.saved_at.isoformat(),
            "notes": s.notes,
        }
        for s in saved
    ]

@router.post("/{job_id}/feedback")
def submit_feedback(job_id: str, candidate_id: str, fb_in: FeedbackCreate, db: Session = Depends(get_db)):
    repo = JobRepository(db)
    fb = repo.add_feedback(candidate_id, job_id, fb_in.feedback, fb_in.notes)
    return {"message": "Feedback recorded", "feedback": fb.feedback}
