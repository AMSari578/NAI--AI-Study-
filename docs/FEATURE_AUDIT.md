# NAI Study feature audit

This file maps the complete product prompt to implemented, testable product areas. The NAI Study identity uses blue `#2563EB`, violet `#7C3AED`, amber `#F59E0B`, and neutral `#64748B`.

## Study loop and dashboard

- Today dashboard: tasks, reminders, upcoming exams, due flashcards, weak topics, recent lectures, and true continuation of the last opened material.
- Interactive study modes: Teach Me, Quick Review, and Quiz Me.
- Contextual tutor actions: simplify, show an example, break down, quiz, and “I don't understand”.
- Review center: due cards, intentionally marked items, stored mistakes, and “Study this mistake with NAI Study”.
- Progress: study sessions, minutes, answers, flashcard reviews, and per-topic mastery labels.

## Materials and contextual AI

- Private PDF/image/text uploads with owner-protected file delivery.
- PDF reader with page navigation, zoom, fullscreen, extracted page text, and split tutor view.
- Material, page, and selected-text context can be sent to the tutor.
- Selected text can be explained, simplified, summarized, converted into a real flashcard or quiz, or saved as a real note.
- All generative tools can target a specific subject, lecture, and material instead of silently choosing one.

## Learning artifacts

- Five summary modes: simple, detailed, key points, exam review, and memorize; Arabic/English; saved and copyable.
- Flashcards: manual and AI creation, answer reveal, Again/Hard/Good/Easy spaced scheduling, due queue, and progress tracking.
- Quizzes: MCQ with four options, True/False, and essay/short answer; answers remain editable until submission.
- Correct answers are not returned to the browser before submission. Semantic educational feedback records correct, missing, and incorrect concepts.
- Concept maps: material-grounded hierarchy in an interactive zoomable/pannable React Flow canvas.
- Rich notes: headings, emphasis, highlights, lists, checklists, links, tables, and AI summarize/organize/explain/key-points/flashcard/quiz actions.

## Exams, planning, and focus

- Mock exams support multiple lectures, question types, difficulty, count, and time limit. Answers are hidden until submission.
- Exams include subject, date, included lectures, and notes.
- Manual and AI study plans support scheduled activities, completion, skipping, rescheduling, and recalculation.
- Month/week calendar combines plan items, exams, tasks, and reminders.
- Focus mode supports lecture/material choice, timer, notes, tutor access, and persisted study sessions.

## Library, search, and productivity

- Subjects, lectures, summaries, tests, tasks, reminders, and settings remain in the established top-navigation design.
- Private global search covers subjects, lectures, materials, summaries, notes, flashcards, and quiz questions.
- Tasks support inline creation, completion, deletion, due dates, and full-list access.
- Existing summary and test result libraries support subject/lecture filtering and bulk deletion.

## Architecture, privacy, and reliability

- FastAPI routers are split by domain: study, reader, memory, exam mode, planning, search, notes AI, auth, library, and productivity.
- SQLAlchemy models cover pages, spaced repetition, exams, plans, sessions, progress, and review items.
- Nested resources are resolved through the authenticated user's subject ownership; cross-user access returns 404.
- Uploaded files are served only through authenticated ownership checks.
- AI providers remain isolated behind the provider abstraction, with local/offline fallback.
- Loading, empty, and recoverable error states exist across the new workspaces.
- Automated coverage verifies the full local study flow, semantic feedback, reader actions, spaced review, planning, search, mock exams, hidden answers, continuation, and cross-user denial.
