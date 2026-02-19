from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite for now — swap this one line for Postgres later:
# DATABASE_URL = "postgresql://user:password@localhost/workout_tracker"
import os
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./workout_tracker.db"  # default for local dev
)
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite-only; remove for Postgres
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass