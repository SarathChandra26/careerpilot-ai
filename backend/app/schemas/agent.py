from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class ToolExecutionStep(BaseModel):
    tool: str
    arguments: Dict[str, Any]
    status: str  # SUCCESS, FAILED, BLOCKED
    result: Any
    duration_ms: float = 0.0
    error: Optional[str] = None

class ChatRequest(BaseModel):
    candidate_id: str
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    conversation_id: str
    message: str
    tools_called: List[ToolExecutionStep] = Field(default_factory=list)
    llm_source: str  # "Ollama (llama3.2:3b)" or "Deterministic Fallback Engine"
    memory_extracted: Optional[List[Dict[str, str]]] = None

class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
