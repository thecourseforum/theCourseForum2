# Q&A Dashboard — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fully implement the `/qa/` dashboard so users can browse, create, answer, search, filter, and vote on questions — mirroring the proven UX of the `/forum/` page.

**Architecture:** Two-panel AJAX layout. A `question_detail` AJAX endpoint renders a partial template for the right panel. The `qa_dashboard` view handles filtering/search. All JS interaction lives in `qa_dashboard.js`.

**Tech Stack:** Django 4.x, PostgreSQL (trigram for course search), vanilla `fetch` API (no jQuery for new code), Bootstrap 4 (already loaded), Font Awesome icons (already loaded).

---

## Context & Key Files

Before starting, read these files to understand the shape of the code:

- `tcf_website/views/qa.py` — existing Q&A views (create_question is broken; edit_question has a missing import for datetime)
- `tcf_website/views/forum.py` — reference implementation (AJAX, voting, course search)
- `tcf_website/models/models.py` lines 1422–1690 — Question, Answer, VoteQuestion, VoteAnswer models
- `tcf_website/templates/qa/qa_dashboard.html` — current template
- `tcf_website/templates/forum/_post_detail.html` — reference partial
- `tcf_website/static/forum/forum_dashboard.js` — reference JS
- `tcf_website/tests/test_utils.py` — `setup()` helper used in all tests

**Run tests with:**
```bash
python manage.py test tcf_website.tests.test_qa -v 2
```

---

## Task 1: Fix QuestionForm and create_question view

The `create_question` view currently uses a hardcoded placeholder instructor and doesn't use the form. The `QuestionForm` also doesn't include `title`.

**Files:**
- Modify: `tcf_website/views/qa.py`
- Create: `tcf_website/tests/test_qa.py`

**Step 1: Create the test file with failing tests**

```python
# tcf_website/tests/test_qa.py
"""Tests for the Q&A views."""

from urllib.parse import urlencode

from django.test import TestCase
from django.urls import reverse

from ..models import Question
from .test_utils import setup, suppress_request_warnings


class CreateQuestionTests(TestCase):
    """Tests for the create_question view."""

    def setUp(self):
        setup(self)

    def test_create_question_requires_login(self):
        """Unauthenticated POST is redirected to login."""
        response = self.client.post(
            reverse("create_question"),
            {"title": "Test?", "text": "Body", "course": self.course.id, "instructor": self.instructor.id},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response["Location"])

    def test_create_question_creates_record(self):
        """Valid POST creates a Question with correct fields."""
        self.client.force_login(self.user1)
        self.client.post(
            reverse("create_question"),
            {
                "title": "What is the workload?",
                "text": "How many hours per week?",
                "course": self.course.id,
                "instructor": self.instructor.id,
            },
        )
        q = Question.objects.get(user=self.user1)
        self.assertEqual(q.title, "What is the workload?")
        self.assertEqual(q.text, "How many hours per week?")
        self.assertEqual(q.instructor, self.instructor)

    def test_create_question_redirects_to_qa(self):
        """Valid POST redirects to /qa/."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("create_question"),
            {
                "title": "Test title",
                "text": "Test body text here",
                "course": self.course.id,
                "instructor": self.instructor.id,
            },
        )
        self.assertRedirects(response, reverse("qa"), fetch_redirect_response=False)
```

**Step 2: Run tests to verify they fail**

```bash
python manage.py test tcf_website.tests.test_qa.CreateQuestionTests -v 2
```
Expected: Some tests fail because `create_question` uses a placeholder instructor and `QuestionForm` lacks `title`.

**Step 3: Fix QuestionForm to include title**

In `tcf_website/views/qa.py`, update `QuestionForm`:

```python
class QuestionForm(forms.ModelForm):
    """Form for question creation"""

    class Meta:
        model = Question
        fields = ["title", "text", "course", "instructor"]
```

**Step 4: Fix create_question view**

Replace the existing `create_question` function in `tcf_website/views/qa.py`:

```python
@login_required
def create_question(request):
    """Create a new question via the Q&A dashboard modal."""
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.user = request.user
            instance.save()
        # Redirect regardless of validation (modal POST pattern)
        return redirect("qa")
    return redirect("qa")
```

**Step 5: Run tests to verify they pass**

```bash
python manage.py test tcf_website.tests.test_qa.CreateQuestionTests -v 2
```
Expected: All 3 tests PASS.

**Step 6: Commit**

```bash
git add tcf_website/views/qa.py tcf_website/tests/test_qa.py
git commit -m "fix(qa): fix create_question view and add title to QuestionForm"
```

---

## Task 2: Update qa_dashboard view with filtering and vote annotation

The dashboard view currently passes questions without vote annotations and has no support for search/filter/question-selection query params.

**Files:**
- Modify: `tcf_website/views/qa.py`
- Modify: `tcf_website/tests/test_qa.py`

**Step 1: Write failing tests**

Add to `tcf_website/tests/test_qa.py`:

```python
class QaDashboardTests(TestCase):
    """Tests for the qa_dashboard view."""

    def setUp(self):
        setup(self)
        self.question1 = Question.objects.create(
            title="Workload?",
            text="How hard is this course?",
            course=self.course,
            instructor=self.instructor,
            user=self.user1,
        )
        self.question2 = Question.objects.create(
            title="Exams?",
            text="How many exams?",
            course=self.course2,
            instructor=self.instructor,
            user=self.user2,
        )
        self.client.force_login(self.user1)

    def test_dashboard_returns_200(self):
        """Dashboard page loads successfully."""
        response = self.client.get(reverse("qa"))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_contains_questions(self):
        """Dashboard context includes all questions."""
        response = self.client.get(reverse("qa"))
        self.assertIn(self.question1, response.context["questions"])
        self.assertIn(self.question2, response.context["questions"])

    def test_dashboard_search_filter(self):
        """?q= param filters questions by title/text."""
        response = self.client.get(reverse("qa") + "?q=Workload")
        self.assertIn(self.question1, response.context["questions"])
        self.assertNotIn(self.question2, response.context["questions"])

    def test_dashboard_course_filter(self):
        """?course= param filters questions by course."""
        response = self.client.get(reverse("qa") + f"?course={self.course.id}")
        self.assertIn(self.question1, response.context["questions"])
        self.assertNotIn(self.question2, response.context["questions"])

    def test_dashboard_selected_question(self):
        """?question= param sets the active question in context."""
        response = self.client.get(reverse("qa") + f"?question={self.question2.id}")
        self.assertEqual(response.context["selected_question"].id, self.question2.id)

    def test_dashboard_has_courses_in_context(self):
        """Dashboard context includes courses list for filter dropdown."""
        response = self.client.get(reverse("qa"))
        self.assertIn("courses_with_questions", response.context)
```

**Step 2: Run tests to verify they fail**

```bash
python manage.py test tcf_website.tests.test_qa.QaDashboardTests -v 2
```
Expected: Several tests fail (context keys missing, no filtering).

