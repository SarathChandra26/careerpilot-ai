from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.application_repo import ApplicationRepository
from app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
)

router = APIRouter(prefix="/api/applications", tags=["Application Tracker"])

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(candidate_id: str, app_in: ApplicationCreate, db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    app = repo.create(candidate_id, app_in)
    return app

@router.get("/{candidate_id}", response_model=List[ApplicationResponse])
def get_applications(candidate_id: str, status_filter: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    return repo.get_by_candidate(candidate_id, status=status_filter)

@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(application_id: str, app_in: ApplicationUpdate, db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    app = repo.update(application_id, app_in)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(application_id: str, db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    if not repo.delete(application_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return None

# Task endpoints
@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(candidate_id: str, task_in: TaskCreate, db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    return repo.create_task(candidate_id, task_in)

@router.get("/tasks/{candidate_id}", response_model=List[TaskResponse])
def get_tasks(candidate_id: str, is_completed: Optional[bool] = Query(None), db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    return repo.get_tasks_by_candidate(candidate_id, is_completed=is_completed)

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, task_in: TaskUpdate, db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    task = repo.update_task(task_id, task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    repo = ApplicationRepository(db)
    if not repo.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    return None
