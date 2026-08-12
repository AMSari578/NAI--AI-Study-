from fastapi import HTTPException
from sqlalchemy.orm import Session
from ..models import Subject, Topic, StudyMaterial, Note, ChatConversation, Quiz, QuizQuestion

def subject_for(db: Session, subject_id: int, user_id: int):
    obj = db.query(Subject).filter(Subject.id == subject_id, Subject.user_id == user_id).first()
    if not obj: raise HTTPException(404, "Subject not found")
    return obj
def topic_for(db: Session, topic_id: int, user_id: int):
    obj = db.query(Topic).join(Subject).filter(Topic.id == topic_id, Subject.user_id == user_id).first()
    if not obj: raise HTTPException(404, "Topic not found")
    return obj
def material_for(db, obj_id, user_id):
    obj = db.query(StudyMaterial).join(Topic).join(Subject).filter(StudyMaterial.id == obj_id, Subject.user_id == user_id).first()
    if not obj: raise HTTPException(404, "Material not found")
    return obj
def note_for(db, obj_id, user_id):
    obj = db.query(Note).join(Topic).join(Subject).filter(Note.id == obj_id, Subject.user_id == user_id).first()
    if not obj: raise HTTPException(404, "Note not found")
    return obj
def conversation_for(db, obj_id, user_id):
    obj = db.query(ChatConversation).join(Topic).join(Subject).filter(ChatConversation.id == obj_id, Subject.user_id == user_id).first()
    if not obj: raise HTTPException(404, "Conversation not found")
    return obj
def question_for(db, obj_id, user_id):
    obj = db.query(QuizQuestion).join(Quiz).join(Topic).join(Subject).filter(QuizQuestion.id == obj_id, Subject.user_id == user_id).first()
    if not obj: raise HTTPException(404, "Question not found")
    return obj
