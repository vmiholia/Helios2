"""
Helios2 Database Setup
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from . import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./helios2.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database tables"""
    models.Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
