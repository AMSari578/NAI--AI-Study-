from sqlalchemy import inspect, text

from .session import Base, engine


def initialize_database() -> None:
    """Create tables and apply the small SQLite-compatible legacy migrations."""
    Base.metadata.create_all(engine)
    summary_columns = {column["name"] for column in inspect(engine).get_columns("summaries")}
    subject_columns = {column["name"] for column in inspect(engine).get_columns("subjects")}
    flashcard_columns = {column["name"] for column in inspect(engine).get_columns("flashcards")}
    material_columns = {column["name"] for column in inspect(engine).get_columns("study_materials")}
    with engine.begin() as connection:
        if "summary_type" not in summary_columns:
            connection.execute(text("ALTER TABLE summaries ADD COLUMN summary_type VARCHAR(20) NOT NULL DEFAULT 'simple'"))
        if "language" not in summary_columns:
            connection.execute(text("ALTER TABLE summaries ADD COLUMN language VARCHAR(20) NOT NULL DEFAULT 'english'"))
        if "icon" not in subject_columns:
            connection.execute(text("ALTER TABLE subjects ADD COLUMN icon VARCHAR(40) NOT NULL DEFAULT 'book'"))
        if "color" not in subject_columns:
            connection.execute(text("ALTER TABLE subjects ADD COLUMN color VARCHAR(20) NOT NULL DEFAULT '#3B82F6'"))
        if "last_reviewed_at" not in flashcard_columns:
            connection.execute(text("ALTER TABLE flashcards ADD COLUMN last_reviewed_at DATETIME"))
        if "next_review_at" not in flashcard_columns:
            connection.execute(text("ALTER TABLE flashcards ADD COLUMN next_review_at DATETIME"))
        if "review_count" not in flashcard_columns:
            connection.execute(text("ALTER TABLE flashcards ADD COLUMN review_count INTEGER NOT NULL DEFAULT 0"))
        if "interval_days" not in flashcard_columns:
            connection.execute(text("ALTER TABLE flashcards ADD COLUMN interval_days INTEGER NOT NULL DEFAULT 0"))
        if "ease_factor" not in flashcard_columns:
            connection.execute(text("ALTER TABLE flashcards ADD COLUMN ease_factor FLOAT NOT NULL DEFAULT 2.5"))
        if "last_opened_at" not in material_columns:
            connection.execute(text("ALTER TABLE study_materials ADD COLUMN last_opened_at DATETIME"))
