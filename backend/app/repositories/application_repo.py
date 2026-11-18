from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationTask
from app.schemas.application import ApplicationCreate, ApplicationUpdate, TaskCreate, TaskUpdate

class ApplicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, application_id: str) -> Optional[Application]:
        return self.db.query(Application).filter(Application.id == application_id).first()

    def get_by_candidate_and_job(self, candidate_id: str, job_id: str) -> Optional[Application]:
        return (
            self.db.query(Application)
            .filter(Application.candidate_id == candidate_id, Application.job_id == job_id)
            .first()
        )

    def get_by_candidate(self, candidate_id: str, status: Optional[str] = None) -> List[Application]:
        query = self.db.query(Application).filter(Application.candidate_id == candidate_id)
        if status and status != "All":
            query = query.filter(Application.status == status)
        return query.order_by(Application.updated_at.desc()).all()

    def create(self, candidate_id: str, app_in: ApplicationCreate) -> Application:
        existing = self.get_by_candidate_and_job(candidate_id, app_in.job_id)
        if existing:
            existing.status = app_in.status
            if app_in.notes:
                existing.notes = app_in.notes
            if app_in.applied_date:
                existing.applied_date = app_in.applied_date
            if app_in.deadline_date:
                existing.deadline_date = app_in.deadline_date
            self.db.commit()
            self.db.refresh(existing)
            return existing

        app = Application(
            candidate_id=candidate_id,
            job_id=app_in.job_id,
            status=app_in.status,
            notes=app_in.notes,
            applied_date=app_in.applied_date,
            deadline_date=app_in.deadline_date,
        )
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        return app

    def update(self, application_id: str, app_in: ApplicationUpdate) -> Optional[Application]:
        app = self.get_by_id(application_id)
        if not app:
            return None

        update_data = app_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(app, field, value)

        self.db.commit()
        self.db.refresh(app)
        return app

    def delete(self, application_id: str) -> bool:
        app = self.get_by_id(application_id)
        if not app:
            return False
        self.db.delete(app)
        self.db.commit()
        return True

    def create_task(self, candidate_id: str, task_in: TaskCreate) -> ApplicationTask:
        task = ApplicationTask(
            candidate_id=candidate_id,
            application_id=task_in.application_id,
            job_id=task_in.job_id,
            title=task_in.title,
            description=task_in.description,
            due_date=task_in.due_date,
            is_completed=task_in.is_completed,
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_tasks_by_candidate(
        self, candidate_id: str, is_completed: Optional[bool] = None
    ) -> List[ApplicationTask]:
        query = self.db.query(ApplicationTask).filter(ApplicationTask.candidate_id == candidate_id)
        if is_completed is not None:
            query = query.filter(ApplicationTask.is_completed == is_completed)
        return query.order_by(ApplicationTask.created_at.desc()).all()

    def get_task_by_id(self, task_id: str) -> Optional[ApplicationTask]:
        return self.db.query(ApplicationTask).filter(ApplicationTask.id == task_id).first()

    def update_task(self, task_id: str, task_in: TaskUpdate) -> Optional[ApplicationTask]:
        task = self.get_task_by_id(task_id)
        if not task:
            return None

        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
            if field == "is_completed":
                task.completed_at = datetime.utcnow() if value else None

        self.db.commit()
        self.db.refresh(task)
        return task

    def delete_task(self, task_id: str) -> bool:
        task = self.get_task_by_id(task_id)
        if not task:
            return False
        self.db.delete(task)
        self.db.commit()
        return True
