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
            {
                "title": "Test?",
                "text": "Body",
                "course": self.course.id,
                "instructor": self.instructor.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response["Location"])

    def test_create_question_creates_record(self):
        """Valid POST creates a Question with correct fields."""
        self.client.force_login(self.user1)
        response = self.client.post(
            reverse("create_question"),
            {
                "title": "What is the workload?",
                "text": "How many hours per week?",
                "course": self.course.id,
                "instructor": self.instructor.id,
            },
        )
        self.assertRedirects(response, reverse("qa"), fetch_redirect_response=False)
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

    def test_create_department_question_without_instructor(self):
        """Valid POST can create a department-targeted question without instructor."""
        self.client.force_login(self.user1)
        self.client.post(
            reverse("create_question"),
            {
                "title": "Department elective advice",
                "text": "What are good upper-level electives?",
                "department": self.department.id,
            },
        )
        q = Question.objects.get(user=self.user1, title="Department elective advice")
        self.assertEqual(q.department, self.department)
        self.assertIsNone(q.course)
        self.assertIsNone(q.instructor)

    def test_department_question_ignores_stale_course_and_instructor(self):
        """Department selection should win if stale course/instructor IDs are also posted."""
        self.client.force_login(self.user1)
        self.client.post(
            reverse("create_question"),
            {
                "title": "Department-only target",
                "text": "This should not save to a course.",
                "department": self.department.id,
                "course": self.course.id,
                "instructor": self.instructor.id,
            },
        )

        q = Question.objects.get(user=self.user1, title="Department-only target")
        self.assertEqual(q.department, self.department)
        self.assertIsNone(q.course)
        self.assertIsNone(q.instructor)


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
        self.department_question = Question.objects.create(
            title="Department recommendations",
            text="Any broad CS recommendations?",
            department=self.department,
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
        self.assertNotIn(self.department_question, response.context["questions"])

    def test_dashboard_department_filter_includes_department_and_course_posts(self):
        """?department= includes both department-broad and course-targeted questions."""
        response = self.client.get(reverse("qa") + f"?department={self.department.id}")
        self.assertIn(self.question1, response.context["questions"])
        self.assertIn(self.question2, response.context["questions"])
        self.assertIn(self.department_question, response.context["questions"])

    def test_dashboard_department_broad_scope_filter(self):
        """?scope=department_broad limits to department-targeted posts only."""
        response = self.client.get(
            reverse("qa")
            + f"?department={self.department.id}&scope=department_broad"
        )
        self.assertIn(self.department_question, response.context["questions"])
        self.assertNotIn(self.question1, response.context["questions"])
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

    def test_question_detail_accessible_without_login(self):
        """Unauthenticated request returns 200 (read-only access)."""
        response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )
        self.assertEqual(response.status_code, 200)

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

    def test_question_detail_labels_answer_without_semester(self):
        """Answers without a semester render as not taken yet."""
        Answer.objects.create(
            text="I am planning to take it next term.",
            question=self.question,
            user=self.user1,
            semester=None,
        )

        response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )

        self.assertContains(response, "Not Taken")

    def test_new_answer_accepts_blank_semester(self):
        """Blank semester stores a null semester on the answer."""
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse("new_answer"),
            {
                "text": "I have not taken it yet.",
                "question": self.question.id,
                "semester": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        answer = Answer.objects.get(text="I have not taken it yet.")
        self.assertIsNone(answer.semester)

    def test_user_can_create_multiple_answers_for_same_question(self):
        """A user may post more than one top-level answer to one question."""
        self.client.force_login(self.user1)

        first_response = self.client.post(
            reverse("new_answer"),
            {
                "text": "First answer.",
                "question": self.question.id,
                "semester": self.semester.id,
            },
        )
        second_response = self.client.post(
            reverse("new_answer"),
            {
                "text": "Second answer.",
                "question": self.question.id,
                "semester": self.semester.id,
            },
        )

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 302)
        self.assertEqual(
            Answer.objects.filter(question=self.question, user=self.user1).count(),
            2,
        )

    def test_new_reply_accepts_blank_semester(self):
        """Blank semester stores a null semester on a reply."""
        self.client.force_login(self.user1)

        response = self.client.post(
            reverse("new_reply"),
            {
                "text": "Following because I have not taken it either.",
                "question": self.question.id,
                "parent_answer": self.answer.id,
                "semester": "",
            },
        )

        self.assertEqual(response.status_code, 302)
        reply = Answer.objects.get(text="Following because I have not taken it either.")
        self.assertIsNone(reply.semester)
        self.assertEqual(reply.parent_answer, self.answer)

    def test_question_detail_renders_nested_replies_with_capped_indent(self):
        """Nested replies render recursively and stop increasing indent after level 3."""
        reply_1 = Answer.objects.create(
            text="First reply",
            question=self.question,
            user=self.user1,
            semester=self.semester,
            parent_answer=self.answer,
        )
        reply_2 = Answer.objects.create(
            text="Second reply",
            question=self.question,
            user=self.user2,
            semester=self.semester,
            parent_answer=reply_1,
        )
        reply_3 = Answer.objects.create(
            text="Third reply",
            question=self.question,
            user=self.user1,
            semester=self.semester,
            parent_answer=reply_2,
        )
        Answer.objects.create(
            text="Fourth reply",
            question=self.question,
            user=self.user2,
            semester=self.semester,
            parent_answer=reply_3,
        )

        self.client.force_login(self.user1)
        response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )

        self.assertContains(response, "First reply")
        self.assertContains(response, "Second reply")
        self.assertContains(response, "Third reply")
        self.assertContains(response, "Fourth reply")
        self.assertContains(response, 'class="response-count">(5)</span>', html=True)
        self.assertContains(response, 'data-depth="4"', html=False)
        self.assertContains(response, "thread-depth-3")
        self.assertNotContains(response, "thread-depth-4")

    def test_delete_answer_soft_deletes_and_keeps_replies(self):
        """Deleting an answer leaves a placeholder and preserves nested replies."""
        reply = Answer.objects.create(
            text="Nested reply stays.",
            question=self.question,
            user=self.user1,
            semester=self.semester,
            parent_answer=self.answer,
        )
        self.client.force_login(self.user2)

        response = self.client.post(reverse("delete_answer", args=[self.answer.id]))

        self.assertRedirects(response, reverse("qa"), fetch_redirect_response=False)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.text, "")
        self.assertTrue(Answer.objects.filter(pk=reply.pk).exists())

        detail_response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )
        self.assertContains(detail_response, "[deleted]")
        self.assertContains(detail_response, "Nested reply stays.")

    def test_delete_question_soft_deletes_and_keeps_answers(self):
        """Deleting a question leaves a placeholder and preserves answers."""
        self.client.force_login(self.user1)

        response = self.client.post(reverse("delete_question", args=[self.question.id]))

        self.assertRedirects(response, reverse("qa"), fetch_redirect_response=False)
        self.question.refresh_from_db()
        self.assertEqual(self.question.title, "")
        self.assertEqual(self.question.text, "")
        self.assertTrue(Answer.objects.filter(pk=self.answer.pk).exists())

        detail_response = self.client.get(
            reverse("qa_question_detail", args=[self.question.id])
        )
        self.assertContains(detail_response, "[deleted]")
        self.assertContains(detail_response, "Review lecture notes daily.")

    def test_dashboard_still_lists_soft_deleted_questions(self):
        """Soft-deleted questions remain selectable so their answers stay reachable."""
        self.question.soft_delete()
        self.client.force_login(self.user1)

        response = self.client.get(reverse("qa") + f"?question={self.question.id}")

        self.assertEqual(response.status_code, 200)
        self.assertIn(self.question, response.context["questions"])
        self.assertEqual(response.context["selected_question"].id, self.question.id)
        self.assertContains(response, "[deleted]")

    @suppress_request_warnings
    def test_question_detail_404_for_nonexistent(self):
        """Returns 404 for a nonexistent question ID."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("qa_question_detail", args=[99999]))
        self.assertEqual(response.status_code, 404)


class SearchCoursesQaTests(TestCase):
    """Tests for search_courses_qa API."""

    def setUp(self):
        setup(self)

    def test_short_query_returns_empty(self):
        """Short (1-char) query returns empty results per min-length guard."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("qa_search_courses") + "?q=a")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["results"], [])

    def test_course_search_returns_json(self):
        """Course search endpoint returns JSON with results key."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("qa_search_courses") + "?q=CS")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertIsInstance(data["results"], list)

    def test_search_returns_department_results(self):
        """Search endpoint includes department matches in the same result set."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("qa_search_courses") + "?q=Computer")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(
            any(item.get("type") == "department" for item in data["results"])
        )


class GetInstructorsForCourseTests(TestCase):
    """Tests for get_instructors_for_course API."""

    def setUp(self):
        setup(self)

    def test_returns_instructors_for_course(self):
        """Returns instructors who have taught the course."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("qa_get_instructors", args=[self.course.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("instructors", data)
        instructor_ids = [i["id"] for i in data["instructors"]]
        self.assertIn(self.instructor.id, instructor_ids)

    @suppress_request_warnings
    def test_returns_404_for_invalid_course(self):
        """Returns 404 for a nonexistent course ID."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("qa_get_instructors", args=[99999]))
        self.assertEqual(response.status_code, 404)


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
        response = self.client.get(reverse("qa_question_detail", args=[question.id]))
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
        response = self.client.get(reverse("qa_question_detail", args=[question.id]))
        self.assertContains(response, "Yes, there is a generous curve.")
