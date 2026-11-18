import os
import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.config import settings, STORAGE_DIR
from app.database.session import get_db
from app.repositories.candidate_repo import CandidateRepository
from app.services.resume_parser import ResumeParserService
from app.schemas.candidate import ResumeResponse, SkillCreate, CandidateUpdate

router = APIRouter(prefix="/api/resumes", tags=["Resumes"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    candidate_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    repo = CandidateRepository(db)
    candidate = repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported format '{ext}'. Only PDF, DOCX, and TXT files are accepted."
        )

    # Ensure upload directory exists
    upload_dir = STORAGE_DIR / "resumes"
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}_{Path(file.filename).name}"
    save_path = upload_dir / safe_filename

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write resume file: {e}")

    # Check file size (10 MB limit)
    if save_path.stat().st_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_MB}MB.")

    # Extract text and parse
    try:
        raw_text = ResumeParserService.extract_text_from_file(str(save_path), ext)
        parsed_data = ResumeParserService.parse_resume_content(raw_text)
    except Exception as e:
        save_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Failed to parse resume content: {e}")

    # Update candidate profile with extracted information if missing
    update_data = {}
    if parsed_data.full_name and candidate.full_name in ["Candidate", "Alex Rivera", ""]:
        update_data["full_name"] = parsed_data.full_name
    if parsed_data.phone and not candidate.phone:
        update_data["phone"] = parsed_data.phone
    if parsed_data.education and not candidate.education:
        update_data["education"] = parsed_data.education
    if parsed_data.degree and not candidate.degree:
        update_data["degree"] = parsed_data.degree
    if parsed_data.career_interests:
        update_data["career_interests"] = parsed_data.career_interests

    if update_data:
        repo.update(candidate_id, CandidateUpdate(**update_data))

    # Add extracted skills
    for skill_name in parsed_data.skills:
        repo.add_skill(
            candidate_id,
            SkillCreate(skill_name=skill_name, category="Extracted", proficiency="Intermediate")
        )

    # Persist resume record
    resume = repo.save_resume(
        candidate_id=candidate_id,
        filename=file.filename,
        file_path=str(save_path),
        file_type=ext.replace(".", ""),
        raw_text=raw_text,
        parsed_data=parsed_data.model_dump(),
    )

    return ResumeResponse(
        id=resume.id,
        candidate_id=resume.candidate_id,
        filename=resume.filename,
        file_type=resume.file_type,
        uploaded_at=resume.uploaded_at,
        parsed_data=parsed_data.model_dump(),
    )

@router.get("/{candidate_id}/list")
def list_resumes(candidate_id: str, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    resumes = repo.get_resumes(candidate_id)
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "file_type": r.file_type,
            "uploaded_at": r.uploaded_at.isoformat(),
        }
        for r in resumes
    ]

@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(resume_id: str, db: Session = Depends(get_db)):
    repo = CandidateRepository(db)
    if not repo.delete_resume(resume_id):
        raise HTTPException(status_code=404, detail="Resume not found")
    return None
