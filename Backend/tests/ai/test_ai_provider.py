from types import SimpleNamespace

from app.integrations.ai_provider import retrieval_context


def make_topic():
    return SimpleNamespace(
        title="Pharmacology",
        description="A lecture about medicines.",
        subject=SimpleNamespace(name="Medicine"),
        materials=[
            SimpleNamespace(file_name="intro.txt", extracted_text="Tablets are solid dosage forms. " * 20),
            SimpleNamespace(file_name="insulin.txt", extracted_text="Insulin lowers blood glucose by helping glucose enter cells. " * 20),
            SimpleNamespace(file_name="arabic.txt", extracted_text="الانسولين يساعد على خفض سكر الدم ويساعد الجلوكوز على دخول الخلايا. " * 20),
        ],
        notes=[],
    )


def test_rag_retrieves_relevant_english_source():
    context = retrieval_context(make_topic(), "How does insulin affect blood glucose?", max_chunks=1)
    assert "Material: insulin.txt" in context
    assert "Tablets are solid" not in context


def test_rag_retrieves_relevant_arabic_source():
    context = retrieval_context(make_topic(), "كيف يخفض الانسولين سكر الدم؟", max_chunks=1)
    assert "Material: arabic.txt" in context
