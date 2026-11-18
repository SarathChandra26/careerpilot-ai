import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
STORAGE_DIR = BASE_DIR / "storage"
RESUMES_DIR = STORAGE_DIR / "resumes"
CHROMADB_DIR = STORAGE_DIR / "chromadb"

# Ensure directories exist
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
RESUMES_DIR.mkdir(parents=True, exist_ok=True)
CHROMADB_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_DB_PATH = str(STORAGE_DIR / "careerpilot.db").replace("\\", "/")

class Settings(BaseSettings):
    APP_NAME: str = "CareerPilot AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"
    
    # Ollama LLM
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_TIMEOUT_SECONDS: int = 60
    LLM_MAX_RETRIES: int = 2
    
    # Embeddings & Vector Search
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_DB_DIR: str = str(CHROMADB_DIR)
    ENABLE_SEMANTIC_SEARCH: bool = True
    
    # Storage
    RESUME_STORAGE_DIR: str = str(RESUMES_DIR)
    MAX_FILE_SIZE_MB: int = 10
    
    # Server
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8005
    FRONTEND_PORT: int = 8501
    LOG_LEVEL: str = "INFO"
    
    # Agent
    MAX_AGENT_TOOL_STEPS: int = 6

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
