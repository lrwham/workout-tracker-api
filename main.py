import hashlib
import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import get_current_user, get_db, verify_password, create_access_token
from models import Exercise, Workout, WorkoutSet, WorkoutSubmission, User
from database import Base, engine, SessionLocal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

Base.metadata.create_all(bind=engine)

@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/submit")
async def submit_workout(
    workout: WorkoutSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ):

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