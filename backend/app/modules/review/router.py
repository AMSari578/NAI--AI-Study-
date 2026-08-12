from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_

from app import models as m
from app.modules.review import schemas as s
from app.db.session import get_db
from app.shared.dependencies import topic_for
from app.core.security import current_user

router = APIRouter(tags=["memory"])


def _card_for(db, card_id: int, user_id: int):
    card = (
        db.query(m.Flashcard)
        .select_from(m.Flashcard)
        .join(m.Topic, m.Flashcard.topic_id == m.Topic.id)
        .join(m.Subject, m.Topic.subject_id == m.Subject.id)
        .filter(m.Flashcard.id == card_id, m.Subject.user_id == user_id)
        .first()
    )
    if not card:
        raise HTTPException(404, "Flashcard not found")
    return card


def _progress(db, user_id: int, topic_id: int):
    item = db.query(m.TopicProgress).filter_by(user_id=user_id, topic_id=topic_id).first()
    if not item:
        item = m.TopicProgress(user_id=user_id, topic_id=topic_id, correct_answers=0, incorrect_answers=0, flashcard_successes=0, flashcard_failures=0); db.add(item)
    return item


def _mastery(item: m.TopicProgress) -> str:
    attempts = item.correct_answers + item.incorrect_answers + item.flashcard_successes + item.flashcard_failures
    if not attempts: return "Not started"
    success = (item.correct_answers + item.flashcard_successes) / attempts
    if attempts < 3: return "Started"
    if success >= .85: return "Strong"
    if success >= .65: return "Good"
    if success >= .45: return "Needs review"
    return "Weak"


@router.post("/flashcards/{card_id}/review")
def rate_flashcard(card_id: int, body: s.FlashcardRating, db=Depends(get_db), user=Depends(current_user)):
    card = _card_for(db, card_id, user.id); now = datetime.now()
    if body.rating == "again": interval, ease, success = 0, max(1.3, card.ease_factor - .2), False
    elif body.rating == "hard": interval, ease, success = max(1, round(max(1, card.interval_days) * 1.2)), max(1.3, card.ease_factor - .15), True
    elif body.rating == "easy": interval, ease, success = max(4, round(max(1, card.interval_days) * card.ease_factor * 1.3)), card.ease_factor + .15, True
    else: interval, ease, success = max(1, round(max(1, card.interval_days) * card.ease_factor)), card.ease_factor, True
    card.last_reviewed_at = now; card.review_count += 1; card.interval_days = interval; card.ease_factor = ease
    card.next_review_at = now + (timedelta(minutes=10) if body.rating == "again" else timedelta(days=interval))
    progress = _progress(db, user.id, card.topic_id)
    if success: progress.flashcard_successes += 1
    else: progress.flashcard_failures += 1
    progress.mastery_label = _mastery(progress); db.commit(); db.refresh(card)
    return {"id":card.id,"rating":body.rating,"next_review_at":card.next_review_at,"interval_days":card.interval_days,"review_count":card.review_count}

@router.post("/topics/{topic_id}/flashcards",status_code=201)
def create_flashcard(topic_id:int,body:s.FlashcardIn,db=Depends(get_db),user=Depends(current_user)):
    topic_for(db,topic_id,user.id);card=m.Flashcard(topic_id=topic_id,question=body.question,answer=body.answer);db.add(card);db.commit();db.refresh(card);return card

@router.delete("/flashcards/{card_id}",status_code=204)
def delete_flashcard(card_id:int,db=Depends(get_db),user=Depends(current_user)):
    card=_card_for(db,card_id,user.id);db.delete(card);db.commit()


@router.get("/review/due-flashcards")
def due_flashcards(topic_id: int | None = None, db=Depends(get_db), user=Depends(current_user)):
    if topic_id is not None: topic_for(db, topic_id, user.id)
    query = (
        db.query(m.Flashcard, m.Topic, m.Subject)
        .select_from(m.Flashcard)
        .join(m.Topic, m.Flashcard.topic_id == m.Topic.id)
        .join(m.Subject, m.Topic.subject_id == m.Subject.id)
        .filter(
            m.Subject.user_id == user.id,
            or_(m.Flashcard.next_review_at.is_(None), m.Flashcard.next_review_at <= datetime.now()),
        )
    )
    if topic_id is not None: query = query.filter(m.Topic.id == topic_id)
    return [{"id":card.id,"question":card.question,"answer":card.answer,"topic_id":topic.id,"topic_title":topic.title,"subject_name":subject.name,"review_count":card.review_count} for card,topic,subject in query.order_by(m.Flashcard.next_review_at).limit(100).all()]

@router.get("/review/items")
def review_items(db=Depends(get_db),user=Depends(current_user)):
    rows=db.query(m.ReviewItem,m.Topic,m.Subject).join(m.Topic,m.ReviewItem.topic_id==m.Topic.id).join(m.Subject,m.Topic.subject_id==m.Subject.id).filter(m.ReviewItem.user_id==user.id,m.ReviewItem.completed.is_(False)).order_by(m.ReviewItem.id.desc()).all()
    return [{"id":item.id,"title":item.title,"topic_id":topic.id,"topic_title":topic.title,"subject_name":subject.name,"source_type":item.source_type} for item,topic,subject in rows]

@router.post("/review/items",status_code=201)
def add_review_item(body:s.ReviewItemIn,db=Depends(get_db),user=Depends(current_user)):
    topic_for(db,body.topic_id,user.id);item=m.ReviewItem(user_id=user.id,**body.model_dump());db.add(item);db.commit();db.refresh(item);return item

@router.post("/review/items/{item_id}/complete")
def complete_review_item(item_id:int,db=Depends(get_db),user=Depends(current_user)):
    item=db.query(m.ReviewItem).filter_by(id=item_id,user_id=user.id).first()
    if not item:raise HTTPException(404,"Review item not found")
    item.completed=True;db.commit();return {"id":item.id,"completed":True}


@router.get("/progress")
def progress(db=Depends(get_db), user=Depends(current_user)):
    topics = db.query(m.Topic).join(m.Subject).filter(m.Subject.user_id == user.id).all()
    progress_by_topic = {item.topic_id:item for item in db.query(m.TopicProgress).filter_by(user_id=user.id).all()}
    sessions = db.query(m.StudySession).filter_by(user_id=user.id).all()
    rows=[]
    for topic in topics:
        item=progress_by_topic.get(topic.id)
        rows.append({"topic_id":topic.id,"topic_title":topic.title,"subject_name":topic.subject.name,"mastery_label":item.mastery_label if item else "Not started","correct_answers":item.correct_answers if item else 0,"incorrect_answers":item.incorrect_answers if item else 0,"flashcard_reviews":((item.flashcard_successes+item.flashcard_failures) if item else 0)})
    return {"subjects_studied":len({topic.subject_id for topic in topics if topic.last_opened_at}),"topics_studied":sum(1 for topic in topics if topic.last_opened_at),"study_sessions":len(sessions),"minutes_studied":sum(item.duration_minutes or 0 for item in sessions),"topics":rows}
