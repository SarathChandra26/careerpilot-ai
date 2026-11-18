from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.services.interview_service import InterviewService
from app.schemas.interview import InterviewGenerateRequest, InterviewResponse

router = APIRouter(prefix="/api/interview", tags=["Interview Preparation"])

@router.post("/generate", response_model=InterviewResponse)
def generate_interview(request: InterviewGenerateRequest, db: Session = Depends(get_db)):
    svc = InterviewService(db)
    try:
        return svc.generate_interview_prep(request.candidate_id, request.job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Interview generation error: {e}")