**Step 3: Rewrite qa_dashboard view**

Replace the existing `qa_dashboard` function in `tcf_website/views/qa.py`:

```python
@login_required
def qa_dashboard(request):
    """Q&A Dashboard view."""
    from django.db.models import Q as DQ

    search_query = request.GET.get("q", "").strip()
    course_filter = request.GET.get("course", "")
    selected_question_id = request.GET.get("question", None)

    # Base queryset annotated with vote totals
    questions = (
        Question.objects.select_related("course", "course__subdepartment", "instructor", "user")
        .exclude(text="")
        .annotate(
            sum_q_votes=models.functions.Coalesce(
                models.Sum("votequestion__value"), models.Value(0)
            )
        )
    )

    if request.user.is_authenticated:
        questions = questions.annotate(
            user_q_vote=models.functions.Coalesce(
                models.Sum(
                    "votequestion__value",
                    filter=models.Q(votequestion__user=request.user),
                ),
                models.Value(0),
            )
        )

    if search_query:
        questions = questions.filter(
            DQ(title__icontains=search_query) | DQ(text__icontains=search_query)
        )

    if course_filter:
        questions = questions.filter(course_id=course_filter)

    questions = questions.order_by("-created")

    # Determine selected question
    selected_question = None
    answers = []
    if selected_question_id:
        try:
            selected_question = questions.get(id=selected_question_id)
        except Question.DoesNotExist:
            pass
    if selected_question is None and questions.exists():
        selected_question = questions.first()

    if selected_question:
        answers = Answer.display_activity(
            question_id=selected_question.id,
            user=request.user,
        )

    # Courses that have at least one question (for filter dropdown)
    from ..models import Course
    courses_with_questions = (
        Course.objects.filter(question__isnull=False)
        .select_related("subdepartment")
        .distinct()
        .order_by("subdepartment__mnemonic", "number")
    )

    return render(
        request,
        "qa/qa_dashboard.html",
        {
            "questions": questions,
            "selected_question": selected_question,
            "answers": answers,
            "courses_with_questions": courses_with_questions,
            "search_query": search_query,
            "selected_course": course_filter,
        },
    )
```

Also add these imports at the top of `qa.py` (they are needed):
- `from ..models import Answer, Course, Question` (update existing import)
- `from django.db import models` (add if not present)

**Step 4: Run tests**

```bash
python manage.py test tcf_website.tests.test_qa.QaDashboardTests -v 2
```
Expected: All 6 tests PASS.

**Step 5: Commit**

```bash
git add tcf_website/views/qa.py tcf_website/tests/test_qa.py
git commit -m "feat(qa): update qa_dashboard with search, course filter, vote annotation"
```

---

## Task 3: Add question_detail AJAX view

This view returns rendered HTML for the right panel when a user clicks a question in the sidebar.

**Files:**
- Modify: `tcf_website/views/qa.py`
- Modify: `tcf_website/tests/test_qa.py`

**Step 1: Write failing tests**

Add to `tcf_website/tests/test_qa.py`:

```python
class QuestionDetailTests(TestCase):
    """Tests for the question_detail AJAX view."""

    def setUp(self):
        setup(self)
        self.question = Question.objects.create(
            title="Best study tips?",
            text="What study strategies work well?",
            course=self.course,
            instructor=self.instructor,
            user=self.user1,
        )
        self.answer = Answer.objects.create(
            text="Review lecture notes daily.",
            question=self.question,
            user=self.user2,
            semester=self.semester,
        )

    def test_question_detail_requires_login(self):
        """Unauthenticated request redirects to login."""
        response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )
        self.assertEqual(response.status_code, 302)

    def test_question_detail_returns_200(self):
        """Returns 200 for a valid question ID."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_question_detail_contains_question_text(self):
        """Response HTML contains the question text."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )
        self.assertContains(response, "What study strategies work well?")

    def test_question_detail_contains_answer(self):
        """Response HTML contains the answer text."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )
        self.assertContains(response, "Review lecture notes daily.")

    @suppress_request_warnings
    def test_question_detail_404_for_nonexistent(self):
        """Returns 404 for a nonexistent question ID."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("qa_question_detail", args=[99999])
        )
        self.assertEqual(response.status_code, 404)
```

**Step 2: Add the URL name to urls.py (needed for reverse())**

Add to `tcf_website/urls.py` before the `# API URLs` comment:

```python
path(
    "qa/question/<int:question_id>/",
    views.qa.question_detail,
    name="qa_question_detail",
),
```

**Step 3: Run tests to verify they fail**

```bash
python manage.py test tcf_website.tests.test_qa.QuestionDetailTests -v 2
```
Expected: Tests fail because `question_detail` view doesn't exist yet.

**Step 4: Implement question_detail view**

Add to `tcf_website/views/qa.py` after the `qa_dashboard` function:

```python
@login_required
def question_detail(request, question_id):
    """AJAX endpoint: returns rendered HTML partial for a question + its answers."""
    question = get_object_or_404(Question, pk=question_id)

    # Annotate the question with vote data
    from django.db.models import Sum, Value
    import django.db.models.functions as func

    question_qs = Question.objects.filter(pk=question_id).annotate(
        sum_q_votes=func.Coalesce(
            models.Sum("votequestion__value"), models.Value(0)
        )
    )
    if request.user.is_authenticated:
        question_qs = question_qs.annotate(
            user_q_vote=func.Coalesce(
                models.Sum(
                    "votequestion__value",
                    filter=models.Q(votequestion__user=request.user),
                ),
                models.Value(0),
            )
        )
    question = question_qs.first()

    answers = Answer.display_activity(question_id=question.id, user=request.user)
    semesters = Semester.objects.order_by("-number")[:20]

    return render(
        request,
        "qa/_question_detail.html",
        {
            "question": question,
            "answers": answers,
            "semesters": semesters,
        },
    )
```

Also add `Semester` to the import at top of `qa.py`:
```python
from ..models import Answer, Course, Question, Semester
```

**Step 5: Run tests**

```bash
python manage.py test tcf_website.tests.test_qa.QuestionDetailTests -v 2
```
Expected: Tests that test `reverse()` will pass (URL resolves). Tests checking content will fail until template is created (Task 6). For now that's OK — we're building incrementally.

**Step 6: Commit**

```bash
git add tcf_website/views/qa.py tcf_website/urls.py tcf_website/tests/test_qa.py
git commit -m "feat(qa): add question_detail AJAX endpoint"
```

---

## Task 4: Add search_courses_qa and get_instructors_for_course API views

These two JSON endpoints power the course search autocomplete and instructor dropdown in the "New Post" modal.

**Files:**
- Modify: `tcf_website/views/qa.py`
- Modify: `tcf_website/tests/test_qa.py`

**Step 1: Write failing tests**

Add to `tcf_website/tests/test_qa.py`:

