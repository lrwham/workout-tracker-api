import hashlib
import json

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from models import Exercise, Workout, WorkoutSet, WorkoutSubmission
from database import Base, engine, SessionLocal

app = FastAPI()

API_KEY = "dev-workout-key-123"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
    db_workout = Workout(date=workout.date, hash=hash_digest)
    for exercise in workout.exercises:
        db_exercise = Exercise(name=exercise.name)
        for s in exercise.sets:
            db_exercise.sets.append(WorkoutSet(lbs=s.lbs, reps=s.reps))
        db_workout.exercises.append(db_exercise)

    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)

    return {"hash": hash_digest, "id": db_workout.id}