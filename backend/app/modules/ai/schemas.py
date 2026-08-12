from typing import Literal
from pydantic import BaseModel, Field

class ChatIn(BaseModel):
    topic_id: int; message: str = Field(min_length=1); conversation_id: int | None = None
    mode: Literal["ask", "teach", "review", "quiz"] = "ask"
    action: Literal["simplify", "example", "break_down", "quiz", "dont_understand"] | None = None
    material_id: int | None = None; page_number: int | None = Field(default=None, ge=1)
    selected_text: str | None = Field(default=None, max_length=12000)
class GenerateIn(BaseModel): topic_id: int; material_id: int | None = None; source: str = "all"; count: int = Field(default=10, ge=1, le=20); quiz_type: str = "mcq"; summary_type: Literal["simple","detailed","key_points","exam_review","memorize"] = "simple"; language: Literal["english","arabic"] = "english"
class NoteAIIn(BaseModel): action: Literal["summarize","organize","explain","key_points","flashcards","quiz"]
class ContextActionIn(BaseModel):
    topic_id: int; action: Literal["explain","simplify","summarize","create_flashcard","add_to_notes","quiz"]
    selected_text: str = Field(min_length=1,max_length=12000); material_id: int | None = None
    page_number: int | None = Field(default=None,ge=1)
