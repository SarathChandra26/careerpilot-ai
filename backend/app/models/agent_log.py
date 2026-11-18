import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Text
from app.database.session import Base

class AgentToolLog(Base):
    __tablename__ = "agent_tool_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), nullable=True, index=True)
    conversation_id = Column(String(36), nullable=True, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    arguments = Column(Text, nullable=False)  # JSON string
    execution_status = Column(String(50), nullable=False)  # SUCCESS, FAILED, BLOCKED
    execution_duration_ms = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    result_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
