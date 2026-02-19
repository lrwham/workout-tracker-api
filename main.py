import hashlib
import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from auth import get_current_user, get_db, verify_password, create_access_token
from models import (
    Exercise,
    Workout,
    WorkoutSet,
    WorkoutSubmission,
    User,
    TemplateCreate,
    TemplateExerciseCreate,
    TemplateExercise,
    TemplateResponse,
    WorkoutTemplate,
)
from database import Base, engine, SessionLocal

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://localhost:3000","http://localhost:8000"],
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
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
    json_string = json.dumps(
        workout.model_dump(), sort_keys=True, separators=(",", ":")
    )
    hash_digest = hashlib.sha256(json_string.encode()).hexdigest()

    # Persist to database
    db_workout = Workout(date=workout.date, hash=hash_digest, user_id=current_user.id)

    for exercise in workout.exercises:
        db_exercise = Exercise(name=exercise.name)
        for s in exercise.sets:
            db_exercise.sets.append(WorkoutSet(lbs=s.lbs, reps=s.reps))
        db_workout.exercises.append(db_exercise)

    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)

    return {"hash": hash_digest, "id": db_workout.id}


@app.post("/templates", response_model=TemplateResponse, status_code=201)
async def create_template(
    template: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_template = WorkoutTemplate(
        user_id=current_user.id,
        label=template.label,
        focus=template.focus,
    )
    for i, exercise in enumerate(template.exercises):
        db_template.exercises.append(
            TemplateExercise(
                name=exercise.name,
                target_weight=exercise.target_weight,
                num_sets=exercise.num_sets,
                position=i,
            )
        )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@app.get("/templates", response_model=list[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    templates = (
        db.query(WorkoutTemplate)
        .filter(WorkoutTemplate.user_id == current_user.id)
        .all()
    )
    return templates


@app.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(WorkoutTemplate)
        .filter(
            WorkoutTemplate.id == template_id,
            WorkoutTemplate.user_id == current_user.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@app.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    template = (
        db.query(WorkoutTemplate)
        .filter(
            WorkoutTemplate.id == template_id,
            WorkoutTemplate.user_id == current_user.id,
        )
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    db.delete(template)
    db.commit()
    return {"detail": "Template deleted successfully"}
