from pydantic import BaseModel

class AnswerIn(BaseModel): question_id: int; answer: str
class AnswerEvaluation(BaseModel):
    answer_id: int; is_correct: bool; overall_evaluation: str
    correct_concepts: list[str] = []; missing_concepts: list[str] = []; incorrect_concepts: list[str] = []
    suggested_answer: str; explanation: str; educational_feedback: bool = True
class StudySessionIn(BaseModel): topic_id: int; material_id: int | None = None; mode: str = "study"