```python
from ..models import Answer  # add this import at top of file

class SearchCoursesQaTests(TestCase):
    """Tests for search_courses_qa API."""

    def setUp(self):
        setup(self)

    def test_empty_query_returns_empty(self):
        """Short query returns empty results."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("qa_search_courses") + "?q=a")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["results"], [])

    def test_course_search_returns_matches(self):
        """Query matching a course returns that course."""
        self.client.force_login(self.user1)
        # course.combined_mnemonic_number = "CS1420" (set by Course.save())
        response = self.client.get(reverse("qa_search_courses") + "?q=CS")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreater(len(data["results"]), 0)
        codes = [r["code"] for r in data["results"]]
        self.assertTrue(any("CS" in c for c in codes))


class GetInstructorsForCourseTests(TestCase):
    """Tests for get_instructors_for_course API."""

    def setUp(self):
        setup(self)

    def test_returns_instructors_for_course(self):
        """Returns instructors who have taught the course."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("qa_get_instructors", args=[self.course.id])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        instructor_ids = [i["id"] for i in data["instructors"]]
        self.assertIn(self.instructor.id, instructor_ids)

    @suppress_request_warnings
    def test_returns_404_for_invalid_course(self):
        """Returns 404 for a nonexistent course ID."""
        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("qa_get_instructors", args=[99999])
        )
        self.assertEqual(response.status_code, 404)
```

**Step 2: Add URL names to urls.py**

Add to `tcf_website/urls.py`:

```python
path(
    "qa/api/courses/search/",
    views.qa.search_courses_qa,
    name="qa_search_courses",
),
path(
    "qa/api/courses/<int:course_id>/instructors/",
    views.qa.get_instructors_for_course,
    name="qa_get_instructors",
),
```

**Step 3: Run tests to verify they fail**

```bash
python manage.py test tcf_website.tests.test_qa.SearchCoursesQaTests tcf_website.tests.test_qa.GetInstructorsForCourseTests -v 2
```
Expected: FAIL — views don't exist yet.

**Step 4: Implement the two API views**

Add to `tcf_website/views/qa.py`:

```python
def search_courses_qa(request):
    """API: search courses by mnemonic/number for the New Post modal."""
    from django.contrib.postgres.search import TrigramSimilarity

    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({"results": []})

    courses = (
        Course.objects.annotate(
            similarity=TrigramSimilarity("combined_mnemonic_number", query)
        )
        .filter(similarity__gte=0.1)
        .select_related("subdepartment")
        .order_by("-similarity")[:10]
    )

    results = [
        {
            "id": course.id,
            "code": f"{course.subdepartment.mnemonic} {course.number}",
            "title": course.title,
        }
        for course in courses
    ]
    return JsonResponse({"results": results})


def get_instructors_for_course(request, course_id):
    """API: get instructors who have taught a given course."""
    from ..models import Instructor, Section

    course = get_object_or_404(Course, pk=course_id)
    instructors = (
        Instructor.objects.filter(section__course=course)
        .distinct()
        .order_by("last_name", "first_name")
    )
    return JsonResponse(
        {
            "instructors": [
                {"id": i.id, "name": f"{i.first_name} {i.last_name}".strip()}
                for i in instructors
            ]
        }
    )
```

Also update the import at top of `qa.py` to include `Instructor` and `Section` won't be needed at module level (they're imported inside the function).

**Step 5: Run tests**

```bash
python manage.py test tcf_website.tests.test_qa.SearchCoursesQaTests tcf_website.tests.test_qa.GetInstructorsForCourseTests -v 2
```
Expected: All tests PASS.

**Step 6: Commit**

```bash
git add tcf_website/views/qa.py tcf_website/urls.py tcf_website/tests/test_qa.py
git commit -m "feat(qa): add course search and instructor API endpoints"
```

---

## Task 5: Export new views from views/__init__.py

**Files:**
- Modify: `tcf_website/views/__init__.py`

**Step 1: Update the qa imports**

In `tcf_website/views/__init__.py`, the `from .qa import (...)` block currently exports:

```python
from .qa import (
    DeleteAnswer,
    DeleteQuestion,
    downvote_answer,
    downvote_question,
    edit_answer,
    edit_question,
    new_answer,
    new_question,
    qa_dashboard,
    qa_dashboard_hard,
    upvote_answer,
    upvote_question,
)
```

Add `create_question`, `question_detail`, `search_courses_qa`, `get_instructors_for_course` to the list:

```python
from .qa import (
    DeleteAnswer,
    DeleteQuestion,
    create_question,
    downvote_answer,
    downvote_question,
    edit_answer,
    edit_question,
    get_instructors_for_course,
    new_answer,
    new_question,
    qa_dashboard,
    qa_dashboard_hard,
    question_detail,
    search_courses_qa,
    upvote_answer,
    upvote_question,
)
```

Note: `create_question` was already in urls.py as `views.qa.create_question`, so it didn't need to be exported before — but now we need consistency.

**Step 2: Verify the server starts without import errors**

```bash
python manage.py check
```
Expected: `System check identified no issues (0 silenced).`

**Step 3: Commit**

```bash
git add tcf_website/views/__init__.py
git commit -m "feat(qa): export new qa views"
```

---

## Task 6: Create _question_detail.html partial template

This partial renders the right panel: question content, answers, and the answer submission form.

**Files:**
- Create: `tcf_website/templates/qa/_question_detail.html`

**Step 1: Create the template**

