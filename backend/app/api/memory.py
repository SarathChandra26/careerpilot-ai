from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.memory_repo import MemoryRepository
from app.schemas.memory import MemoryCreate, MemoryUpdate, MemoryResponse

router = APIRouter(prefix="/api/memory", tags=["Candidate Memory"])

@router.get("/{candidate_id}", response_model=List[MemoryResponse])
def get_memories(
    candidate_id: str,
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    repo = MemoryRepository(db)
    return repo.get_memories(candidate_id, category=category)

@router.post("/{candidate_id}", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
def create_memory(candidate_id: str, memory_in: MemoryCreate, db: Session = Depends(get_db)):
    repo = MemoryRepository(db)
    return repo.add_memory(candidate_id, memory_in)

@router.put("/item/{memory_id}", response_model=MemoryResponse)
def update_memory(memory_id: str, update_in: MemoryUpdate, db: Session = Depends(get_db)):
    repo = MemoryRepository(db)
    mem = repo.update_memory(memory_id, update_in)
    if not mem:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return mem

@router.delete("/item/{memory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    repo = MemoryRepository(db)
    if not repo.delete_memory(memory_id):
        raise HTTPException(status_code=404, detail="Memory item not found")
    return None
