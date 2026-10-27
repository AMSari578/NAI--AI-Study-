from typing import Literal
from pydantic import BaseModel, Field

class FlashcardRating(BaseModel): rating: Literal["again","hard","good","easy"]
class FlashcardIn(BaseModel): question: str = Field(min_length=1); answer: str = Field(min_length=1)
class ReviewItemIn(BaseModel): topic_id: int; title: str = Field(min_length=1,max_length=220); source_type: str = "manual"; source_id: int | None = None
