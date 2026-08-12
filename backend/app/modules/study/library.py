from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models as m
from app.db.session import get_db
from app.shared.dependencies import question_for, topic_for
from app.core.security import current_user

router = APIRouter(tags=["result library"])


def _topic_ids(db: Session, user_id: int) -> list[int]:
    return [row[0] for row in db.query(m.Topic.id).join(m.Subject).filter(m.Subject.user_id == user_id).all()]


@router.get("/results/{result_type}")
def result_library(result_type: str, db=Depends(get_db), user=Depends(current_user)):
    models = {"summaries": m.Summary, "flashcards": m.Flashcard, "concept-maps": m.ConceptMap, "quizzes": m.Quiz, "chats": m.ChatConversation, "notes": m.Note}
    model = models.get(result_type)
    if not model:
        raise HTTPException(404, "Unknown result type")
    result = []
    for subject in db.query(m.Subject).filter(m.Subject.user_id == user.id).order_by(m.Subject.updated_at.desc()).all():
        ids = [topic.id for topic in subject.topics]
        count = db.query(func.count(model.id)).filter(model.topic_id.in_(ids)).scalar() if ids else 0
        latest = db.query(model).filter(model.topic_id.in_(ids)).order_by(model.created_at.desc()).first() if ids else None
        result.append({"id": subject.id, "name": subject.name, "description": subject.description, "topic_count": len(ids), "result_count": count or 0, "latest_topic_id": latest.topic_id if latest else None})
    return result


@router.get("/question-bank")
def question_bank(db=Depends(get_db), user=Depends(current_user)):
    cards = (
        db.query(m.Flashcard, m.Topic, m.Subject)
        .select_from(m.Flashcard)
        .join(m.Topic, m.Flashcard.topic_id == m.Topic.id)
        .join(m.Subject, m.Topic.subject_id == m.Subject.id)
        .filter(m.Subject.user_id == user.id)
        .order_by(m.Flashcard.created_at.desc())
        .all()
    )
    questions = (
        db.query(m.QuizQuestion, m.Quiz, m.Topic, m.Subject)
        .select_from(m.QuizQuestion)
        .join(m.Quiz, m.QuizQuestion.quiz_id == m.Quiz.id)
        .join(m.Topic, m.Quiz.topic_id == m.Topic.id)
        .join(m.Subject, m.Topic.subject_id == m.Subject.id)
        .filter(m.Subject.user_id == user.id)
        .order_by(m.QuizQuestion.id.desc())
        .all()
    )
    result = [{"key": f"flashcard-{card.id}", "id": card.id, "source": "flashcard", "question": card.question, "answer": card.answer, "choices": None, "subject_id": subject.id, "subject_name": subject.name, "topic_id": topic.id, "topic_title": topic.title, "created_at": card.created_at} for card, topic, subject in cards]
    result.extend({"key": f"quiz-{question.id}", "id": question.id, "source": "quiz", "question": question.question, "answer": question.correct_answer, "choices": question.choices, "subject_id": subject.id, "subject_name": subject.name, "topic_id": topic.id, "topic_title": topic.title, "created_at": quiz.created_at} for question, quiz, topic, subject in questions)
    return sorted(result, key=lambda item: item["created_at"], reverse=True)


@router.delete("/question-bank", status_code=204)
def delete_all_bank_questions(db=Depends(get_db), user=Depends(current_user)):
    ids = _topic_ids(db, user.id)
    quiz_ids = [row[0] for row in db.query(m.Quiz.id).filter(m.Quiz.topic_id.in_(ids)).all()] if ids else []
    if quiz_ids: db.query(m.QuizQuestion).filter(m.QuizQuestion.quiz_id.in_(quiz_ids)).delete(synchronize_session=False)
    if ids: db.query(m.Flashcard).filter(m.Flashcard.topic_id.in_(ids)).delete(synchronize_session=False)
    db.commit()


@router.delete("/question-bank/{source}/{question_id}", status_code=204)
def delete_bank_question(source: str, question_id: int, db=Depends(get_db), user=Depends(current_user)):
    if source == "flashcard":
        item = db.query(m.Flashcard).filter(m.Flashcard.id == question_id).first()
        if not item: raise HTTPException(404, "Question not found")
        topic_for(db, item.topic_id, user.id)
    elif source == "quiz": item = question_for(db, question_id, user.id)
    else: raise HTTPException(404, "Unknown question type")
    db.delete(item); db.commit()


@router.get("/summary-bank")
def summary_bank(db=Depends(get_db), user=Depends(current_user)):
    rows = (
        db.query(m.Summary, m.Topic, m.Subject)
        .select_from(m.Summary)
        .join(m.Topic, m.Summary.topic_id == m.Topic.id)
        .join(m.Subject, m.Topic.subject_id == m.Subject.id)
        .filter(m.Subject.user_id == user.id)
        .order_by(m.Summary.created_at.desc())
        .all()
    )
    return [{"id": summary.id, "content": summary.content, "summary_type": summary.summary_type, "language": summary.language, "created_at": summary.created_at, "subject_id": subject.id, "subject_name": subject.name, "topic_id": topic.id, "topic_title": topic.title} for summary, topic, subject in rows]


@router.delete("/summary-bank", status_code=204)
def delete_all_summaries(db=Depends(get_db), user=Depends(current_user)):
    ids = _topic_ids(db, user.id)
    if ids: db.query(m.Summary).filter(m.Summary.topic_id.in_(ids)).delete(synchronize_session=False)
    db.commit()
