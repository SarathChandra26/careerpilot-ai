from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings, STORAGE_DIR

db_url = settings.DATABASE_URL
if db_url.startswith("sqlite:///") and (":/" not in db_url[10:] and ":\\" not in db_url[10:]):
    # Relative sqlite path: resolve to STORAGE_DIR
    raw_path = db_url.replace("sqlite:///", "").replace("./", "")
    abs_path = (STORAGE_DIR / Path(raw_path).name).resolve()
    clean_path = str(abs_path).replace("\\", "/")
    db_url = f"sqlite:///{clean_path}"

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if "sqlite" in db_url else {},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    import app.models  # Ensure all models are registered with Base
    Base.metadata.create_all(bind=engine)
