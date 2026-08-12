from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from app.shared.schemas import ORM

class TaskIn(BaseModel): title: str = Field(min_length=1); description: str = ""; subject_id: int | None = None; topic_id: int | None = None; due_date: datetime | None = None; completed: bool = False
class TaskOut(ORM): id: int; user_id: int; subject_id: int | None; topic_id: int | None; title: str; description: str; due_date: datetime | None; completed: bool; created_at: datetime
class ReminderIn(BaseModel): title: str = Field(min_length=1); subject_id: int | None = None; topic_id: int | None = None; reminder_datetime: datetime; message: str = ""
class ReminderOut(ORM): id: int; user_id: int; subject_id: int | None; topic_id: int | None; title: str; reminder_datetime: datetime; message: str; created_at: datetime
class StudyPlanItemIn(BaseModel): topic_id: int | None = None; title: str = Field(min_length=1,max_length=220); activity_type: Literal["study","review","flashcards","quiz","mock_exam"] = "study"; scheduled_for: datetime; duration_minutes: int = Field(default=30,ge=5,le=480)
class StudyPlanIn(BaseModel): title: str = Field(min_length=1,max_length=220); exam_id: int | None = None; items: list[StudyPlanItemIn] = []
class AIPlanIn(BaseModel): exam_id: int; available_days: list[int] = Field(default=[0,1,2,3,4,5,6]); daily_minutes: int = Field(default=60,ge=15,le=480)
class PlanItemStatus(BaseModel): status: Literal["planned","completed","skipped","reschedule"]; scheduled_for: datetime | None = None
