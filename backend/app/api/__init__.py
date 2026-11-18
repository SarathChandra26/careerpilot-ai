from fastapi import APIRouter
from app.api.candidates import router as candidates_router
from app.api.resumes import router as resumes_router
from app.api.jobs import router as jobs_router
from app.api.matching import router as matching_router
from app.api.agent import router as agent_router
from app.api.memory import router as memory_router
from app.api.applications import router as applications_router
from app.api.interview import router as interview_router
from app.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(candidates_router)
api_router.include_router(resumes_router)
api_router.include_router(jobs_router)
api_router.include_router(matching_router)
api_router.include_router(agent_router)
api_router.include_router(memory_router)
api_router.include_router(applications_router)
api_router.include_router(interview_router)

__all__ = ["api_router"]
