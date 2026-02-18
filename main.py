import hashlib
import json

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

# ---------------------------------------------------------------------------
# Database setup
# ---------------------------------------------------------------------------

DATABASE_URL = "sqlite:///./workout_tracker.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite only — remove for Postgres
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class WorkoutRecord(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    hash = Column(String, nullable=False)
    exercises = relationship(
        "ExerciseRecord", back_populates="workout", cascade="all, delete-orphan"
    )


class ExerciseRecord(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    name = Column(String, nullable=False)
    workout = relationship("WorkoutRecord", back_populates="exercises")
    sets = relationship(
        "WorkoutSetRecord", back_populates="exercise", cascade="all, delete-orphan"
    )


class WorkoutSetRecord(Base):
    __tablename__ = "workout_sets"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    lbs = Column(Integer, nullable=False)
    reps = Column(Integer, nullable=False)
    exercise = relationship("ExerciseRecord", back_populates="sets")


# Create tables on startup
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# App & middleware
# ---------------------------------------------------------------------------

app = FastAPI()

API_KEY = "dev-workout-key-123"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# ---------------------------------------------------------------------------
# Pydantic schemas (unchanged)
# ---------------------------------------------------------------------------

class WorkoutSet(BaseModel):
    lbs: int
    reps: int


class Exercise(BaseModel):
    name: str
    sets: list[WorkoutSet]


class WorkoutSubmission(BaseModel):
    date: str
    exercises: list[Exercise]


# ---------------------------------------------------------------------------
# DB session dependency
# ---------------------------------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/submit")
async def submit_workout(
    workout: WorkoutSubmission,
    x_api_key: str = Header(),
    db: Session = Depends(get_db),
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Hashing logic — unchanged from original
    json_string = json.dumps(workout.model_dump(), sort_keys=True, separators=(',', ':'))
    hash_digest = hashlib.sha256(json_string.encode()).hexdigest()

    # Persist to database
    db_workout = WorkoutRecord(date=workout.date, hash=hash_digest)
    for exercise in workout.exercises:
        db_exercise = ExerciseRecord(name=exercise.name)
        for s in exercise.sets:
            db_exercise.sets.append(WorkoutSetRecord(lbs=s.lbs, reps=s.reps))
        db_workout.exercises.append(db_exercise)

    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)

    return {"hash": hash_digest, "id": db_workout.id}