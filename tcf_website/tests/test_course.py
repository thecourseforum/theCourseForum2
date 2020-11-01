# pylint: disable=no-member
"""Tests for Course model."""

from django.test import Client, TestCase
from django.urls import reverse

from ..api.serializers import CourseSerializer, CourseWithStatsSerializer
from ..models import Semester
from .test_utils import setup


class CourseTestCase(TestCase):
    """Tests for course model."""

    def setUp(self):
        setup(self)

    def test_code(self):
        """Course code string."""
        code = self.course.code()
        self.assertTrue(code == 'CS 420')

    def test_is_recent(self):
        """Test for is_recent()."""

        self.assertTrue(self.course.is_recent())

        Semester.objects.create(
            year=2021,
            season='JANUARY',
            number=1211
        )

        self.assertFalse(self.course.is_recent())

    def test_get_queryset_recent5years_with_stats(self):
        """Test CourseViewSet.get_queryset() with recent5years parameter
        and stats parameters"""
        client = Client()
        response = client.get(path=reverse('course-list'),
                              data={'stats': '', 'recent5years': ''})
        courses = response.json()['results']
        self.assertTrue(len(courses) == 2)
        serializer = CourseWithStatsSerializer(data=courses, many=True)
        self.assertTrue(serializer.is_valid())
        serializer = CourseSerializer(data=courses, many=True)
        self.assertFalse(serializer.is_valid())

    def test_get_queryset_recent5years_without_stats(self):
        """Test CourseViewSet.get_queryset() with recent5years parameter
        but without stats parameters"""
        client = Client()
        response = client.get(path=reverse('course-list'),
                              data={'recent5years': ''})
        courses = response.json()['results']
        self.assertTrue(len(courses) == 2)
        serializer = CourseWithStatsSerializer(data=courses, many=True)
        self.assertFalse(serializer.is_valid())
        serializer = CourseSerializer(data=courses, many=True)
        self.assertTrue(serializer.is_valid())

    def test_get_queryset_all_with_stats(self):
        """Test CourseViewSet.get_queryset() with stats parameter
        but without recent5years parameters"""
        client = Client()
        response = client.get(
            path=reverse('course-list'),
            data={'stats': ''},
        )
        courses = response.json()['results']
        self.assertTrue(len(courses) == 5)
        serializer = CourseWithStatsSerializer(data=courses, many=True)
        self.assertTrue(serializer.is_valid())
        serializer = CourseSerializer(data=courses, many=True)
        self.assertFalse(serializer.is_valid())

    def test_get_queryset_all_without_stats(self):
        """Test CourseViewSet.get_queryset() without recent5years parameter
        or stats parameters"""
        client = Client()
        response = client.get(path=reverse('course-list'))
        courses = response.json()['results']
        self.assertTrue(len(courses) == 5)
        serializer = CourseWithStatsSerializer(data=courses, many=True)
        self.assertFalse(serializer.is_valid())
        serializer = CourseSerializer(data=courses, many=True)
        self.assertTrue(serializer.is_valid())