```html
{% load static %}

<!-- Top Navigation -->
<div class="content-nav">
    <div class="post-info">
        {% if question.course %}
        <h3>
            <a href="{% url 'course' mnemonic=question.course.subdepartment.mnemonic course_number=question.course.number %}">
                {{ question.course.subdepartment.mnemonic }} {{ question.course.number }}
            </a>
        </h3>
        {% endif %}
    </div>
    {% if user.is_authenticated and user == question.user %}
    <div class="dropdown">
        <button class="nav-btn dropdown-toggle" type="button" data-toggle="dropdown">
            <i class="fa fa-ellipsis-v"></i>
        </button>
        <div class="dropdown-menu dropdown-menu-right">
            <a class="dropdown-item edit-question-btn" href="#"
               data-question-id="{{ question.id }}"
               data-title="{{ question.title }}"
               data-text="{{ question.text }}">
                <i class="fa fa-pencil"></i> Edit
            </a>
            <a class="dropdown-item delete-question-btn text-danger" href="#"
               data-question-id="{{ question.id }}">
                <i class="fa fa-trash"></i> Delete
            </a>
        </div>
    </div>
    {% endif %}
</div>

<!-- Post Content -->
<div class="post-content">
    <!-- Main Question -->
    <div class="main-question">
        <h2 class="post-content-title">{{ question.title|default:"(No title)" }}</h2>
        <div class="post-meta">
            <span class="post-author">
                <i class="fa fa-user"></i>
                {{ question.user.first_name|default:question.user.computing_id|default:"Anonymous" }}
            </span>
            <span class="post-timestamp">
                <i class="fa fa-clock-o"></i> {{ question.created|timesince }} ago
            </span>
        </div>

        <div class="post-body">
            <p>{{ question.text|linebreaks }}</p>
        </div>

        <!-- Question Vote Actions -->
        <div class="post-actions">
            {% if user.is_authenticated %}
            <button class="action-btn vote-btn {% if question.user_q_vote == 1 %}voted{% endif %}"
                    data-type="question"
                    data-id="{{ question.id }}"
                    data-action="up">
                <i class="fa fa-thumbs-up"></i>
            </button>
            <span class="vote-count" id="question-vote-count-{{ question.id }}">
                {{ question.sum_q_votes|default:0 }}
            </span>
            <button class="action-btn vote-btn {% if question.user_q_vote == -1 %}voted{% endif %}"
                    data-type="question"
                    data-id="{{ question.id }}"
                    data-action="down">
                <i class="fa fa-thumbs-down"></i>
            </button>
            {% else %}
            <span class="vote-display">
                <i class="fa fa-thumbs-up"></i> {{ question.sum_q_votes|default:0 }}
            </span>
            {% endif %}
        </div>
    </div>

    <!-- Answers Section -->
    <div class="comments-section">
        <h3 class="comments-header">
            Answers
            <span class="response-count">({{ answers|length }})</span>
        </h3>

        <div class="thread-container" id="answersContainer">
            {% for answer in answers %}
            <div class="thread-post" data-answer-id="{{ answer.id }}">
                <div class="post-main">
                    <div class="post-header-info">
                        {% if answer.semester %}
                        <span class="semester-tag">{{ answer.semester }}</span>
                        {% endif %}
                        <span class="response-author">
                            {{ answer.user.first_name|default:answer.user.computing_id|default:"Anonymous" }}
                        </span>
                        <span class="post-time">{{ answer.created|timesince }} ago</span>
                    </div>
                    <div class="post-body">
                        <p>{{ answer.text|linebreaks }}</p>
                    </div>
                    <div class="post-actions">
                        {% if user.is_authenticated %}
                        <button class="action-btn vote-btn {% if answer.user_a_vote == 1 %}voted{% endif %}"
                                data-type="answer"
                                data-id="{{ answer.id }}"
                                data-action="up">
                            <i class="fa fa-thumbs-up"></i>
                        </button>
                        <span class="vote-count" id="answer-vote-count-{{ answer.id }}">
                            {{ answer.sum_a_votes|default:0 }}
                        </span>
                        <button class="action-btn vote-btn {% if answer.user_a_vote == -1 %}voted{% endif %}"
                                data-type="answer"
                                data-id="{{ answer.id }}"
                                data-action="down">
                            <i class="fa fa-thumbs-down"></i>
                        </button>

                        {% if user == answer.user %}
                        <div class="dropdown d-inline-block">
                            <button class="action-btn dropdown-toggle" type="button" data-toggle="dropdown">
                                <i class="fa fa-ellipsis-h"></i>
                            </button>
                            <div class="dropdown-menu dropdown-menu-right">
                                <a class="dropdown-item edit-answer-btn" href="#"
                                   data-answer-id="{{ answer.id }}"
                                   data-text="{{ answer.text }}"
                                   data-semester="{{ answer.semester.id|default:'' }}">
                                    <i class="fa fa-pencil"></i> Edit
                                </a>
                                <a class="dropdown-item delete-answer-btn text-danger" href="#"
                                   data-answer-id="{{ answer.id }}">
                                    <i class="fa fa-trash"></i> Delete
                                </a>
                            </div>
                        </div>
                        {% endif %}
                        {% else %}
                        <span class="vote-display">
                            <i class="fa fa-thumbs-up"></i> {{ answer.sum_a_votes|default:0 }}
                        </span>
                        {% endif %}
                    </div>
                </div>
            </div>
            <hr>
            {% empty %}
            <div class="no-responses">
                <p>No answers yet. Be the first to answer!</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Answer Submission Form -->
    {% if user.is_authenticated %}
    <div class="reply-input-container">
        <form id="mainAnswerForm" method="POST" action="{% url 'new_answer' %}">
            {% csrf_token %}
            <input type="hidden" name="question" value="{{ question.id }}">
            <div class="reply-input-wrapper">
                <div class="reply-form-row mb-2">
                    <select name="semester" class="form-control semester-select" required>
                        <option value="">Select semester you took this course...</option>
                        {% for semester in semesters %}
                        <option value="{{ semester.id }}">{{ semester }}</option>
                        {% endfor %}
                    </select>
                </div>
                <textarea class="reply-textarea"
                          name="text"
                          placeholder="Write your answer..."
                          required></textarea>
                <div class="d-flex align-items-center mt-2">
                    <span id="duplicate-answer-warning" class="text-danger mr-3" style="display:none;">
                        You have already answered this question.
                    </span>
                    <button type="submit" class="btn-submit-reply ml-auto">Post Answer</button>
                </div>
            </div>
        </form>
    </div>
    {% else %}
    <div class="login-prompt">
        <a href="{% url 'login' %}">Login</a> to post an answer.
    </div>
    {% endif %}
</div>
```

**Step 2: Run the question_detail tests that check content**

```bash
python manage.py test tcf_website.tests.test_qa.QuestionDetailTests -v 2
```
Expected: All 5 tests PASS now that the template exists.

**Step 3: Commit**

```bash
git add tcf_website/templates/qa/_question_detail.html
git commit -m "feat(qa): add _question_detail.html partial template"
```

---

## Task 7: Update qa_dashboard.html template

Wire up the sidebar (clickable post items, course filter, search), update the "New Post" modal (add title, course search autocomplete, instructor dropdown), and show the `_question_detail.html` partial in the right panel.

**Files:**
- Modify: `tcf_website/templates/qa/qa_dashboard.html`

**Step 1: Replace the entire template**

