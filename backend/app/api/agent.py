from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.agents.orchestrator import AgentOrchestrator
from app.tools.registry import TOOL_DEFINITIONS
from app.repositories.memory_repo import MemoryRepository
from app.schemas.agent import ChatRequest, ChatResponse, ToolDefinition

router = APIRouter(prefix="/api/agent", tags=["AI Agent"])

@router.post("/chat", response_model=ChatResponse)
def agent_chat(request: ChatRequest, db: Session = Depends(get_db)):
    orchestrator = AgentOrchestrator(
        db=db,
        candidate_id=request.candidate_id,
        conversation_id=request.conversation_id
    )
    return orchestrator.process_message(request.message)

@router.get("/tools")
def list_agent_tools():
    return {"tools": TOOL_DEFINITIONS}

@router.get("/history/{candidate_id}")
def get_chat_history(candidate_id: str, conversation_id: Optional[str] = Query(None), db: Session = Depends(get_db)):
    repo = MemoryRepository(db)
    conv = repo.get_or_create_conversation(candidate_id, conversation_id)
    messages = repo.get_conversation_history(conv.id, limit=50)
    return {
        "conversation_id": conv.id,
        "title": conv.title,
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "content": m.content,
                "tool_name": m.tool_name,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ]
    }
