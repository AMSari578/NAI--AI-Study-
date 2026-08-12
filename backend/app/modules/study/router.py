from fastapi import APIRouter, Depends, HTTPException

from app.modules.ai.schemas import ContextActionIn
from app.modules.study import schemas as s
from app.db.session import get_db
from app.shared.dependencies import question_for, topic_for
from app.core.security import current_user
from app.modules.study.service import evaluate_answer, mistake_items
from app.integrations.ai_provider import provider
from app import models as m
from app.shared.dependencies import material_for

router = APIRouter(tags=["study"])


@router.post("/ai/evaluate-answer", response_model=s.AnswerEvaluation)
def evaluate(body: s.AnswerIn, db=Depends(get_db), user=Depends(current_user)):
    question = question_for(db, body.question_id, user.id)
    return evaluate_answer(db, question, body.answer)


@router.get("/review/mistakes")
def mistakes(topic_id: int | None = None, db=Depends(get_db), user=Depends(current_user)):
    if topic_id is not None:
        topic_for(db, topic_id, user.id)
    return mistake_items(db, user.id, topic_id)


@router.post("/study/context-action")
def context_action(body: ContextActionIn, db=Depends(get_db), user=Depends(current_user)):
    topic = topic_for(db, body.topic_id, user.id)
    if body.material_id:
        material = material_for(db, body.material_id, user.id)
        if material.topic_id != topic.id:
            raise HTTPException(400, "Material does not belong to the selected topic")
    context = f"SELECTED STUDY TEXT:\n{body.selected_text}"
    if body.action == "add_to_notes":
        note = m.Note(topic_id=topic.id, title=f"Selected text — {topic.title}"[:200], content=body.selected_text)
        db.add(note); db.commit(); db.refresh(note)
        return {"action": body.action, "created_id": note.id, "content": "Selected text was added to your notes."}
    if body.action == "create_flashcard":
        raw = provider().structured("Create one accurate flashcard from this selected text. Return one JSON object with question and answer.", context)
        if isinstance(raw, list): raw = raw[0] if raw else {}
        question = str(raw.get("question", "")).strip() if isinstance(raw, dict) else ""
        answer = str(raw.get("answer", "")).strip() if isinstance(raw, dict) else ""
        if not question or not answer:
            question, answer = "What is the key idea in this selected text?", body.selected_text
        card = m.Flashcard(topic_id=topic.id, question=question, answer=answer)
        db.add(card); db.commit(); db.refresh(card)
        return {"action": body.action, "created_id": card.id, "content": f"Created flashcard: {card.question}"}
    if body.action == "quiz":
        raw = provider().structured("Create one multiple-choice question from this selected text with exactly four choices, correct_answer, and explanation.", context)
        if isinstance(raw, list): raw = raw[0] if raw else {}
        quiz = m.Quiz(topic_id=topic.id, quiz_type="mcq"); db.add(quiz); db.flush()
        question = str(raw.get("question", "What does this selected text explain?")).strip()
        correct = str(raw.get("correct_answer", body.selected_text[:300])).strip()
        choices = list(dict.fromkeys(str(value).strip() for value in raw.get("choices", []) if str(value).strip())) if isinstance(raw, dict) else []
        if correct not in choices: choices.insert(0, correct)
        while len(choices) < 4: choices.append(f"Not supported by the selected text ({len(choices)+1})")
        db.add(m.QuizQuestion(quiz_id=quiz.id, question=question, question_type="mcq", choices=choices[:4], correct_answer=correct, explanation=str(raw.get("explanation", "Based on the selected text.")) if isinstance(raw, dict) else "Based on the selected text."))
        db.commit()
        return {"action": body.action, "created_id": quiz.id, "content": "Created a quiz question from the selected text."}
    prompts = {"explain":"Explain this selected text clearly and step by step.","simplify":"Explain this selected text with simpler words and one familiar example.","summarize":"Summarize only this selected text into concise study points."}
    content = provider().text(prompts[body.action], context)
    if body.action == "summarize":
        summary = m.Summary(topic_id=topic.id, content=content, summary_type="key_points", language="arabic" if any("\u0600" <= c <= "\u06ff" for c in body.selected_text) else "english")
        db.add(summary); db.commit(); db.refresh(summary)
        return {"action": body.action, "created_id": summary.id, "content": content}
    return {"action": body.action, "content": content}
