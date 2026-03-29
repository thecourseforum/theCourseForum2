from django.test import TestCase
from django.urls import reverse

from .test_utils import setup


class AutocompleteAPITestCase(TestCase):
    def setUp(self):
        setup(self)

    def test_autocomplete_courses(self):
        # Should match course by title
        response = self.client.get(reverse("autocomplete"), {"q": "software"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        print("\nDEBUG courses:", data.get("courses"))
        self.assertIn("courses", data)
        self.assertTrue(any("Software" in c["title"] for c in data["courses"]))

    def test_autocomplete_instructors(self):
        # Should match instructor by name
        response = self.client.get(reverse("autocomplete"), {"q": "jefferson"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("instructors", data)
        self.assertTrue(any("Jefferson" in i["full_name"] for i in data["instructors"]))

    def test_autocomplete_clubs(self):
        # Should return clubs in club mode, expected to be empty since there aren't clubs in the test database
        response = self.client.get(
            reverse("autocomplete"), {"q": "Chess", "mode": "clubs"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("clubs", data)
        self.assertIsInstance(data["clubs"], list)

    def test_autocomplete_empty_query(self):
        # Should return empty lists for empty query
        response = self.client.get(reverse("autocomplete"), {"q": ""})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data, {"courses": [], "instructors": [], "clubs": []})

    def test_autocomplete_no_match(self):
        # Should return empty lists for nonsense query
        response = self.client.get(reverse("autocomplete"), {"q": "zzzzzzzzzz"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(all(len(v) == 0 for v in data.values()))
