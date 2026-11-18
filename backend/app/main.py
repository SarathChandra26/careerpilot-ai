import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.session import init_db, SessionLocal
from app.api import api_router
from app.services.job_service import JobService
from app.repositories.job_repo import JobRepository
from app.repositories.candidate_repo import CandidateRepository
from app.schemas.candidate import CandidateCreate, SkillCreate
from app.core.logging import logger

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "CareerPilot AI: A local, agentic AI career assistant featuring candidate memory, "
        "deterministic profile-job matching, skill gap discovery, interview preparation, "
        "and job application management."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for Streamlit and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

@app.on_event("startup")
def on_startup():
    logger.info("Initializing CareerPilot database...")
    init_db()

    # Seed sample jobs and active candidate if database is fresh
    db = SessionLocal()
    try:
        job_repo = JobRepository(db)
        if job_repo.count() == 0:
            logger.info("No jobs found in database. Ingesting sample jobs dataset...")
            job_svc = JobService(db)
            csv_path = Path(__file__).resolve().parent.parent.parent / "data" / "sample_jobs.csv"
            if csv_path.exists():
                res = job_svc.import_from_csv(str(csv_path))
                logger.info(f"Ingested {res['total_inserted']} sample jobs.")
            else:
                logger.warning(f"Sample jobs CSV not found at {csv_path}")

        # Ensure a default active candidate profile exists
        cand_repo = CandidateRepository(db)
        if not cand_repo.get_first_or_default():
            logger.info("Creating default exploration candidate profile...")
            default_cand = CandidateCreate(
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
            cand = cand_repo.create(default_cand)
            cand_repo.add_skill(cand.id, SkillCreate(skill_name="Python", category="Programming", proficiency="Advanced"))
            cand_repo.add_skill(cand.id, SkillCreate(skill_name="SQL", category="Databases", proficiency="Intermediate"))
            cand_repo.add_skill(cand.id, SkillCreate(skill_name="Machine Learning", category="AI/ML", proficiency="Intermediate"))
            cand_repo.add_skill(cand.id, SkillCreate(skill_name="n8n", category="Tools", proficiency="Intermediate"))
            cand_repo.add_skill(cand.id, SkillCreate(skill_name="FastAPI", category="Frameworks", proficiency="Beginner"))

        # Warm search index
        job_svc = JobService(db)
        job_svc.warm_search_index()
    finally:
        db.close()

    logger.info("CareerPilot AI Backend started successfully.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=settings.DEBUG)
