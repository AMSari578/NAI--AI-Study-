from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pypdf import PdfReader
from sqlalchemy import func

from app import models as m
from app.modules.materials import schemas as s
from app.core.config import BASE_DIR, settings
from app.db.session import get_db
from app.shared.dependencies import material_for, note_for, subject_for, topic_for
from app.core.security import current_user
from app.modules.study.service import list_subjects

router = APIRouter(tags=["study content"])

ALLOWED_UPLOADS = {
    "application/pdf": "pdf",
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "text/plain": "txt",
}


@router.get("/search", tags=["search"])
def search(q: str = Query(min_length=2, max_length=200), db=Depends(get_db), user=Depends(current_user)):
    like = f"%{q}%"
    results = []
    for item in db.query(m.Subject).filter(m.Subject.user_id == user.id, m.Subject.name.ilike(like)).limit(20):
        results.append({"type": "subject", "title": item.name, "snippet": item.description, "href": f"/subjects/{item.id}"})
    for item in db.query(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, (m.Topic.title.ilike(like) | m.Topic.description.ilike(like))).limit(30):
        results.append({"type": "topic", "title": item.title, "snippet": item.description, "href": f"/topics/{item.id}"})
    for item in db.query(m.StudyMaterial).join(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, (m.StudyMaterial.file_name.ilike(like) | m.StudyMaterial.extracted_text.ilike(like))).limit(30):
        results.append({"type": "material", "title": item.file_name, "snippet": _search_snippet(item.extracted_text, q), "href": f"/materials/{item.id}"})
    for item in db.query(m.Note).join(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, (m.Note.title.ilike(like) | m.Note.content.ilike(like))).limit(30):
        results.append({"type": "note", "title": item.title, "snippet": _search_snippet(item.content, q), "href": f"/topics/{item.topic_id}?tab=notes"})
    for item in db.query(m.Flashcard).join(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, (m.Flashcard.question.ilike(like) | m.Flashcard.answer.ilike(like))).limit(30):
        results.append({"type": "flashcard", "title": item.question, "snippet": item.answer, "href": f"/topics/{item.topic_id}?tab=flashcards"})
    for item in db.query(m.QuizQuestion).join(m.Quiz).join(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, m.QuizQuestion.question.ilike(like)).limit(30):
        results.append({"type": "quiz", "title": item.question, "snippet": item.explanation, "href": f"/topics/{item.quiz.topic_id if hasattr(item, 'quiz') else ''}?tab=quiz"})
    return results[:100]


def _search_snippet(text: str, query: str):
    value = str(text or "")
    index = value.casefold().find(query.casefold())
    start = max(0, index - 90) if index >= 0 else 0
    return value[start:start + 260]


@router.get("/subjects")
def subjects(db=Depends(get_db), user=Depends(current_user)):
    return list_subjects(db, user.id)