```html
{% extends "base/base.html" %}
{% load static %}

{% block title %}Q&A | theCourseForum{% endblock %}

{% block styles %}
    <link rel="stylesheet" href="{% static 'qa/qa_dashboard.css' %}">
{% endblock %}

{% block content %}
<div class="qa-container">
    <!-- Left Sidebar: Posts List -->
    <div class="qa-sidebar">
        <!-- Header with New Post button and Search -->
        <div class="qa-header">
            {% if user.is_authenticated %}
            <button class="btn-new-post" id="openNewPostModal">
                <i class="fa fa-plus"></i> New Post
            </button>
            {% else %}
            <a href="{% url 'login' %}" class="btn-new-post">
                <i class="fa fa-sign-in"></i> Login to Post
            </a>
            {% endif %}
            <div class="search-container">
                <i class="fa fa-search search-icon"></i>
                <input type="text"
                       class="search-input"
                       id="searchInput"
                       placeholder="Search questions..."
                       value="{{ search_query }}">
            </div>
        </div>

        <!-- Course Filter -->
        <div class="qa-filters">
            <div class="dropdown">
                <button class="filter-btn dropdown-toggle" type="button" id="courseDropdown" data-toggle="dropdown">
                    <i class="fa fa-filter"></i>
                    {% if selected_course %}
                        Filter active
                    {% else %}
                        All Courses
                    {% endif %}
                </button>
                <div class="dropdown-menu" aria-labelledby="courseDropdown">
                    <a class="dropdown-item {% if not selected_course %}active{% endif %}"
                       href="{% url 'qa' %}{% if search_query %}?q={{ search_query }}{% endif %}">
                        All Courses
                    </a>
                    {% for course in courses_with_questions %}
                    <a class="dropdown-item {% if selected_course == course.id|stringformat:'s' %}active{% endif %}"
                       href="{% url 'qa' %}?course={{ course.id }}{% if search_query %}&q={{ search_query }}{% endif %}">
                        {{ course.subdepartment.mnemonic }} {{ course.number }}
                    </a>
                    {% endfor %}
                </div>
            </div>
        </div>

        <!-- Posts List -->
        <div class="posts-list" id="postsList">
            {% for question in questions %}
            <div class="post-item {% if selected_question.id == question.id %}active{% endif %}"
                 data-question-id="{{ question.id }}">
                <div class="post-header">
                    <span class="post-tag">
                        {{ question.course.subdepartment.mnemonic }} {{ question.course.number }}
                    </span>
                    <span class="post-title">{{ question.title|default:question.text|truncatechars:30 }}</span>
                    <span class="post-date">{{ question.created|date:"n/j/y" }}</span>
                </div>
                <div class="post-preview">
                    {{ question.text|truncatechars:80 }}
                </div>
                <div class="post-footer">
                    <span class="post-stats">
                        <i class="fa fa-thumbs-up"></i> {{ question.sum_q_votes|default:0 }}
                    </span>
                </div>
            </div>
            {% empty %}
            <div class="no-posts">
                <i class="fa fa-comments-o fa-3x mb-3"></i>
                <p>No questions found.</p>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- Right Content: Question Detail -->
    <div class="qa-content" id="questionContent">
        {% if selected_question %}
        {% include 'qa/_question_detail.html' with question=selected_question answers=answers %}
        {% else %}
        <div class="no-post-selected">
            <i class="fa fa-hand-o-left fa-3x mb-3"></i>
            <p>Select a question to view its details</p>
        </div>
        {% endif %}
    </div>
</div>

<!-- New Post Modal -->
<div id="newPostModal" class="modal-overlay" style="display: none;">
    <div class="modal-container">
        <div class="modal-header">
            <h2>Ask a Question</h2>
            <button class="modal-close" id="closeModal">
                <i class="fa fa-times"></i>
            </button>
        </div>
        <form id="newPostForm" method="POST" action="{% url 'create_question' %}">
            {% csrf_token %}
            <div class="modal-body">
                <div class="form-group">
                    <label for="postTitle">Title <span class="required">*</span></label>
                    <input type="text"
                           id="postTitle"
                           name="title"
                           class="form-control"
                           placeholder="e.g. How hard is the final exam?"
                           required
                           maxlength="200">
                </div>
                <div class="form-group">
                    <label for="courseSearch">Course <span class="required">*</span></label>
                    <input type="text"
                           id="courseSearch"
                           class="form-control"
                           placeholder="Search for a course (e.g. CS 2100)..."
                           autocomplete="off"
                           required>
                    <input type="hidden" id="courseId" name="course">
                    <div id="courseResults" class="course-search-results"></div>
                </div>
                <div class="form-group">
                    <label for="instructorSelect">Instructor <span class="required">*</span></label>
                    <select id="instructorSelect" name="instructor" class="form-control" required disabled>
                        <option value="">Select a course first...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="postText">Question <span class="required">*</span></label>
                    <textarea id="postText"
                              name="text"
                              class="form-control"
                              placeholder="Describe your question in detail..."
                              required
                              rows="4"></textarea>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn-cancel" id="cancelModal">Cancel</button>
                <button type="submit" class="btn-submit">Post Question</button>
            </div>
        </form>
    </div>
</div>

<!-- Edit Question Modal -->
<div id="editQuestionModal" class="modal-overlay" style="display: none;">
    <div class="modal-container">
        <div class="modal-header">
            <h2>Edit Question</h2>
            <button class="modal-close" id="closeEditModal">
                <i class="fa fa-times"></i>
            </button>
        </div>
        <form id="editQuestionForm" method="POST">
            {% csrf_token %}
            <div class="modal-body">
                <div class="form-group">
                    <label for="editTitle">Title</label>
                    <input type="text" id="editTitle" name="title" class="form-control" maxlength="200">
                </div>
                <div class="form-group">
                    <label for="editText">Question</label>
                    <textarea id="editText" name="text" class="form-control" rows="4" required></textarea>
                </div>
                <!-- course and instructor are required by form but shouldn't change on edit -->
                <input type="hidden" id="editCourse" name="course">
                <input type="hidden" id="editInstructor" name="instructor">
            </div>
            <div class="modal-footer">
                <button type="button" class="btn-cancel" id="cancelEditModal">Cancel</button>
                <button type="submit" class="btn-submit">Save Changes</button>
            </div>
        </form>
    </div>
</div>

<!-- Edit Answer Modal -->
<div id="editAnswerModal" class="modal-overlay" style="display: none;">
    <div class="modal-container">
        <div class="modal-header">
            <h2>Edit Answer</h2>
            <button class="modal-close" id="closeEditAnswerModal">
                <i class="fa fa-times"></i>
            </button>
        </div>
        <form id="editAnswerForm" method="POST">
            {% csrf_token %}
            <div class="modal-body">
                <div class="form-group">
                    <label for="editAnswerSemester">Semester</label>
                    <select id="editAnswerSemester" name="semester" class="form-control">
                        {% for semester in semesters %}
                        <option value="{{ semester.id }}">{{ semester }}</option>
                        {% endfor %}
                    </select>
                </div>
                <div class="form-group">
                    <label for="editAnswerText">Answer</label>
                    <textarea id="editAnswerText" name="text" class="form-control" rows="4" required></textarea>
                </div>
                <input type="hidden" id="editAnswerQuestion" name="question">
            </div>
            <div class="modal-footer">
                <button type="button" class="btn-cancel" id="cancelEditAnswerModal">Cancel</button>
                <button type="submit" class="btn-submit">Save Changes</button>
            </div>
        </form>
    </div>
</div>

{% endblock %}

{% block js %}
<script>
    const QA_URLS = {
        questionDetail: '{% url "qa_question_detail" question_id=0 %}'.replace('0', ''),
        createQuestion: '{% url "create_question" %}',
        searchCourses: '{% url "qa_search_courses" %}',
        getInstructors: '{% url "qa_get_instructors" course_id=0 %}'.replace('0', ''),
        upvoteQuestion: '/questions/',
        downvoteQuestion: '/questions/',
        upvoteAnswer: '/answers/',
        downvoteAnswer: '/answers/',
        editQuestion: '{% url "edit_question" question_id=0 %}'.replace('0', ''),
        deleteQuestion: '/questions/',
        editAnswer: '{% url "edit_answer" answer_id=0 %}'.replace('0', ''),
        deleteAnswer: '/answers/',
        checkDuplicate: '{% url "answers/check_duplicate/" %}',
        dashboard: '{% url "qa" %}',
    };
    const IS_AUTHENTICATED = {{ user.is_authenticated|yesno:"true,false" }};
    const CSRF_TOKEN = '{{ csrf_token }}';
    {% if selected_question %}
    const SEMESTERS = [
        {% for semester in semesters %}
        {"id": {{ semester.id }}, "label": "{{ semester }}"}{% if not forloop.last %},{% endif %}
        {% endfor %}
    ];
    {% endif %}
</script>
<script src="{% static 'qa/qa_dashboard.js' %}"></script>
{% endblock %}
```

