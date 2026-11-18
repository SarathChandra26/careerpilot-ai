from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class MemoryCreate(BaseModel):
    category: str = Field(..., max_length=80)
    memory_key: str = Field(..., min_length=1, max_length=100)
    memory_value: str = Field(..., min_length=1)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = Field(default="conversation")

class MemoryUpdate(BaseModel):
    memory_value: str = Field(..., min_length=1)
    confidence: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)

class MemoryResponse(BaseModel):
    id: str
    candidate_id: str
    category: str
    memory_key: str
    memory_value: str
    confidence: float
    source: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    sender: str = Field(..., pattern="^(user|assistant|system|tool)$")
    content: str
    tool_name: Optional[str] = None
    tool_arguments: Optional[str] = None
    tool_result: Optional[str] = None

class ChatMessageResponse(ChatMessageCreate):
    id: str
    conversation_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationResponse(BaseModel):
    id: str
    candidate_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)