@router.post("/subjects", response_model=s.SubjectOut, status_code=201)
def create_subject(body: s.SubjectIn, db=Depends(get_db), user=Depends(current_user)):
    subject = m.Subject(user_id=user.id, **body.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.get("/subjects/{subject_id}")
def get_subject(subject_id: int, db=Depends(get_db), user=Depends(current_user)):
    subject = subject_for(db, subject_id, user.id)
    topic_ids = [topic.id for topic in subject.topics]
    topic_names = {topic.id: topic.title for topic in subject.topics}
    summaries = db.query(m.Summary).filter(m.Summary.topic_id.in_(topic_ids)).order_by(m.Summary.created_at.desc()).all() if topic_ids else []
    quizzes = db.query(m.Quiz).filter(m.Quiz.topic_id.in_(topic_ids)).order_by(m.Quiz.created_at.desc()).all() if topic_ids else []
    materials = db.query(m.StudyMaterial).filter(m.StudyMaterial.topic_id.in_(topic_ids)).order_by(m.StudyMaterial.created_at.desc()).all() if topic_ids else []
    notes = db.query(m.Note).filter(m.Note.topic_id.in_(topic_ids)).order_by(m.Note.updated_at.desc()).all() if topic_ids else []
    reminders = db.query(m.Reminder).filter(m.Reminder.user_id == user.id).order_by(m.Reminder.reminder_datetime).all()
    reminders = [item for item in reminders if item.subject_id == subject.id or item.topic_id in topic_ids]
    return {
        "subject": s.SubjectOut.model_validate(subject),
        "topics": [
            {
                **s.TopicOut.model_validate(topic).model_dump(),
                "material_count": len(topic.materials),
                "summary_count": db.query(func.count(m.Summary.id)).filter(m.Summary.topic_id == topic.id).scalar() or 0,
                "question_count": db.query(func.count(m.QuizQuestion.id)).join(m.Quiz, m.QuizQuestion.quiz_id == m.Quiz.id).filter(m.Quiz.topic_id == topic.id).scalar() or 0,
            }
            for topic in subject.topics
        ],
        "summaries": [{"id": item.id, "topic_id": item.topic_id, "topic_title": topic_names.get(item.topic_id, ""), "content": item.content, "summary_type": item.summary_type, "language": item.language, "created_at": item.created_at} for item in summaries],
        "quizzes": [{"id": item.id, "topic_id": item.topic_id, "topic_title": topic_names.get(item.topic_id, ""), "quiz_type": item.quiz_type, "question_count": len(item.questions), "created_at": item.created_at} for item in quizzes],
        "materials": [{**s.MaterialOut.model_validate(item).model_dump(), "topic_title": topic_names.get(item.topic_id, "")} for item in materials],
        "notes": [{**s.NoteOut.model_validate(item).model_dump(), "topic_title": topic_names.get(item.topic_id, "")} for item in notes],
        "reminders": reminders,
    }


@router.put("/subjects/{subject_id}", response_model=s.SubjectOut)
def edit_subject(subject_id: int, body: s.SubjectIn, db=Depends(get_db), user=Depends(current_user)):
    subject = subject_for(db, subject_id, user.id)
    for field, value in body.model_dump().items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", status_code=204)
def delete_subject(subject_id: int, db=Depends(get_db), user=Depends(current_user)):
    db.delete(subject_for(db, subject_id, user.id))
    db.commit()


@router.post("/subjects/{subject_id}/topics", response_model=s.TopicOut, status_code=201)
def create_topic(subject_id: int, body: s.TopicIn, db=Depends(get_db), user=Depends(current_user)):
    subject_for(db, subject_id, user.id)
    topic = m.Topic(subject_id=subject_id, **body.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


@router.get("/topics/{topic_id}")
def get_topic(topic_id: int, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, topic_id, user.id)
    topic.last_opened_at = datetime.utcnow()
    topic.subject.last_studied_at = datetime.utcnow()
    db.commit()
    return {
        "topic": s.TopicOut.model_validate(topic),
        "subject": s.SubjectOut.model_validate(topic.subject),
        "materials": [s.MaterialOut.model_validate(item) for item in topic.materials],
        "notes": [s.NoteOut.model_validate(item) for item in topic.notes],
    }


@router.put("/topics/{topic_id}", response_model=s.TopicOut)
def edit_topic(topic_id: int, body: s.TopicIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, topic_id, user.id)
    topic.title = body.title
    topic.description = body.description
    db.commit()
    db.refresh(topic)
    return topic


@router.delete("/topics/{topic_id}", status_code=204)
def delete_topic(topic_id: int, db=Depends(get_db), user=Depends(current_user)):
    db.delete(topic_for(db, topic_id, user.id))
    db.commit()


@router.post("/topics/{topic_id}/materials", response_model=s.MaterialOut, status_code=201)
async def upload_material(topic_id: int, file: UploadFile = File(...), db=Depends(get_db), user=Depends(current_user)):
    topic_for(db, topic_id, user.id)
    if file.content_type not in ALLOWED_UPLOADS:
        raise HTTPException(415, "Unsupported file format")
    data = await file.read()
    if len(data) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "File is too large")
    folder = BASE_DIR / "uploads" / str(user.id) / str(topic_id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid4().hex}.{ALLOWED_UPLOADS[file.content_type]}"
    path.write_bytes(data)
    text, pages = "", []
    try:
        if file.content_type == "application/pdf":
            pages = [page.extract_text() or "" for page in PdfReader(path).pages]
            text = "\n".join(pages)
        elif file.content_type == "text/plain":
            text = data.decode("utf-8", errors="replace")
            pages = [text]
    except Exception:
        text, pages = "", []
    material = m.StudyMaterial(topic_id=topic_id, file_name=file.filename or "material", file_type=file.content_type, storage_path=str(path), extracted_text=text)
    db.add(material)
    db.flush()
    db.add_all([m.MaterialPage(material_id=material.id, page_number=index + 1, content=content) for index, content in enumerate(pages)])
    db.commit()
    db.refresh(material)
    return material


@router.post("/topics/{topic_id}/materials/text", response_model=s.MaterialOut, status_code=201)
def text_material(topic_id: int, body: s.TextMaterialIn, db=Depends(get_db), user=Depends(current_user)):
    topic_for(db, topic_id, user.id)
    material = m.StudyMaterial(topic_id=topic_id, file_name=body.title, file_type="text/plain", extracted_text=body.content)
    db.add(material)
    db.flush()
    db.add(m.MaterialPage(material_id=material.id, page_number=1, content=body.content))
    db.commit()
    db.refresh(material)
    return material


@router.delete("/materials/{material_id}", status_code=204)
def delete_material(material_id: int, db=Depends(get_db), user=Depends(current_user)):
    material = material_for(db, material_id, user.id)
    if material.storage_path:
        Path(material.storage_path).unlink(missing_ok=True)
    db.delete(material)
    db.commit()


@router.post("/topics/{topic_id}/notes", response_model=s.NoteOut, status_code=201)
def create_note(topic_id: int, body: s.NoteIn, db=Depends(get_db), user=Depends(current_user)):
    topic_for(db, topic_id, user.id)
    note = m.Note(topic_id=topic_id, **body.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.put("/notes/{note_id}", response_model=s.NoteOut)
def edit_note(note_id: int, body: s.NoteIn, db=Depends(get_db), user=Depends(current_user)):
    note = note_for(db, note_id, user.id)
    note.title = body.title
    note.content = body.content
    db.commit()
    db.refresh(note)
    return note


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, db=Depends(get_db), user=Depends(current_user)):
    db.delete(note_for(db, note_id, user.id))
    db.commit()
