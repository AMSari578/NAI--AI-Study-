from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException

from app import models as m
from app.modules.exams.schemas import ExamIn
from app.modules.planning import schemas as s
from app.modules.study.schemas import StudySessionIn
from app.integrations.ai_provider import provider
from app.db.session import get_db
from app.shared.dependencies import material_for, subject_for, topic_for
from app.core.security import current_user

router=APIRouter(tags=["planning"])

def exam_for(db,exam_id,user_id):
    item=db.query(m.Exam).filter_by(id=exam_id,user_id=user_id).first()
    if not item: raise HTTPException(404,"Exam not found")
    return item

def plan_for(db,plan_id,user_id):
    item=db.query(m.StudyPlan).filter_by(id=plan_id,user_id=user_id).first()
    if not item: raise HTTPException(404,"Study plan not found")
    return item

def exam_dict(item):
    return {"id":item.id,"name":item.name,"subject_id":item.subject_id,"subject_name":item.subject.name if hasattr(item,"subject") and item.subject else "","exam_datetime":item.exam_datetime,"notes":item.notes,"topic_ids":[link.topic_id for link in item.topics]}

@router.get("/exams")
def exams(db=Depends(get_db),user=Depends(current_user)):
    rows=db.query(m.Exam).filter_by(user_id=user.id).order_by(m.Exam.exam_datetime).all()
    return [{"id":x.id,"name":x.name,"subject_id":x.subject_id,"exam_datetime":x.exam_datetime,"notes":x.notes,"topic_ids":[t.topic_id for t in x.topics]} for x in rows]

@router.post("/exams",status_code=201)
def create_exam(body:ExamIn,db=Depends(get_db),user=Depends(current_user)):
    subject=subject_for(db,body.subject_id,user.id)
    for topic_id in body.topic_ids:
        topic=topic_for(db,topic_id,user.id)
        if topic.subject_id!=subject.id: raise HTTPException(400,"Every exam topic must belong to the selected subject")
    item=m.Exam(user_id=user.id,subject_id=subject.id,name=body.name,exam_datetime=body.exam_datetime,notes=body.notes);db.add(item);db.flush();db.add_all([m.ExamTopic(exam_id=item.id,topic_id=value) for value in body.topic_ids]);db.commit();db.refresh(item);return {"id":item.id,"name":item.name,"subject_id":item.subject_id,"exam_datetime":item.exam_datetime,"notes":item.notes,"topic_ids":body.topic_ids}

@router.delete("/exams/{exam_id}",status_code=204)
def delete_exam(exam_id:int,db=Depends(get_db),user=Depends(current_user)):
    db.delete(exam_for(db,exam_id,user.id));db.commit()

@router.get("/study-plans")
def plans(db=Depends(get_db),user=Depends(current_user)):
    rows=db.query(m.StudyPlan).filter_by(user_id=user.id).order_by(m.StudyPlan.id.desc()).all()
    return [{"id":x.id,"title":x.title,"exam_id":x.exam_id,"items":[{"id":i.id,"topic_id":i.topic_id,"title":i.title,"activity_type":i.activity_type,"scheduled_for":i.scheduled_for,"duration_minutes":i.duration_minutes,"status":i.status} for i in x.items]} for x in rows]

@router.post("/study-plans",status_code=201)
def create_plan(body:s.StudyPlanIn,db=Depends(get_db),user=Depends(current_user)):
    if body.exam_id: exam_for(db,body.exam_id,user.id)
    for item in body.items:
        if item.topic_id: topic_for(db,item.topic_id,user.id)
    plan=m.StudyPlan(user_id=user.id,title=body.title,exam_id=body.exam_id);db.add(plan);db.flush();db.add_all([m.StudyPlanItem(plan_id=plan.id,**item.model_dump()) for item in body.items]);db.commit();db.refresh(plan);return {"id":plan.id,"title":plan.title,"items":plan.items}

