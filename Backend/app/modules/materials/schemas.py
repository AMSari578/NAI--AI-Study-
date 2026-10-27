from datetime import datetime
from pydantic import BaseModel, Field
from app.shared.schemas import ORM

class SubjectIn(BaseModel): name: str = Field(min_length=1, max_length=160); description: str = ""; icon: str = "book"; color: str = "#3B82F6"
class SubjectOut(ORM): id: int; name: str; description: str; icon: str = "book"; color: str = "#3B82F6"; created_at: datetime; updated_at: datetime; last_studied_at: datetime | None; topic_count: int = 0
class TopicIn(BaseModel): title: str = Field(min_length=1, max_length=200); description: str = ""
class TopicOut(ORM): id: int; subject_id: int; title: str; description: str; created_at: datetime; updated_at: datetime; last_opened_at: datetime | None
class TextMaterialIn(BaseModel): title: str = Field(min_length=1, max_length=255); content: str = Field(min_length=1)
class MaterialOut(ORM): id: int; topic_id: int; file_name: str; file_type: str; extracted_text: str; created_at: datetime
class NoteIn(BaseModel): title: str = Field(min_length=1, max_length=200); content: str = Field(min_length=1)
class NoteOut(ORM): id: int; topic_id: int; title: str; content: str; created_at: datetime; updated_at: datetime