Note: The `semesters` variable needs to be added to the `qa_dashboard` context. Go back to `qa_dashboard` view in `qa.py` and add:
```python
semesters = Semester.objects.order_by("-number")[:20]
```
And pass it in the `render()` context dict as `"semesters": semesters`.

**Step 2: Verify page loads**

```bash
python manage.py test tcf_website.tests.test_qa.QaDashboardTests -v 2
```
Expected: All tests still pass.

**Step 3: Commit**

```bash
git add tcf_website/templates/qa/qa_dashboard.html tcf_website/views/qa.py
git commit -m "feat(qa): update qa_dashboard.html with wired sidebar and modals"
```

---

## Task 8: Rewrite qa_dashboard.js

This is the bulk of the interactive logic.

**Files:**
- Modify: `tcf_website/static/qa/qa_dashboard.js`

**Step 1: Replace the entire file**

```javascript
/**
 * Q&A Dashboard JavaScript
 * Handles all interactive functionality for the Q&A dashboard.
 */

document.addEventListener('DOMContentLoaded', function () {
    initQuestionSelection();
    initSearch();
    initNewPostModal();
    initVoting();
    initAnswerForm();
    initQuestionActions();
    initAnswerActions();
});

// ─── Question Selection ───────────────────────────────────────────────────────

function initQuestionSelection() {
    document.querySelectorAll('.post-item').forEach(item => {
        item.addEventListener('click', function () {
            const questionId = this.dataset.questionId;
            loadQuestionDetail(questionId);

            document.querySelectorAll('.post-item').forEach(p => p.classList.remove('active'));
            this.classList.add('active');

            const url = new URL(window.location);
            url.searchParams.set('question', questionId);
            window.history.pushState({}, '', url);
        });
    });
}

function loadQuestionDetail(questionId) {
    const contentArea = document.getElementById('questionContent');
    contentArea.classList.add('loading');

    fetch(`${QA_URLS.questionDetail}${questionId}/`)
        .then(r => r.text())
        .then(html => {
            contentArea.innerHTML = html;
            contentArea.classList.remove('loading');
            // Re-initialise handlers for newly injected HTML
            initVoting();
            initAnswerForm();
            initQuestionActions();
            initAnswerActions();
        })
        .catch(() => {
            contentArea.classList.remove('loading');
            contentArea.innerHTML = '<div class="no-post-selected"><p>Error loading question. Please try again.</p></div>';
        });
}

// ─── Search ───────────────────────────────────────────────────────────────────

function initSearch() {
    const input = document.getElementById('searchInput');
    if (!input) return;

    let timeout;
    input.addEventListener('input', function () {
        clearTimeout(timeout);
        const q = this.value.trim();
        timeout = setTimeout(() => {
            const url = new URL(window.location);
            if (q) url.searchParams.set('q', q);
            else url.searchParams.delete('q');
            url.searchParams.delete('question');
            window.location.href = url.toString();
        }, 500);
    });

    input.addEventListener('keypress', function (e) {
        if (e.key === 'Enter') {
            clearTimeout(timeout);
            const url = new URL(window.location);
            const q = this.value.trim();
            if (q) url.searchParams.set('q', q);
            else url.searchParams.delete('q');
            url.searchParams.delete('question');
            window.location.href = url.toString();
        }
    });
}

// ─── New Post Modal ───────────────────────────────────────────────────────────

function initNewPostModal() {
    const modal = document.getElementById('newPostModal');
    if (!modal) return;

    const openBtn = document.getElementById('openNewPostModal');
    const closeBtn = document.getElementById('closeModal');
    const cancelBtn = document.getElementById('cancelModal');
    const form = document.getElementById('newPostForm');
    const courseSearchInput = document.getElementById('courseSearch');
    const courseIdInput = document.getElementById('courseId');
    const courseResults = document.getElementById('courseResults');
    const instructorSelect = document.getElementById('instructorSelect');

    function openModal() {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        modal.style.display = 'none';
        document.body.style.overflow = '';
        if (form) form.reset();
        if (courseIdInput) courseIdInput.value = '';
        if (courseResults) courseResults.classList.remove('show');
        if (instructorSelect) {
            instructorSelect.innerHTML = '<option value="">Select a course first...</option>';
            instructorSelect.disabled = true;
        }
    }

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);
    modal.addEventListener('click', e => { if (e.target === modal) closeModal(); });

    // Course search autocomplete
    if (courseSearchInput) {
        let searchTimeout;
        courseSearchInput.addEventListener('input', function () {
            clearTimeout(searchTimeout);
            const q = this.value.trim();
            if (q.length < 2) {
                courseResults.classList.remove('show');
                return;
            }
            searchTimeout = setTimeout(() => {
                fetch(`${QA_URLS.searchCourses}?q=${encodeURIComponent(q)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.results && data.results.length > 0) {
                            courseResults.innerHTML = data.results.map(c =>
                                `<div class="course-result-item" data-id="${c.id}" data-code="${c.code}">
                                    <div class="course-result-code">${c.code}</div>
                                    <div class="course-result-title">${c.title}</div>
                                </div>`
                            ).join('');
                            courseResults.classList.add('show');

                            courseResults.querySelectorAll('.course-result-item').forEach(item => {
                                item.addEventListener('click', function () {
                                    courseIdInput.value = this.dataset.id;
                                    courseSearchInput.value = this.dataset.code;
                                    courseResults.classList.remove('show');
                                    loadInstructors(this.dataset.id);
                                });
                            });
                        } else {
                            courseResults.innerHTML = '<div class="course-result-item text-muted">No courses found</div>';
                            courseResults.classList.add('show');
                        }
                    });
            }, 300);
        });

        courseSearchInput.addEventListener('keydown', function (e) {
            if (e.key === 'Backspace' && courseIdInput.value) {
                courseIdInput.value = '';
                instructorSelect.innerHTML = '<option value="">Select a course first...</option>';
                instructorSelect.disabled = true;
            }
        });

        document.addEventListener('click', function (e) {
            if (!courseSearchInput.contains(e.target) && !courseResults.contains(e.target)) {
                courseResults.classList.remove('show');
            }
        });
    }

    function loadInstructors(courseId) {
        if (!instructorSelect) return;
        instructorSelect.disabled = true;
        instructorSelect.innerHTML = '<option value="">Loading...</option>';

        fetch(`${QA_URLS.getInstructors}${courseId}/`)
            .then(r => r.json())
            .then(data => {
                if (data.instructors && data.instructors.length > 0) {
                    instructorSelect.innerHTML =
                        '<option value="">Select an instructor...</option>' +
                        data.instructors.map(i =>
                            `<option value="${i.id}">${i.name}</option>`
                        ).join('');
                    instructorSelect.disabled = false;
                } else {
                    instructorSelect.innerHTML = '<option value="">No instructors found</option>';
                }
            })
            .catch(() => {
                instructorSelect.innerHTML = '<option value="">Error loading instructors</option>';
            });
    }
}

