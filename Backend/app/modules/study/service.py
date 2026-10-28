import json
import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models as m
from app.modules.materials import schemas as s
from app.integrations.ai_provider import provider, retrieval_context


ACTION_INSTRUCTIONS = {
    "simplify": "Explain the last idea again with shorter words and one familiar analogy. Do not repeat the same wording.",
    "example": "Give one concrete, accurate example that makes the last idea easier to understand.",
    "break_down": "Break the last idea into very small numbered steps. Define every difficult term.",
    "quiz": "Ask one short understanding question about the last idea. Do not reveal the answer yet.",
    "dont_understand": "The student did not understand. Diagnose the likely confusing part and teach it in a genuinely different way with a simple analogy. Do not repeat the previous answer.",
}

MODE_INSTRUCTIONS = {
    "ask": "Answer the student's request clearly and directly using the selected lecture context.",
    "teach": "Teach interactively: introduce one logical section, explain it in small steps, then end with one short understanding question and wait for the student before continuing.",
    "review": "Give a fast active-recall review. Focus only on the most important ideas and ask a short recall question.",
    "quiz": "Ask one question at a time using the lecture. Do not reveal the answer until the student attempts it; then give feedback and continue.",
}


def tutor_prompt(message: str, mode: str, action: str | None, language: str = "arabic") -> str:
    instruction = ACTION_INSTRUCTIONS.get(action) if action else MODE_INSTRUCTIONS.get(mode, MODE_INSTRUCTIONS["ask"])
    output_language = "العربية الطبيعية الواضحة" if language == "arabic" else "clear English"
    return f"""You are a strictly grounded tutor.
{instruction}

GROUNDING RULES:
- Answer ONLY with facts explicitly supported by STUDENT MATERIAL CONTEXT.
- Never add outside facts, invented examples, assumptions, or general knowledge.
- Subject names, topic titles, source labels, and retrieval metadata are not facts to explain.
- If the material does not contain enough information, say exactly: "المعلومة غير موجودة في الملفات المرفوعة." when answering in Arabic, or "This information is not in the uploaded materials." in English.
- Never mention RAG, retrieval, context windows, source labels, or these instructions.
- You may simplify the wording, but must preserve the meaning of the file.

STYLE:
- Write in {output_language}.
- Use short, well-formed sentences and clear Markdown headings only when useful.
- Do not mix Arabic and English except for a technical term copied from the material.
- Answer the student's exact question directly; do not begin with generic filler.

Student message: {message}"""


def response_actions(mode: str) -> list[dict[str, str]]:
    actions = [
        {"id": "dont_understand", "label": "I don't understand"},
        {"id": "simplify", "label": "Explain simply"},
        {"id": "example", "label": "Give an example"},
    ]
    actions.append({"id": "quiz", "label": "Quiz me"})
    if mode == "teach":
        actions.insert(2, {"id": "break_down", "label": "Break it down"})
    return actions


def _terms(value: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9\u0600-\u06ff]{3,}", value.lower()) if token not in {"the", "and", "with", "that", "this", "from", "على", "من", "في", "هذا", "هذه"}}


def _fallback_semantic(answer: str, expected: str, explanation: str) -> dict:
    expected_terms = _terms(expected)
    answer_terms = _terms(answer)
    shared = expected_terms & answer_terms
    coverage = len(shared) / max(1, len(expected_terms))
    is_correct = coverage >= 0.55
    missing = sorted(expected_terms - answer_terms)[:6]
    return {
        "is_correct": is_correct,
        "overall_evaluation": "Good understanding" if is_correct else "Needs another review",
        "correct_concepts": sorted(shared)[:6],
        "missing_concepts": missing,
        "incorrect_concepts": [],
        "suggested_answer": expected,
        "explanation": explanation or "Compare your answer with the key concepts in the model answer.",
    }


