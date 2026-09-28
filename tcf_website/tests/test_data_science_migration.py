"""Regression coverage for the Data Science catalog repair."""

from importlib import import_module
from types import SimpleNamespace

from django.apps import apps
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from tcf_website.models import Department, School, Subdepartment

repair = import_module(
    "tcf_website.migrations.0029_school_of_data_science"
).add_school_of_data_science


class DataScienceMigrationTests(TestCase):
    def run_repair(self):
        repair(apps, SimpleNamespace(connection=connection))

    def test_creates_missing_hierarchy_and_browse_link(self):
        School.objects.filter(name="School of Data Science").delete()
        self.run_repair()
        subject = Subdepartment.objects.get(mnemonic="DS")
        self.assertEqual(subject.name, "Data Science")
        self.assertEqual(subject.department.school.name, "School of Data Science")
        School.objects.get_or_create(name="College of Arts & Sciences")
        School.objects.get_or_create(name="School of Engineering & Applied Science")
        response = self.client.get(reverse("browse"))
        self.assertContains(response, "School of Data Science")
        self.assertContains(
            response, reverse("department", args=[subject.department_id])
        )

    def test_reparents_existing_subject_without_duplicates(self):
        School.objects.filter(name="School of Data Science").delete()
        school = School.objects.create(name="Miscellaneous")
        department = Department.objects.create(name="Miscellaneous", school=school)
        subject = Subdepartment.objects.create(
            mnemonic="DS", name="Existing subject name", department=department
        )
        other = Subdepartment.objects.create(
            mnemonic="DSTS", name="Unrelated subject", department=department
        )
        self.run_repair()
        self.run_repair()
        subject.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(subject.department.school.name, "School of Data Science")
        self.assertEqual(subject.name, "Existing subject name")
        self.assertEqual(Subdepartment.objects.get(mnemonic="DS").pk, subject.pk)
        self.assertEqual(other.department_id, department.pk)
        self.assertEqual(
            Department.objects.filter(school=subject.department.school).count(), 1
        )