// ─── Voting ───────────────────────────────────────────────────────────────────

function initVoting() {
    document.querySelectorAll('.vote-btn').forEach(btn => {
        // Remove duplicate listeners by cloning
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);

        newBtn.addEventListener('click', function () {
            if (!IS_AUTHENTICATED) {
                window.location.href = '/login/';
                return;
            }

            const type = this.dataset.type;   // 'question' or 'answer'
            const id = this.dataset.id;
            const action = this.dataset.action; // 'up' or 'down'

            let url;
            if (type === 'question') {
                url = action === 'up'
                    ? `/questions/${id}/upvote/`
                    : `/questions/${id}/downvote/`;
            } else {
                url = action === 'up'
                    ? `/answers/${id}/upvote/`
                    : `/answers/${id}/downvote/`;
            }

            const counterId = type === 'question'
                ? `question-vote-count-${id}`
                : `answer-vote-count-${id}`;

            fetch(url, {
                method: 'POST',
                headers: { 'X-CSRFToken': CSRF_TOKEN },
            })
            .then(r => r.json())
            .then(data => {
                if (data.ok) {
                    // Toggle voted state and update displayed count
                    const container = this.closest('.post-actions');
                    const upBtn = container.querySelector('[data-action="up"]');
                    const downBtn = container.querySelector('[data-action="down"]');
                    const counterEl = document.getElementById(counterId);

                    const wasVoted = this.classList.contains('voted');
                    upBtn.classList.remove('voted');
                    downBtn.classList.remove('voted');
                    if (!wasVoted) this.classList.add('voted');

                    if (counterEl) {
                        let current = parseInt(counterEl.textContent) || 0;
                        if (action === 'up') {
                            counterEl.textContent = wasVoted ? current - 1 : current + 1;
                        } else {
                            counterEl.textContent = wasVoted ? current + 1 : current - 1;
                        }
                    }
                }
            })
            .catch(err => console.error('Vote error:', err));
        });
    });
}

// ─── Answer Form ──────────────────────────────────────────────────────────────

function initAnswerForm() {
    const form = document.getElementById('mainAnswerForm');
    if (!form) return;

    const newForm = form.cloneNode(true);
    form.parentNode.replaceChild(newForm, form);

    newForm.addEventListener('submit', function (e) {
        e.preventDefault();

        const warning = document.getElementById('duplicate-answer-warning');
        if (warning) warning.style.display = 'none';

        const formData = new FormData(newForm);
        const submitBtn = newForm.querySelector('.btn-submit-reply');

        // Check for duplicates first
        fetch('/answers/check_duplicate/', {
            method: 'POST',
            body: formData,
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        })
        .then(r => r.json())
        .then(data => {
            if (data.duplicate) {
                if (warning) warning.style.display = 'inline';
            } else {
                submitBtn.disabled = true;
                submitBtn.textContent = 'Posting...';

                fetch(newForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: { 'X-Requested-With': 'XMLHttpRequest' },
                })
                .then(() => {
                    // Reload the current question detail
                    const url = new URL(window.location);
                    const questionId = url.searchParams.get('question');
                    const activeItem = document.querySelector('.post-item.active');
                    const qId = questionId || (activeItem && activeItem.dataset.questionId);
                    if (qId) loadQuestionDetail(qId);
                })
                .catch(err => console.error('Answer submit error:', err))
                .finally(() => {
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Post Answer';
                });
            }
        })
        .catch(err => console.error('Duplicate check error:', err));
    });
}

// ─── Question Actions (Edit / Delete) ────────────────────────────────────────