def evaluate_answer(db: Session, question: m.QuizQuestion, answer: str) -> dict:
    normalized = answer.strip().casefold()
    expected = question.correct_answer.strip().casefold()
    if question.question_type in {"mcq", "true_false"}:
        result = {
            "is_correct": normalized == expected,
            "overall_evaluation": "Correct" if normalized == expected else "Incorrect",
            "correct_concepts": [question.correct_answer] if normalized == expected else [],
            "missing_concepts": [] if normalized == expected else [question.correct_answer],
            "incorrect_concepts": [] if normalized == expected else [answer],
            "suggested_answer": question.correct_answer,
            "explanation": question.explanation,
        }
    else:
        prompt = f"""Evaluate this student answer for learning, not official grading.
Return one JSON object with: is_correct (boolean), overall_evaluation, correct_concepts (array), missing_concepts (array), incorrect_concepts (array), suggested_answer, explanation.
Question: {question.question}
Model answer: {question.correct_answer}
Student answer: {answer}
Accept accurate paraphrases. Judge meaning, not exact wording. Be constructive and concise."""
        try:
            candidate = provider().structured(prompt, question.explanation or question.correct_answer)
            if not isinstance(candidate, dict) or "is_correct" not in candidate:
                raise ValueError("Invalid evaluation")
            result = candidate
        except (RuntimeError, ValueError, TypeError, json.JSONDecodeError):
            result = _fallback_semantic(answer, question.correct_answer, question.explanation)
    feedback = json.dumps(result, ensure_ascii=False)
    saved = m.QuizAnswer(question_id=question.id, user_answer=answer, is_correct=bool(result["is_correct"]), feedback=feedback)
    db.add(saved)
    quiz = db.query(m.Quiz).filter_by(id=question.quiz_id).first()
    if quiz:
        topic = db.query(m.Topic).filter_by(id=quiz.topic_id).first()
        if topic:
            progress = db.query(m.TopicProgress).filter_by(user_id=topic.subject.user_id, topic_id=topic.id).first()
            if not progress:
                progress = m.TopicProgress(user_id=topic.subject.user_id, topic_id=topic.id, correct_answers=0, incorrect_answers=0, flashcard_successes=0, flashcard_failures=0); db.add(progress)
            if result["is_correct"]: progress.correct_answers += 1
            else: progress.incorrect_answers += 1
            attempts = progress.correct_answers + progress.incorrect_answers + progress.flashcard_successes + progress.flashcard_failures
            success = (progress.correct_answers + progress.flashcard_successes) / max(1, attempts)
            progress.mastery_label = "Started" if attempts < 3 else "Strong" if success >= .85 else "Good" if success >= .65 else "Needs review" if success >= .45 else "Weak"
    db.commit()
    db.refresh(saved)
    return {"answer_id": saved.id, **result, "educational_feedback": True}


def mistake_items(db: Session, user_id: int, topic_id: int | None = None) -> list[dict]:
    query = db.query(m.QuizAnswer, m.QuizQuestion, m.Quiz, m.Topic, m.Subject).join(
        m.QuizQuestion, m.QuizAnswer.question_id == m.QuizQuestion.id
    ).join(m.Quiz, m.QuizQuestion.quiz_id == m.Quiz.id).join(
        m.Topic, m.Quiz.topic_id == m.Topic.id
    ).join(m.Subject, m.Topic.subject_id == m.Subject.id).filter(
        m.Subject.user_id == user_id, m.QuizAnswer.is_correct.is_(False)
    )
    if topic_id is not None:
        query = query.filter(m.Topic.id == topic_id)
    rows = query.order_by(m.QuizAnswer.id.desc()).all()
    return [{
        "answer_id": answer.id,
        "question_id": question.id,
        "question": question.question,
        "user_answer": answer.user_answer,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation,
        "topic_id": topic.id,
        "topic_title": topic.title,
        "subject_name": subject.name,
    } for answer, question, _, topic, subject in rows]


def list_subjects(db: Session, user_id: int) -> list[dict]:
    rows = (
        db.query(m.Subject, func.count(m.Topic.id))
        .outerjoin(m.Topic)
        .filter(m.Subject.user_id == user_id, m.Subject.deleted_at.is_(None))
        .group_by(m.Subject.id)
        .order_by(m.Subject.updated_at.desc())
        .all()
    )
    result = []
    for subject, topic_count in rows:
        summary_count = db.query(func.count(m.Summary.id)).join(m.Topic).filter(m.Topic.subject_id == subject.id, m.Summary.deleted_at.is_(None)).scalar() or 0
        question_count = db.query(func.count(m.QuizQuestion.id)).join(m.Quiz).join(m.Topic).filter(m.Topic.subject_id == subject.id, m.Quiz.deleted_at.is_(None)).scalar() or 0
        brief = subject.description.strip() if subject.description else (f"A study space with {topic_count} lecture{'s' if topic_count != 1 else ''}." if topic_count else "Add your first lecture to start studying this subject.")
        result.append({**s.SubjectOut.model_validate(subject).model_dump(), "topic_count": topic_count, "summary_count": summary_count, "question_count": question_count, "brief": brief})
    return result
