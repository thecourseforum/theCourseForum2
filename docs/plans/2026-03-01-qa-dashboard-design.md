# Q&A Dashboard — Design Document

**Date:** 2026-03-01
**Branch:** Q-A
**Status:** Approved

---

## Problem

The `/qa/` dashboard is partially built but non-functional:
- Sidebar post items are not clickable (no JS handler)
- Content panel does not show answers for the selected question
- "New Post" modal has a hardcoded course dropdown and is missing a title field
- No instructor selection in the modal
- `create_question` view uses a placeholder instructor
- No search or course filtering works
- No voting interaction in the dashboard

---

## Decision

Complete the `/qa/` dashboard using the existing `Question`/`Answer` models, mirroring the proven two-panel AJAX architecture of the `/forum/` page.

---

## Architecture

Two-panel layout: left sidebar (question list) + right content panel (selected question + answers).

- **View layer:** `qa_dashboard` view serves the page with annotated questions. A new `question_detail` AJAX endpoint returns a rendered HTML partial for the selected question.
- **Template layer:** `qa_dashboard.html` (updated) + new `_question_detail.html` partial.
- **JS layer:** `qa_dashboard.js` (rewritten) wires up all interactions.

---

## Components

### Views (`views/qa.py`)

| View | Method | Description |
|------|--------|-------------|
| `qa_dashboard` | GET | Renders full page. Accepts `?q=`, `?course=`, `?question=`. Annotates questions with vote counts. |
| `question_detail` | GET | AJAX endpoint. Returns rendered `_question_detail.html` partial. |
| `create_question` | POST | Fixed to use instructor from form POST data. |
| `search_courses_qa` | GET | Returns course search results as JSON. |
| `get_instructors_for_course` | GET | Returns instructors for a given course as JSON. |

### URLs (`urls.py`)

```
qa/question/<int:question_id>/          → question_detail (AJAX)
qa/api/courses/search/                  → search_courses_qa
qa/api/courses/<int:course_id>/instructors/ → get_instructors_for_course
```

### Templates

**`qa_dashboard.html` (updated)**
- Sidebar: clickable `.post-item` elements, course filter dropdown, debounced search input
- Content panel: initial `{% include '_question_detail.html' %}` or empty state
- "New Post" modal: title field, course search autocomplete, instructor dropdown, question text

**`qa/_question_detail.html` (new)**
- Question title, body, metadata (age, author)
- Vote buttons (up/down) wired to existing `/questions/<id>/upvote|downvote/`
- Answers section: each answer shows semester tag, author, text, vote buttons, edit/delete if owner
- Inline "Post an Answer" form at bottom

### JavaScript (`static/qa/qa_dashboard.js` — rewritten)

| Function | Purpose |
|----------|---------|
| `initQuestionSelection()` | Sidebar click → AJAX `question_detail` → inject HTML |
| `initSearch()` | Debounced input → reload page with `?q=` |
| `initCourseFilter()` | Dropdown change → reload with `?course=` |
| `initNewPostModal()` | Open/close, course search autocomplete, instructor load, AJAX submit |
| `initVoting()` | Up/down vote questions and answers via existing endpoints |
| `initAnswerForm()` | Submit answer via AJAX, duplicate check |
| `initAnswerActions()` | Edit/delete answers inline (owner only) |

### Model/View Fixes

- `qa_dashboard` view: use `Question.display_activity()` for vote annotation, pass course list for filter
- `create_question` view: use `request.POST['instructor']` instead of placeholder
- `QuestionForm`: add `title` field

---

## API Endpoints (new)

**`GET /qa/question/<id>/`** — Returns rendered HTML partial for a question and its answers.

**`GET /qa/api/courses/search/?q=<query>`** — Returns `{"results": [{"id", "code", "title"}]}`. Uses trigram similarity.

**`GET /qa/api/courses/<id>/instructors/`** — Returns `{"instructors": [{"id", "name"}]}`.

---

## Authentication & Permissions

- Login required: create question, post answer, vote, edit/delete own content
- Unauthenticated: read-only view; CTAs show "Login to post"
- Permission check: edit/delete only if `obj.user == request.user`

---

## Out of Scope (YAGNI)

- Pagination
- Nested replies (Answer model doesn't support it)
- Accepted answer marking
- Email/push notifications
- Rich text editor

---

## Files to Create/Modify

| File | Action |
|------|--------|
| `tcf_website/views/qa.py` | Modify — fix `create_question`, add `question_detail`, `search_courses_qa`, `get_instructors_for_course` |
| `tcf_website/views/__init__.py` | Modify — export new views |
| `tcf_website/urls.py` | Modify — add 3 new URL patterns |
| `tcf_website/templates/qa/qa_dashboard.html` | Modify — wire up sidebar, modal, filters |
| `tcf_website/templates/qa/_question_detail.html` | Create — question+answers partial |
| `tcf_website/static/qa/qa_dashboard.js` | Rewrite — all interactive logic |
