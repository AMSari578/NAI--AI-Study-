from fastapi import APIRouter,Depends,HTTPException
from app import models as m
from app.modules.exams import schemas as s
from app.integrations.ai_provider import provider,topic_context
from app.db.session import get_db
from app.shared.dependencies import topic_for
from app.core.security import current_user
from app.modules.study.service import evaluate_answer
router=APIRouter(tags=["exam-mode"])
@router.post("/ai/mock-exam")
def mock_exam(body:s.MockExamIn,db=Depends(get_db),user=Depends(current_user)):
    topics=[topic_for(db,value,user.id) for value in body.topic_ids];context="\n\n".join(topic_context(topic) for topic in topics)
    types=", ".join(body.question_types);prompt=f"Create exactly {body.count} {body.difficulty}-difficulty mock-exam questions across these lectures. Mix only these types: {types}. Return JSON array with question, question_type, choices, correct_answer, explanation. MCQ must have exactly four unique choices. True/false choices are [True,False]. Essay choices are null. Test varied concepts and applications; no duplicate patterns."
    items=provider().structured(prompt,context);quiz=m.Quiz(topic_id=topics[0].id,quiz_type="mock_exam");db.add(quiz);db.flush()
    for raw in (items if isinstance(items,list) else [])[:body.count]:
        choices=raw.get("choices");kind=str(raw.get("question_type") or ("essay" if choices is None and "essay" in body.question_types else body.question_types[0]));question=str(raw.get("question","")).strip();correct=str(raw.get("correct_answer","")).strip()
        if kind not in body.question_types or not question or not correct:continue
        if kind=="mcq":
            choices=list(dict.fromkeys(str(x).strip() for x in (choices or []) if str(x).strip()))
            if correct not in choices:choices.insert(0,correct)
            if len(choices)!=4:continue
        elif kind=="true_false":choices=["True","False"]
        else:choices=None
        db.add(m.QuizQuestion(quiz_id=quiz.id,question=question,question_type=kind,choices=choices,correct_answer=correct,explanation=str(raw.get("explanation","")).strip()))
    db.commit();questions=db.query(m.QuizQuestion).filter_by(quiz_id=quiz.id).all()
    if not questions:
        fallback_type="essay" if "essay" in body.question_types else body.question_types[0]
        for index in range(body.count):
            topic=topics[index%len(topics)];answer=(topic.materials[0].extracted_text[:500] if topic.materials and topic.materials[0].extracted_text else topic.description or topic.title)
            db.add(m.QuizQuestion(quiz_id=quiz.id,question=f"Explain an important idea from {topic.title} in your own words ({index+1}).",question_type=fallback_type,choices=None if fallback_type=="essay" else ["True","False"],correct_answer=answer,explanation="Compare the response with the selected lecture material."))
        db.commit();questions=db.query(m.QuizQuestion).filter_by(quiz_id=quiz.id).all()
    return {"id":quiz.id,"time_limit_minutes":body.time_limit_minutes,"questions":[{"id":q.id,"question":q.question,"question_type":q.question_type,"choices":q.choices} for q in questions]}
@router.post("/mock-exams/{quiz_id}/submit")
def submit_mock_exam(quiz_id:int,body:s.ExamSubmission,db=Depends(get_db),user=Depends(current_user)):
    quiz=db.query(m.Quiz).join(m.Topic).join(m.Subject).filter(m.Quiz.id==quiz_id,m.Subject.user_id==user.id,m.Quiz.quiz_type=="mock_exam").first()
    if not quiz:raise HTTPException(404,"Mock exam not found")
    by_id={item.question_id:item.answer for item in body.answers};results=[];correct=0
    for question in quiz.questions:
        answer=by_id.get(question.id,"")
        evaluated=evaluate_answer(db,question,answer)
        if evaluated["is_correct"]:correct+=1
        results.append({"question_id":question.id,"question":question.question,"user_answer":answer,"correct_answer":question.correct_answer,"is_correct":evaluated["is_correct"],"explanation":evaluated["explanation"],"suggested_answer":evaluated["suggested_answer"]})
    quiz.score=round(correct/max(1,len(quiz.questions))*100,1);db.commit()
    return {"score":quiz.score,"correct":correct,"total":len(quiz.questions),"time_spent_seconds":body.time_spent_seconds,"results":results,"topic_id":quiz.topic_id}
