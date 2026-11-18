from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.memory import CandidateMemory, Conversation, ConversationMessage
from app.schemas.memory import MemoryCreate, MemoryUpdate, ChatMessageCreate

class MemoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_memory(self, candidate_id: str, memory_in: MemoryCreate) -> CandidateMemory:
        # Check if memory with same candidate_id and key exists
        existing = (
            self.db.query(CandidateMemory)
            .filter(
                CandidateMemory.candidate_id == candidate_id,
                CandidateMemory.memory_key == memory_in.memory_key.strip().lower(),
            )
            .first()
        )
        if existing:
            existing.memory_value = memory_in.memory_value.strip()
            existing.category = memory_in.category
            existing.confidence = memory_in.confidence
            existing.source = memory_in.source
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing

        mem = CandidateMemory(
            candidate_id=candidate_id,
            category=memory_in.category,
            memory_key=memory_in.memory_key.strip().lower(),
            memory_value=memory_in.memory_value.strip(),
            confidence=memory_in.confidence,
            source=memory_in.source,
        )
        self.db.add(mem)
        self.db.commit()
        self.db.refresh(mem)
        return mem

    def get_memories(self, candidate_id: str, category: Optional[str] = None) -> List[CandidateMemory]:
        query = self.db.query(CandidateMemory).filter(CandidateMemory.candidate_id == candidate_id)
        if category:
            query = query.filter(CandidateMemory.category == category)
        return query.order_by(CandidateMemory.updated_at.desc()).all()

    def get_memory_by_id(self, memory_id: str) -> Optional[CandidateMemory]:
        return self.db.query(CandidateMemory).filter(CandidateMemory.id == memory_id).first()

    def update_memory(self, memory_id: str, update_in: MemoryUpdate) -> Optional[CandidateMemory]:
        mem = self.get_memory_by_id(memory_id)
        if not mem:
            return None
        mem.memory_value = update_in.memory_value.strip()
        if update_in.confidence is not None:
            mem.confidence = update_in.confidence
        mem.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(mem)
        return mem

    def delete_memory(self, memory_id: str) -> bool:
        mem = self.get_memory_by_id(memory_id)
        if not mem:
            return False
        self.db.delete(mem)
        self.db.commit()
        return True

    def get_all_context(self, candidate_id: str) -> Dict[str, Any]:
        memories = self.get_memories(candidate_id)
        context = {
            "career_preferences": {},
            "preferred_technologies": [],
            "preferred_roles": [],
            "preferred_locations": [],
            "career_goals": [],
            "other": {},
        }
        for m in memories:
            if m.category == "preferred_technology":
                context["preferred_technologies"].append(m.memory_value)
            elif m.category == "preferred_role":
                context["preferred_roles"].append(m.memory_value)
            elif m.category == "preferred_location":
                context["preferred_locations"].append(m.memory_value)
            elif m.category == "career_goal":
                context["career_goals"].append(m.memory_value)
            elif m.category == "career_preference":
                context["career_preferences"][m.memory_key] = m.memory_value
            else:
                context["other"][m.memory_key] = m.memory_value
        return context

    # Conversation methods
    def get_or_create_conversation(self, candidate_id: str, conversation_id: Optional[str] = None) -> Conversation:
        if conversation_id:
            conv = (
                self.db.query(Conversation)
                .filter(Conversation.id == conversation_id, Conversation.candidate_id == candidate_id)
                .first()
            )
            if conv:
                return conv

        # Find latest or create new
        latest = (
            self.db.query(Conversation)
            .filter(Conversation.candidate_id == candidate_id)
            .order_by(Conversation.updated_at.desc())
            .first()
        )
        if latest:
            return latest

        new_conv = Conversation(candidate_id=candidate_id, title="Career Assistant Chat")
        self.db.add(new_conv)
        self.db.commit()
        self.db.refresh(new_conv)
        return new_conv

    def add_message(self, conversation_id: str, message_in: ChatMessageCreate) -> ConversationMessage:
        msg = ConversationMessage(
            conversation_id=conversation_id,
            sender=message_in.sender,
            content=message_in.content,
            tool_name=message_in.tool_name,
            tool_arguments=message_in.tool_arguments,
            tool_result=message_in.tool_result,
        )
        self.db.add(msg)
        conv = self.db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if conv:
            conv.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_conversation_history(self, conversation_id: str, limit: int = 20) -> List[ConversationMessage]:
        return (
            self.db.query(ConversationMessage)
            .filter(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
            .all()
        )[::-1]  # Return in chronological order
