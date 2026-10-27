from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app import models as m
from app.modules.auth.schemas import UserOut
from app.modules.materials.schemas import MaterialOut, TopicOut
from app.modules.planning.schemas import ReminderIn, TaskIn
from app.db.session import get_db
from app.shared.dependencies import subject_for, topic_for
from app.core.security import current_user
from app.modules.study.service import list_subjects

router = APIRouter(tags=["productivity"])


def register_owned_crud(model, schema) -> None:
    base = f"/{model.__tablename__}"

    @router.get(base)
    def list_items(db=Depends(get_db), user=Depends(current_user)):
        return db.query(model).filter(model.user_id == user.id).order_by(model.id.desc()).all()

    @router.post(base, status_code=201)
    def create_item(body: schema, db=Depends(get_db), user=Depends(current_user)):
        if body.subject_id: subject_for(db, body.subject_id, user.id)
        if body.topic_id: topic_for(db, body.topic_id, user.id)
        item = model(user_id=user.id, **body.model_dump())
        db.add(item); db.commit(); db.refresh(item)
        return item

    @router.put(f"{base}/{{item_id}}")
    def update_item(item_id: int, body: schema, db=Depends(get_db), user=Depends(current_user)):
        item = db.query(model).filter(model.id == item_id, model.user_id == user.id).first()
        if not item: raise HTTPException(404, "Item not found")
        for key, value in body.model_dump().items(): setattr(item, key, value)
        db.commit(); db.refresh(item)
        return item

    @router.delete(f"{base}/{{item_id}}", status_code=204)
    def remove_item(item_id: int, db=Depends(get_db), user=Depends(current_user)):
        item = db.query(model).filter(model.id == item_id, model.user_id == user.id).first()
        if not item: raise HTTPException(404, "Item not found")
        db.delete(item); db.commit()


register_owned_crud(m.Task, TaskIn)
register_owned_crud(m.Reminder, ReminderIn)


@router.get("/dashboard")
def dashboard(db=Depends(get_db), user=Depends(current_user)):
    topics = db.query(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, m.Subject.deleted_at.is_(None)).order_by(m.Topic.last_opened_at.desc().nullslast()).limit(5).all()
    tasks = db.query(m.Task).filter(m.Task.user_id == user.id, m.Task.completed == False).order_by(m.Task.due_date).limit(5).all()
    reminders = db.query(m.Reminder).filter(m.Reminder.user_id == user.id, m.Reminder.reminder_datetime >= datetime.now()).order_by(m.Reminder.reminder_datetime).limit(5).all()
    materials = db.query(m.StudyMaterial).join(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, m.Subject.deleted_at.is_(None), m.StudyMaterial.deleted_at.is_(None)).order_by(m.StudyMaterial.created_at.desc()).limit(6).all()
    recent_topics = [{**TopicOut.model_validate(item).model_dump(), "subject_name": item.subject.name, "material_count": len(item.materials)} for item in topics]
    exams = db.query(m.Exam).filter(m.Exam.user_id == user.id, m.Exam.exam_datetime >= datetime.now()).order_by(m.Exam.exam_datetime).limit(5).all()
    due_cards = db.query(m.Flashcard).join(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id, (m.Flashcard.next_review_at.is_(None)) | (m.Flashcard.next_review_at <= datetime.now())).count()
    weak = db.query(m.TopicProgress, m.Topic, m.Subject).join(m.Topic, m.TopicProgress.topic_id == m.Topic.id).join(m.Subject, m.Topic.subject_id == m.Subject.id).filter(m.TopicProgress.user_id == user.id, m.TopicProgress.mastery_label.in_(["Weak","Needs review"])).limit(5).all()
    last_material = (
        db.query(m.StudyMaterial, m.Topic, m.Subject)
        .select_from(m.StudyMaterial)
        .join(m.Topic, m.StudyMaterial.topic_id == m.Topic.id)
        .join(m.Subject, m.Topic.subject_id == m.Subject.id)
        .filter(
            m.Subject.user_id == user.id,
            m.Subject.deleted_at.is_(None),
            m.StudyMaterial.deleted_at.is_(None),
            m.StudyMaterial.last_opened_at.is_not(None),
        )
        .order_by(m.StudyMaterial.last_opened_at.desc())
        .first()
    )
    continuation=recent_topics[0] if recent_topics else None
    if last_material:
        material,topic,subject=last_material;continuation={"id":topic.id,"title":topic.title,"subject_name":subject.name,"material_id":material.id,"material_name":material.file_name,"last_studied_at":material.last_opened_at}
    owned_topics = db.query(m.Topic.id).join(m.Subject).filter(m.Subject.user_id == user.id, m.Subject.deleted_at.is_(None)).subquery()
    statistics = {
        "subjects": db.query(m.Subject).filter(m.Subject.user_id == user.id, m.Subject.deleted_at.is_(None)).count(),
        "quizzes": db.query(m.Quiz).filter(m.Quiz.topic_id.in_(db.query(owned_topics.c.id)), m.Quiz.deleted_at.is_(None)).count(),
        "summaries": db.query(m.Summary).filter(m.Summary.topic_id.in_(db.query(owned_topics.c.id)), m.Summary.deleted_at.is_(None)).count(),
        "concept_maps": db.query(m.ConceptMap).filter(m.ConceptMap.topic_id.in_(db.query(owned_topics.c.id)), m.ConceptMap.deleted_at.is_(None)).count(),
    }
    return {"user": UserOut.model_validate(user), "statistics": statistics, "subjects": list_subjects(db, user.id), "recent_topics": recent_topics, "recent_materials": [MaterialOut.model_validate(item) for item in materials], "tasks": tasks, "reminders": reminders, "upcoming_exams":[{"id":x.id,"name":x.name,"subject_id":x.subject_id,"exam_datetime":x.exam_datetime} for x in exams], "flashcards_due":due_cards, "weak_topics":[{"topic_id":p.topic_id,"topic_title":t.title,"subject_name":subject.name,"label":p.mastery_label} for p,t,subject in weak], "continue_studying":continuation}
