from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field

class ExamIn(BaseModel): name: str = Field(min_length=1,max_length=220); subject_id: int; exam_datetime: datetime; topic_ids: list[int] = []; notes: str = ""
class MockExamIn(BaseModel): topic_ids: list[int] = Field(min_length=1); count: int = Field(default=20,ge=5,le=60); question_types: list[Literal["mcq","true_false","essay"]] = Field(default=["mcq","true_false"],min_length=1); difficulty: Literal["easy","medium","hard","mixed"] = "mixed"; time_limit_minutes: int | None = Field(default=None,ge=5,le=300)
class SubmittedAnswer(BaseModel): question_id: int; answer: str
class ExamSubmission(BaseModel): answers: list[SubmittedAnswer]; time_spent_seconds: int | None = Field(default=None,ge=0)