@router.post("/study-plans/ai",status_code=201)
def create_ai_plan(body:s.AIPlanIn,db=Depends(get_db),user=Depends(current_user)):
    exam=exam_for(db,body.exam_id,user.id);topics=[topic_for(db,link.topic_id,user.id) for link in exam.topics];now=datetime.now();days=max(1,(exam.exam_datetime-now).days)
    context="\n".join(f"{topic.id}: {topic.title}" for topic in topics)
    prompt=f"Create a realistic study plan before {exam.exam_datetime.isoformat()} using {body.daily_minutes} minutes per available day. Return JSON array with topic_id, title, activity_type (study/review/flashcards/quiz/mock_exam), day_offset, duration_minutes. Include learning, spaced review, quizzes, final review, and one mock exam. Available weekday numbers: {body.available_days}. Topic IDs and titles:\n{context}"
    try: generated=provider().structured(prompt,context)
    except Exception: generated=[]
    if not isinstance(generated,list) or not generated:
        generated=[]
        for index in range(max(1,min(days,len(topics)*3))):
            topic=topics[index%len(topics)] if topics else None;generated.append({"topic_id":topic.id if topic else None,"title":f"Review {topic.title if topic else exam.name}","activity_type":["study","review","quiz"][index%3],"day_offset":index,"duration_minutes":body.daily_minutes})
    plan=m.StudyPlan(user_id=user.id,exam_id=exam.id,title=f"{exam.name} study plan");db.add(plan);db.flush()
    for raw in generated[:60]:
        offset=max(0,min(days-1,int(raw.get("day_offset",0))));scheduled=now+timedelta(days=offset)
        while scheduled.weekday() not in body.available_days and scheduled<exam.exam_datetime: scheduled+=timedelta(days=1)
        db.add(m.StudyPlanItem(plan_id=plan.id,topic_id=raw.get("topic_id"),title=str(raw.get("title","Study session"))[:220],activity_type=str(raw.get("activity_type","study")),scheduled_for=scheduled,duration_minutes=max(5,min(480,int(raw.get("duration_minutes",body.daily_minutes))))))
    db.commit();db.refresh(plan);return {"id":plan.id,"title":plan.title,"items":plan.items}

@router.put("/study-plan-items/{item_id}")
def update_plan_item(item_id:int,body:s.PlanItemStatus,db=Depends(get_db),user=Depends(current_user)):
    item=db.query(m.StudyPlanItem).join(m.StudyPlan).filter(m.StudyPlanItem.id==item_id,m.StudyPlan.user_id==user.id).first()
    if not item: raise HTTPException(404,"Study plan item not found")
    item.status=body.status;item.completed_at=datetime.now() if body.status=="completed" else None
    if body.scheduled_for:item.scheduled_for=body.scheduled_for
    db.commit();db.refresh(item);return item

@router.post("/study-plans/{plan_id}/recalculate")
def recalculate(plan_id:int,db=Depends(get_db),user=Depends(current_user)):
    plan=plan_for(db,plan_id,user.id);exam=exam_for(db,plan.exam_id,user.id) if plan.exam_id else None;remaining=[item for item in plan.items if item.status!="completed"]
    start=datetime.now();end=exam.exam_datetime if exam else start+timedelta(days=max(1,len(remaining)))
    step=max(1,(end-start).days//max(1,len(remaining)))
    for index,item in enumerate(remaining):item.scheduled_for=min(end-timedelta(hours=1),start+timedelta(days=index*step));item.status="planned"
    db.commit();return {"id":plan.id,"rescheduled":len(remaining)}

@router.get("/calendar")
def calendar(db=Depends(get_db),user=Depends(current_user)):
    events=[]
    events += [{"id":x.id,"type":"task","title":x.title,"date":x.due_date} for x in db.query(m.Task).filter(m.Task.user_id==user.id,m.Task.due_date.is_not(None)).all()]
    events += [{"id":x.id,"type":"reminder","title":x.title,"date":x.reminder_datetime} for x in db.query(m.Reminder).filter_by(user_id=user.id).all()]
    events += [{"id":x.id,"type":"exam","title":x.name,"date":x.exam_datetime} for x in db.query(m.Exam).filter_by(user_id=user.id).all()]
    events += [{"id":x.id,"type":"plan","title":x.title,"date":x.scheduled_for,"status":x.status} for x in db.query(m.StudyPlanItem).join(m.StudyPlan).filter(m.StudyPlan.user_id==user.id).all()]
    return sorted(events,key=lambda x:x["date"] or datetime.max)

@router.post("/study-sessions",status_code=201)
def start_session(body:StudySessionIn,db=Depends(get_db),user=Depends(current_user)):
    topic=topic_for(db,body.topic_id,user.id)
    if body.material_id:
        material=material_for(db,body.material_id,user.id)
        if material.topic_id!=topic.id:raise HTTPException(400,"Material does not belong to topic")
    item=m.StudySession(user_id=user.id,subject_id=topic.subject_id,topic_id=topic.id,material_id=body.material_id,mode=body.mode);db.add(item);db.commit();db.refresh(item);return item

@router.post("/study-sessions/{session_id}/finish")
def finish_session(session_id:int,db=Depends(get_db),user=Depends(current_user)):
    item=db.query(m.StudySession).filter_by(id=session_id,user_id=user.id).first()
    if not item:raise HTTPException(404,"Study session not found")
    item.ended_at=datetime.now();item.duration_minutes=max(0,round((item.ended_at-item.started_at).total_seconds()/60));db.commit();db.refresh(item);return item
