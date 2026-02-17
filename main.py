import hashlib
import json

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

API_KEY = "dev-workout-key-123"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


class WorkoutSet(BaseModel):
    lbs: int
    reps: int


class Exercise(BaseModel):
    name: str
    sets: list[WorkoutSet]


class WorkoutSubmission(BaseModel):
    date: str
    exercises: list[Exercise]


@app.post("/submit")
async def submit_workout(
    workout: WorkoutSubmission,
    x_api_key: str = Header(),
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

    json_string = json.dumps(workout.model_dump(), sort_keys=True, separators=(',', ':'))
    hash_digest = hashlib.sha256(json_string.encode()).hexdigest()

    return {"hash": hash_digest}