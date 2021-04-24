# pylint: disable=no-member
"""Tests for SavedCourse model."""

from django.test import TestCase
from django.urls import reverse
from .test_utils import setup, suppress_request_warnings
from ..models import SavedCourse


class SavedCourseReorderingTests(TestCase):
    """Tests for the SavedCourseReorderingView."""

    def setUp(self):
        setup(self)
        self.client.force_login(self.user1)
        self.saved1 = SavedCourse.objects.create(
            user=self.user1,
            course=self.course,
            instructor=self.instructor,
        )
        self.saved2 = SavedCourse.objects.create(
            user=self.user1,
            course=self.course2,
            instructor=self.instructor,
        )
        self.saved3 = SavedCourse.objects.create(
            user=self.user1,
            course=self.course3,
            instructor=self.instructor,
        )
        self.saved4 = SavedCourse.objects.create(
            user=self.user1,
            course=self.course4,
            instructor=self.instructor,
        )

    def test_saved_courses(self):
        """Test if the 4 saved courses show up for user1"""
        response = self.client.post(reverse('courses'))
        saved = response.context['courses']
        # 4 SavedCourses (saved1, saved2, saved3, saved4)
        self.assertEqual(len(list(saved)), 4)

    def test_move_saved_course_one_step(self):
        """Move saved4 to the front of saved3"""
        path = reverse('reorder_saved_courses')
        data = {'to_move_id': self.saved4.id, 'successor_id': self.saved3.id}
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 200)
        self.assertLess(self.saved3.rank, self.saved4.rank)
        self.saved3.refresh_from_db()
        self.saved4.refresh_from_db()
        self.assertGreater(self.saved3.rank, self.saved4.rank)

    def test_move_saved_course_to_the_end(self):
        """Move saved1, which was created first, to the very end"""
        path = reverse('reorder_saved_courses')
        data = {'to_move_id': self.saved1.id}  # No `successor_id`
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 200)
        # saved1 was created first -> lowest rank at first
        for saved in [self.saved2, self.saved3, self.saved4]:
            self.assertLess(self.saved1.rank, saved.rank)
            saved.refresh_from_db()
        self.saved1.refresh_from_db()
        # saved1 was moved to the end -> highest rank now
        for saved in [self.saved2, self.saved3, self.saved4]:
            self.assertGreater(self.saved1.rank, saved.rank)

    @suppress_request_warnings
    def test_reorder_saved_courses_invalid_to_move_id(self):
        """Call `reorder_saved_courses` with invalid `to_move_id`"""
        path = reverse('reorder_saved_courses')
        data = {'to_move_id': 'not_a_number', 'successor_id': self.saved1.id}
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    @suppress_request_warnings
    def test_reorder_saved_courses_invalid_successor_id(self):
        """Call `reorder_saved_courses` with invalid `successor_id`"""
        path = reverse('reorder_saved_courses')
        data = {'to_move_id': self.saved4.id, 'successor_id': 'not_a_number'}
        response = self.client.post(path, data)
        self.assertEqual(response.status_code, 400)

    def test_save_course(self):
        """Call `save_course` with valid data"""
        self.client.force_login(self.user2)
        same_as_saved1 = (self.saved1.course.id, self.saved1.instructor.id)
        path = reverse('save_course', args=same_as_saved1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 200)

    @suppress_request_warnings
    def test_save_course_twice(self):
        """Try saving an already saved course-instructor pair."""
        same_as_saved1 = (self.saved1.course.id, self.saved1.instructor.id)
        path = reverse('save_course', args=same_as_saved1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 400)

    @suppress_request_warnings
    def test_save_course_with_invalid_course_instructor_pair(self):
        """Try saving course-instructor pair for which there is no Section."""
        invalid_pair = (self.course5.id, self.instructor.id)
        path = reverse('save_course', args=invalid_pair)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 400)

    def test_unsave_course(self):
        """Try unsaving a saved course."""
        same_as_saved1 = (self.saved1.course.id, self.saved1.instructor.id)
        path = reverse('unsave_course', args=same_as_saved1)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 204)

    def test_unsave_course_with_invalid_course_instructor_pair(self):
        """Try unsaving a course-instructor pair that has not been saved."""
        random_pair = (12345, 67890)
        path = reverse('unsave_course', args=random_pair)
        response = self.client.post(path)
        self.assertEqual(response.status_code, 204)
