import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company = Column(String(150), nullable=False, index=True)
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=False)
    role_category = Column(String(100), nullable=False, index=True)  # e.g., AI Engineer, Data Analyst
    experience_level = Column(String(50), default="Entry-level")  # Internship, Entry-level, Mid-level, Senior
    experience_years_min = Column(Float, default=0.0)
    location = Column(String(150), default="Remote")
    work_mode = Column(String(50), default="Remote")  # Remote, Hybrid, On-site
    employment_type = Column(String(50), default="Full-time")  # Full-time, Part-time, Internship, Contract
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="USD")
    application_url = Column(String(500), nullable=True)
    is_synthetic = Column(Boolean, default=True)  # Clearly identifies demonstration data
    date_posted = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    saved_by = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    feedbacks = relationship("RecommendationFeedback", back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    is_required = Column(Boolean, default=True)  # True = required, False = preferred
    importance_weight = Column(Float, default=1.0)

    job = relationship("Job", back_populates="skills")


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    saved_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="saved_jobs")
    job = relationship("Job", back_populates="saved_by")


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    feedback = Column(String(50), nullable=False)  # Relevant, Not relevant, Already applied, Not interested
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    job = relationship("Job", back_populates="feedbacks")
