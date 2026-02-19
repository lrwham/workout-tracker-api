import uuid
from datetime import datetime, timezone

from pydantic import BaseModel
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    workouts: Mapped[list["Workout"]] = relationship(back_populates="user")


class WorkoutTemplate(Base):
    __tablename__ = "workout_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    label: Mapped[str] = mapped_column(String)  # "Day B"
    focus: Mapped[str] = mapped_column(String)  # "Lower Body"
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship()
    exercises: Mapped[list["TemplateExercise"]] = relationship(
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="TemplateExercise.position",
    )


class TemplateExercise(Base):
    __tablename__ = "template_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("workout_templates.id"))
    name: Mapped[str] = mapped_column(String)  # "Squat"
    target_weight: Mapped[float] = mapped_column(Float)  # 165
    num_sets: Mapped[int] = mapped_column(Integer)  # 3
    position: Mapped[int] = mapped_column(Integer)  # ordering

    template: Mapped["WorkoutTemplate"] = relationship(back_populates="exercises")


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    date: Mapped[str] = mapped_column(String)
    hash: Mapped[str] = mapped_column(String)

    user: Mapped["User"] = relationship(back_populates="workouts")
    exercises: Mapped[list["Exercise"]] = relationship(
        back_populates="workout", cascade="all, delete-orphan"
    )


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    workout_id: Mapped[int] = mapped_column(ForeignKey("workouts.id"))
    name: Mapped[str] = mapped_column(String)

    workout: Mapped["Workout"] = relationship(back_populates="exercises")
    sets: Mapped[list["WorkoutSet"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan"
    )


class WorkoutSet(Base):
    __tablename__ = "workout_sets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"))
    lbs: Mapped[float | None] = mapped_column(Float, default=None)
    reps: Mapped[int | None] = mapped_column(Integer, default=None)

    exercise: Mapped["Exercise"] = relationship(back_populates="sets")


class ExerciseSubmission(BaseModel):
    name: str
    sets: list["WorkoutSetSubmission"]


class WorkoutSetSubmission(BaseModel):
    lbs: float | None
    reps: int | None


class WorkoutSubmission(BaseModel):
    date: str
    exercises: list[ExerciseSubmission]

class TemplateExerciseCreate(BaseModel):
    name: str
    target_weight: float
    num_sets: int

class TemplateCreate(BaseModel):
    label: str
    focus: str
    exercises: list[TemplateExerciseCreate]

class TemplateExerciseResponse(BaseModel):
    id: int
    name: str
    target_weight: float
    num_sets: int
    position: int

    class Config:
        from_attributes = True

class TemplateResponse(BaseModel):
    id: int
    label: str
    focus: str
    exercises: list[TemplateExerciseResponse]

    class Config:
        from_attributes = True