function initQuestionActions() {
    const editModal = document.getElementById('editQuestionModal');

    document.querySelectorAll('.edit-question-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            if (!editModal) return;

            const qId = this.dataset.questionId;
            document.getElementById('editTitle').value = this.dataset.title || '';
            document.getElementById('editText').value = this.dataset.text || '';
            document.getElementById('editCourse').value = this.dataset.course || '';
            document.getElementById('editInstructor').value = this.dataset.instructor || '';
            document.getElementById('editQuestionForm').action = `${QA_URLS.editQuestion}${qId}/`;

            editModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    });

    const closeEditBtn = document.getElementById('closeEditModal');
    const cancelEditBtn = document.getElementById('cancelEditModal');
    function closeEditModal() {
        if (editModal) {
            editModal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
    if (closeEditBtn) closeEditBtn.addEventListener('click', closeEditModal);
    if (cancelEditBtn) cancelEditBtn.addEventListener('click', closeEditModal);
    if (editModal) editModal.addEventListener('click', e => { if (e.target === editModal) closeEditModal(); });

    document.querySelectorAll('.delete-question-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const qId = this.dataset.questionId;
            if (confirm('Are you sure you want to delete this question?')) {
                fetch(`/questions/${qId}/delete/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': CSRF_TOKEN },
                })
                .then(() => {
                    window.location.href = QA_URLS.dashboard;
                })
                .catch(err => console.error('Delete question error:', err));
            }
        });
    });
}

// ─── Answer Actions (Edit / Delete) ──────────────────────────────────────────

function initAnswerActions() {
    const editAnswerModal = document.getElementById('editAnswerModal');

    document.querySelectorAll('.edit-answer-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            if (!editAnswerModal) return;

            const answerId = this.dataset.answerId;
            document.getElementById('editAnswerText').value = this.dataset.text || '';
            const semSelect = document.getElementById('editAnswerSemester');
            if (semSelect && this.dataset.semester) semSelect.value = this.dataset.semester;
            // Set the question hidden field from the form on the page
            const mainForm = document.getElementById('mainAnswerForm');
            const questionId = mainForm ? mainForm.querySelector('[name="question"]').value : '';
            document.getElementById('editAnswerQuestion').value = questionId;
            document.getElementById('editAnswerForm').action = `${QA_URLS.editAnswer}${answerId}/`;

            editAnswerModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';
        });
    });

    function closeEditAnswerModal() {
        if (editAnswerModal) {
            editAnswerModal.style.display = 'none';
            document.body.style.overflow = '';
        }
    }
    const closeBtn = document.getElementById('closeEditAnswerModal');
    const cancelBtn = document.getElementById('cancelEditAnswerModal');
    if (closeBtn) closeBtn.addEventListener('click', closeEditAnswerModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeEditAnswerModal);
    if (editAnswerModal) editAnswerModal.addEventListener('click', e => {
        if (e.target === editAnswerModal) closeEditAnswerModal();
    });

    document.querySelectorAll('.delete-answer-btn').forEach(btn => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
            const answerId = this.dataset.answerId;
            if (confirm('Are you sure you want to delete this answer?')) {
                fetch(`/answers/${answerId}/delete/`, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': CSRF_TOKEN },
                })
                .then(() => {
                    // Reload current question
                    const url = new URL(window.location);
                    const qId = url.searchParams.get('question');
                    const activeItem = document.querySelector('.post-item.active');
                    const questionId = qId || (activeItem && activeItem.dataset.questionId);
                    if (questionId) loadQuestionDetail(questionId);
                })
                .catch(err => console.error('Delete answer error:', err));
            }
        });
    });
}
```

**Step 2: Also add CSS for course search results dropdown and loading state to qa_dashboard.css**

Append to `tcf_website/static/qa/qa_dashboard.css`:

```css
/* Course Search Results */
.course-search-results {
    display: none;
    position: absolute;
    z-index: 1050;
    background: white;
    border: 1px solid #ced4da;
    border-top: none;
    border-radius: 0 0 4px 4px;
    max-height: 200px;
    overflow-y: auto;
    width: 100%;
}

.course-search-results.show {
    display: block;
}

.course-result-item {
    padding: 0.5rem 0.75rem;
    cursor: pointer;
    border-bottom: 1px solid #f0f0f0;
}

.course-result-item:hover {
    background: #f8f9fa;
}

.course-result-code {
    font-weight: 600;
    font-size: 0.875rem;
}

.course-result-title {
    font-size: 0.8rem;
    color: #6c757d;
}

/* Loading state for content panel */
.qa-content.loading {
    opacity: 0.5;
    pointer-events: none;
}

/* No post selected / empty state */
.no-post-selected,
.no-posts {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #6c757d;
    text-align: center;
    padding: 2rem;
}

/* Voted button state */
.vote-btn.voted {
    color: var(--main-color);
}

/* Login prompt */
.login-prompt {
    padding: 1rem 2rem;
    color: #6c757d;
}

/* Form group relative for dropdown */
.form-group {
    position: relative;
}

/* Required asterisk */
.required {
    color: red;
}
```

**Step 3: Verify delete question/answer routes exist**

The delete views use Django's `DeleteView` pattern which expects a POST to `/questions/<pk>/delete/` and `/answers/<pk>/delete/`. Check that these are correctly wired (they are — they use `DeleteQuestion` and `DeleteAnswer` class-based views). However, these redirect to `course_instructor` after deletion — which won't work well for the dashboard. Update `DeleteQuestion.get_success_url` and `DeleteAnswer.get_success_url` to redirect to `/qa/` instead:

In `tcf_website/views/qa.py`, update `DeleteQuestion`:
```python
def get_success_url(self):
    return reverse_lazy("qa")
```

And update `DeleteAnswer`:
```python
def get_success_url(self):
    return reverse_lazy("qa")
```

**Step 4: Manual test — open the browser and verify**

1. Start the server: `python manage.py runserver`
2. Navigate to `http://localhost:8000/qa/`
3. Verify:
   - Clicking a question in the sidebar loads it in the right panel (AJAX)
   - "New Post" button opens the modal
   - Course search autocomplete works in modal
   - Instructor dropdown populates after selecting a course
   - Submitting a question creates it and redirects back
   - Search input filters questions in sidebar
   - Course filter dropdown filters by course
   - Voting up/down on questions and answers updates counts
   - "Post Answer" form works and reloads panel

**Step 5: Run the full test suite**

```bash
python manage.py test tcf_website.tests.test_qa -v 2
```
Expected: All tests pass.

**Step 6: Commit**

```bash
git add tcf_website/static/qa/qa_dashboard.js tcf_website/static/qa/qa_dashboard.css tcf_website/views/qa.py
git commit -m "feat(qa): rewrite qa_dashboard.js with full interactive functionality"
```

---

## Task 9: Fix edit_question and edit_answer views (missing datetime import)

Both `edit_question` and `edit_answer` reference `datetime.datetime.now()` but `datetime` is never imported. These views will crash if called.

**Files:**
- Modify: `tcf_website/views/qa.py`

**Step 1: Add import**

At the top of `tcf_website/views/qa.py`, add:
```python
import datetime
```

**Step 2: Verify tests pass**

```bash
python manage.py test tcf_website.tests.test_qa -v 2
```

**Step 3: Commit**

```bash
git add tcf_website/views/qa.py
git commit -m "fix(qa): add missing datetime import in edit views"
```

---

## Task 10: Write integration smoke test

A final test that exercises the full user flow.

**Files:**
- Modify: `tcf_website/tests/test_qa.py`

**Step 1: Add smoke test**

```python
class QaDashboardIntegrationTest(TestCase):
    """End-to-end smoke test for the Q&A dashboard flow."""

    def setUp(self):
        setup(self)

    def test_full_qa_flow(self):
        """User creates a question, another user answers it."""
        self.client.force_login(self.user1)

        # Create question
        response = self.client.post(
            reverse("create_question"),
            {
                "title": "How is the grading?",
                "text": "Is it curve-based?",
                "course": self.course.id,
                "instructor": self.instructor.id,
            },
        )
        self.assertRedirects(response, reverse("qa"), fetch_redirect_response=False)

        question = Question.objects.get(title="How is the grading?")

        # Load question detail AJAX
        self.client.force_login(self.user2)
        response = self.client.get(
            reverse("qa_question_detail", args=[question.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Is it curve-based?")

        # Post answer
        response = self.client.post(
            reverse("new_answer"),
            {
                "text": "Yes, there is a generous curve.",
                "question": question.id,
                "semester": self.semester.id,
            },
        )
        self.assertEqual(response.status_code, 302)

        # Verify answer appears in detail
        response = self.client.get(
            reverse("qa_question_detail", args=[question.id])
        )
        self.assertContains(response, "Yes, there is a generous curve.")
```

**Step 2: Run test**

```bash
python manage.py test tcf_website.tests.test_qa.QaDashboardIntegrationTest -v 2
```
Expected: PASS.

**Step 3: Commit**

```bash
git add tcf_website/tests/test_qa.py
git commit -m "test(qa): add integration smoke test for full Q&A flow"
```

---

## Final Checklist

Before considering this complete:

- [ ] `python manage.py test tcf_website.tests.test_qa -v 2` — all pass
- [ ] `python manage.py check` — no errors
- [ ] Manual browser test: sidebar clicks, modal, course search, voting, answer posting, edit, delete
- [ ] No JavaScript console errors on the page
- [ ] `git log --oneline` shows clean commits for each task
