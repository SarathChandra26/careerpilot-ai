import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.orm import relationship
from app.database.session import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    full_name = Column(String(120), nullable=False)
    email = Column(String(120), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    education = Column(String(255), nullable=True)
    degree = Column(String(120), nullable=True)
    experience_years = Column(Float, default=0.0)
    experience_level = Column(String(50), default="Entry-level")  # Internship, Entry-level, Mid-level, Senior
    preferred_roles = Column(Text, default="[]")  # JSON list
    preferred_locations = Column(Text, default="[]")  # JSON list
    preferred_work_mode = Column(String(50), default="Any")  # Remote, Hybrid, On-site, Any
    salary_expectation_min = Column(Integer, nullable=True)
    salary_expectation_max = Column(Integer, nullable=True)
    career_interests = Column(Text, default="[]")  # JSON list
    profile_completeness = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resumes = relationship("Resume", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    preferences = relationship("CandidatePreference", back_populates="candidate", cascade="all, delete-orphan")
    saved_jobs = relationship("SavedJob", back_populates="candidate", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")
    tasks = relationship("ApplicationTask", back_populates="candidate", cascade="all, delete-orphan")
    memories = relationship("CandidateMemory", back_populates="candidate", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="candidate", cascade="all, delete-orphan")


class Resume(Base):
    __tablename__ = "resumes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf, docx, txt
    raw_text = Column(Text, nullable=False)
    parsed_data = Column(Text, default="{}")  # JSON of extracted info
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="resumes")


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    category = Column(String(80), default="Technical")  # Programming, Frameworks, Tools, Soft Skills, etc.
    proficiency = Column(String(50), default="Intermediate")  # Beginner, Intermediate, Advanced
    verified = Column(Boolean, default=True)

    candidate = relationship("Candidate", back_populates="skills")


class CandidatePreference(Base):
    __tablename__ = "candidate_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True)
    preference_key = Column(String(100), nullable=False, index=True)
    preference_value = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="preferences")
