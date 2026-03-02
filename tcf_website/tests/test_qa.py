# tcf_website/tests/test_qa.py
"""Tests for the Q&A views."""

from django.test import TestCase
from django.urls import reverse

from ..models import Answer, Question
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
