from django.apps import apps
from django.test import TestCase
from django.urls import reverse

from ..management.instructor_merge import merge_instructor_into
from ..models import Instructor, InstructorRedirect
from .test_utils import setup


class InstructorRedirectTestCase(TestCase):
    def setUp(self):
        setup(self)
        self.old_id = self.instructor2.id
        merge_instructor_into(apps, self.instructor, self.instructor2)

    def test_merge_records_redirect(self):
        self.assertFalse(Instructor.objects.filter(pk=self.old_id).exists())
        self.assertEqual(
            InstructorRedirect.objects.get(old_id=self.old_id).instructor_id,
            self.instructor.id,
        )

    def test_instructor_page_redirects_permanently(self):
        response = self.client.get(
            reverse("instructor", args=[self.old_id]), {"latest": "false"}
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"],
            reverse("instructor", args=[self.instructor.id]) + "?latest=false",
        )

    def test_course_instructor_page_redirects_permanently(self):
        response = self.client.get(
            reverse("course_instructor", args=[self.course.id, self.old_id])
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"],
            reverse("course_instructor", args=[self.course.id, self.instructor.id]),
        )

    def test_sort_reviews_page_redirects_permanently(self):
        response = self.client.get(
            reverse("sort_reviews", args=[self.course.id, self.old_id, "Helpful"])
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(
            response["Location"],
            reverse(
                "sort_reviews", args=[self.course.id, self.instructor.id, "Helpful"]
            ),
        )

    def test_chained_merge_points_to_final_instructor(self):
        final = Instructor.objects.create(first_name="Final", last_name="Row")
        middle_id = self.instructor.id
        merge_instructor_into(apps, final, self.instructor)
        self.assertEqual(
            set(
                InstructorRedirect.objects.filter(instructor=final).values_list(
                    "old_id", flat=True
                )
            ),
            {self.old_id, middle_id},
        )

    def test_unknown_instructor_still_404s(self):
        response = self.client.get(reverse("instructor", args=[987654321]))
        self.assertEqual(response.status_code, 404)
