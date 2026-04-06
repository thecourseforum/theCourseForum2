# pylint: disable=no-member
"""Redirects, ``next`` / ``state`` URLs, Referer fallbacks, and login gates."""

from unittest.mock import MagicMock, patch

from django.contrib.messages import get_messages
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse

from ..models import Schedule, ScheduledCourse, User
from ..utils import safe_next_url
from .base import TCFDataTestCase

# ---------------------------------------------------------------------------
# safe_next_url and open-redirect hardening (RequestFactory + Client)
# ---------------------------------------------------------------------------


class SafeNextUrlRedirectTestCase(TestCase):
    """Reject off-site ``next``; accept same-host paths."""

    def test_rejects_full_url_to_other_host(self):
        """Absolute URL to another host must not be used."""
        factory = RequestFactory()
        request = factory.get(
            "/schedule/",
            {"next": "https://evil.example/phish"},
            HTTP_HOST="testserver",
        )
        self.assertEqual(safe_next_url(request, "/schedule/"), "/schedule/")

    def test_rejects_protocol_relative_evil_host(self):
        """Protocol-relative URLs are not safe next targets."""
        factory = RequestFactory()
        request = factory.get(
            "/",
            {"next": "//evil.example/path"},
            HTTP_HOST="testserver",
        )
        self.assertEqual(safe_next_url(request, "/browse/"), "/browse/")

    def test_accepts_same_host_path_with_query(self):
        """Path + query on the current host is allowed."""
        factory = RequestFactory()
        target = "/course/CS/1420/?sortby=rating"
        request = factory.post(
            "/schedule/new/",
            {"next": target, "name": "x"},
            HTTP_HOST="testserver",
        )
        self.assertEqual(safe_next_url(request, "/schedule/"), target)

    def test_post_next_overrides_get_for_safe_next_url(self):
        """POST body wins when both GET and POST supply ``next``."""
        factory = RequestFactory()
        request = factory.post(
            "/?next=/ignored/",
            {"next": "/browse/", "name": "Plan"},
            HTTP_HOST="testserver",
        )
        self.assertEqual(safe_next_url(request, "/schedule/"), "/browse/")


# ---------------------------------------------------------------------------
# Auth: login, Cognito callback state, logout
# ---------------------------------------------------------------------------


@override_settings(
    COGNITO_DOMAIN="https://test-pool.auth.us-east-1.amazoncognito.com",
    COGNITO_APP_CLIENT_ID="test-client-id",
    COGNITO_APP_CLIENT_SECRET="test-secret",
    COGNITO_REDIRECT_URI="/cognito-callback/",
)
class AuthRedirectTestCase(TCFDataTestCase):
    """Cognito entry/exit URLs and post-login ``state`` handling."""

    def test_login_anonymous_sends_user_to_cognito_with_client_id(self):
        """Unauthenticated GET /login/ redirects to hosted UI."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("https://test-pool.auth."))
        self.assertIn("client_id=test-client-id", response.url)
        self.assertIn("redirect_uri=", response.url)

    def test_login_anonymous_appends_quoted_state_from_next(self):
        """``next`` is passed through Cognito as ``state`` (quoted)."""
        response = self.client.get(
            reverse("login"),
            {"next": "/schedule/?semester=1"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("state=", response.url)

    def test_login_authenticated_redirects_to_profile(self):
        """Logged-in users hitting /login/ go to profile with a message."""
        self.client.force_login(self.user1)
        response = self.client.get(reverse("login"))
        self.assertRedirects(
            response,
            reverse("profile"),
            fetch_redirect_response=False,
        )

    def test_cognito_callback_without_code_redirects_home(self):
        """Missing ``code`` is a failed auth attempt."""
        response = self.client.get(reverse("cognito_callback"))
        self.assertRedirects(
            response,
            reverse("index"),
            fetch_redirect_response=False,
        )

    @patch("tcf_website.views.auth.authenticate")
    @patch("tcf_website.views.auth.requests.post")
    def test_cognito_callback_safe_relative_state_redirect(
        self, mock_post, mock_authenticate
    ):
        """After token exchange, safe ``state`` becomes the redirect target."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"id_token": "fake.jwt.token"}
        user = self.user1
        user.backend = "django.contrib.auth.backends.ModelBackend"
        mock_authenticate.return_value = user

        response = self.client.get(
            reverse("cognito_callback"),
            {"code": "auth-code", "state": "/browse/"},
        )
        self.assertRedirects(
            response,
            "/browse/",
            fetch_redirect_response=False,
        )

    @patch("tcf_website.views.auth.authenticate")
    @patch("tcf_website.views.auth.requests.post")
    def test_cognito_callback_unsafe_state_falls_back_to_browse(
        self, mock_post, mock_authenticate
    ):
        """Off-site ``state`` is ignored; default is browse."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"id_token": "fake.jwt.token"}
        user = self.user1
        user.backend = "django.contrib.auth.backends.ModelBackend"
        mock_authenticate.return_value = user

        response = self.client.get(
            reverse("cognito_callback"),
            {
                "code": "auth-code",
                "state": "https://evil.example/stolen-session",
            },
        )
        self.assertRedirects(
            response,
            reverse("browse"),
            fetch_redirect_response=False,
        )

    @patch("tcf_website.views.auth.authenticate")
    @patch("tcf_website.views.auth.requests.post")
    def test_cognito_callback_no_state_goes_to_browse(
        self, mock_post, mock_authenticate
    ):
        """Successful login without ``state`` opens browse."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"id_token": "fake.jwt.token"}
        user = self.user1
        user.backend = "django.contrib.auth.backends.ModelBackend"
        mock_authenticate.return_value = user

        response = self.client.get(
            reverse("cognito_callback"),
            {"code": "auth-code"},
        )
        self.assertRedirects(
            response,
            reverse("browse"),
            fetch_redirect_response=False,
        )

    def test_logout_post_redirects_to_cognito_logout(self):
        """Logout clears session and sends user to Cognito logout URL."""
        self.client.force_login(self.user1)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("test-pool.auth.", response.url)
        self.assertIn("logout_uri=", response.url)


# ---------------------------------------------------------------------------
# Login-required gates preserve ``next``
# ---------------------------------------------------------------------------


class LoginRequiredNextParamTestCase(TCFDataTestCase):
    """Anonymous users are sent to login with return path."""

    def test_schedule_requires_login_with_next(self):
        """Anonymous schedule builder redirects to login with encoded return URL."""
        response = self.client.get(reverse("schedule"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertIn("next=", response.url)

    def test_new_schedule_requires_login(self):
        """Creating a schedule requires authentication."""
        response = self.client.get(reverse("new_schedule"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


# ---------------------------------------------------------------------------
# Schedule builder: GET/POST redirects and ``next``
# ---------------------------------------------------------------------------


class ScheduleFlowRedirectTestCase(TCFDataTestCase):
    """new/edit/delete/duplicate/remove and ``safe_next_url`` wiring."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_get_new_schedule_honors_next_query_param(self):
        """GET /schedule/new/ always redirects; ``next`` can steer it."""
        target = reverse("browse")
        response = self.client.get(
            reverse("new_schedule"),
            {"next": target},
        )
        self.assertRedirects(response, target, fetch_redirect_response=False)

    def test_post_new_schedule_success_redirects_to_new_schedule(self):
        """Valid create always redirects to the newly created schedule, ignoring ``next``."""
        response = self.client.post(
            reverse("new_schedule"),
            {
                "name": "Redirect test plan",
                "semester": str(self.semester.pk),
                "next": reverse("browse"),  # should be ignored
            },
        )
        created = Schedule.objects.get(name="Redirect test plan", user=self.user1)
        self.assertRedirects(
            response,
            f"{reverse('schedule')}?schedule={created.pk}",
            fetch_redirect_response=False,
        )

    def test_post_new_schedule_rejects_offsite_next(self):
        """Malicious ``next`` falls back to schedule deep link with new row."""
        response = self.client.post(
            reverse("new_schedule"),
            {
                "name": "Safe fallback plan",
                "semester": str(self.semester.pk),
                "next": "https://evil.example/",
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Schedule.objects.get(name="Safe fallback plan", user=self.user1)
        self.assertIn(reverse("schedule"), response.url)
        self.assertIn(str(created.pk), response.url)

    def test_post_new_schedule_invalid_form_still_redirects(self):
        """Invalid data surfaces an error message and redirects away."""
        long_name = "x" * 150
        response = self.client.post(
            reverse("new_schedule"),
            {
                "name": long_name,
                "semester": str(self.semester.pk),
            },
        )
        self.assertEqual(response.status_code, 302)
        msgs = [m.message for m in get_messages(response.wsgi_request)]
        self.assertTrue(
            msgs
            and any("Invalid" in str(m) or "at most" in str(m).lower() for m in msgs),
            msgs,
        )

    def test_delete_schedule_get_redirects_using_next(self):
        """DELETE flow uses POST body; bare GET still ends in redirect."""
        sched = Schedule.objects.create(
            name="To delete",
            user=self.user1,
            semester=self.semester,
        )
        response = self.client.get(
            reverse("delete_schedule"),
            {"next": reverse("browse")},
        )
        self.assertRedirects(
            response,
            reverse("browse"),
            fetch_redirect_response=False,
        )
        self.assertTrue(Schedule.objects.filter(pk=sched.pk).exists())

    def test_duplicate_schedule_redirects_to_new_copy(self):
        """Duplicate always redirects to the newly created copy, ignoring ``next``."""
        sched = Schedule.objects.create(
            name="Original",
            user=self.user1,
            semester=self.semester,
        )
        response = self.client.get(
            reverse("duplicate_schedule", args=[sched.pk]),
            {"next": reverse("browse")},  # should be ignored
        )
        self.assertEqual(response.status_code, 302)
        copy = Schedule.objects.get(user=self.user1, name__startswith="Copy of")
        self.assertIn(str(copy.pk), response.url)

    def test_edit_schedule_non_post_redirects_to_schedule(self):
        """GET edit_schedule is rejected and bounced to the builder."""
        response = self.client.get(reverse("edit_schedule"))
        self.assertRedirects(
            response,
            reverse("schedule"),
            fetch_redirect_response=False,
        )

    def test_remove_scheduled_course_get_ignores_next(self):
        """GET remove does not use ``safe_next_url`` (always plain schedule)."""
        schedule = Schedule.objects.create(
            name="S",
            user=self.user1,
            semester=self.semester,
        )
        sc = ScheduledCourse.objects.create(
            schedule=schedule,
            section=self.section_course,
            instructor=self.instructor,
            enrolled_units=3,
            time="TBA",
        )
        response = self.client.get(
            reverse("remove_scheduled_course", args=[sc.pk]),
            {"next": reverse("browse")},
        )
        self.assertRedirects(
            response,
            reverse("schedule"),
            fetch_redirect_response=False,
        )
        self.assertTrue(ScheduledCourse.objects.filter(pk=sc.pk).exists())

    def test_remove_scheduled_course_post_uses_safe_next(self):
        """POST remove honors safe ``next``."""
        schedule = Schedule.objects.create(
            name="S2",
            user=self.user1,
            semester=self.semester,
        )
        sc = ScheduledCourse.objects.create(
            schedule=schedule,
            section=self.section_course,
            instructor=self.instructor,
            enrolled_units=3,
            time="TBA",
        )
        response = self.client.post(
            reverse("remove_scheduled_course", args=[sc.pk]),
            {"next": reverse("browse")},
        )
        self.assertRedirects(
            response,
            reverse("browse"),
            fetch_redirect_response=False,
        )
        self.assertFalse(ScheduledCourse.objects.filter(pk=sc.pk).exists())


# ---------------------------------------------------------------------------
# Reviews: delete success URL, invalid AJAX fallbacks
# ---------------------------------------------------------------------------


class ReviewRedirectTestCase(TCFDataTestCase):
    """DeleteReview ``next`` and check_* invalid-form redirects."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_delete_review_post_next_overrides_default(self):
        """``next`` on delete POST wins over the default reviews list."""
        target = reverse("browse")
        response = self.client.post(
            reverse("delete_review", args=[self.review1.pk]),
            {"next": target},
        )
        self.assertRedirects(response, target, fetch_redirect_response=False)

    def test_check_duplicate_invalid_form_redirects_to_new_review(self):
        """Invalid POST to duplicate check falls back to the review form."""
        response = self.client.post(reverse("check_review_duplicate"), {})
        self.assertRedirects(
            response,
            reverse("new_review"),
            fetch_redirect_response=False,
        )

    def test_check_zero_hours_invalid_form_redirects_to_new_review(self):
        """Invalid zero-hours check POST redirects like duplicate check."""
        response = self.client.post(reverse("check_zero_hours_per_week"), {})
        self.assertRedirects(
            response,
            reverse("new_review"),
            fetch_redirect_response=False,
        )


# ---------------------------------------------------------------------------
# New review GET: club mode without club -> club search (like courses)
# ---------------------------------------------------------------------------


class NewReviewClubSearchTestCase(TCFDataTestCase):
    """Club review entry without ``club`` shows searchable picker."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_club_review_get_without_club_renders_review_page(self):
        """Club mode without ``club`` id shows unified review page with club picker."""
        response = self.client.get(
            reverse("new_review"),
            {"mode": "clubs"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "site/review/review.html")
        self.assertContains(response, "Search for a club by name")


# ---------------------------------------------------------------------------
# Profile POST hard-redirect (documents current behavior)
# ---------------------------------------------------------------------------


class ProfilePostRedirectTestCase(TCFDataTestCase):
    """Profile save always redirects to ``/profile`` (not ``reverse``)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_profile_post_redirects_to_slash_profile(self):
        """Successful save uses a hard-coded path (not ``safe_next_url``)."""
        response = self.client.post(
            reverse("profile"),
            {
                "first_name": "Pat",
                "last_name": "Lee",
                "graduation_year": 2027,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profile")


class DeleteProfileRedirectTestCase(TCFDataTestCase):
    """Account deletion success URL honors ``safe_next_url``."""

    def test_delete_profile_post_accepts_safe_next(self):
        """``next`` can send the user somewhere on-site after account deletion."""
        user = self.user4
        self.client.force_login(user)
        target = reverse("index")
        response = self.client.post(
            reverse("delete_profile", args=[user.pk]),
            {"next": target},
        )
        self.assertRedirects(response, target, fetch_redirect_response=False)
        self.assertFalse(User.objects.filter(pk=user.pk).exists())


class CognitoCallbackFailureRedirectTestCase(TCFDataTestCase):
    """Token exchange and auth failures land on the home page."""

    @patch("tcf_website.views.auth.requests.post")
    def test_cognito_callback_token_error_redirects_index(self, mock_post):
        """Non-200 from Cognito token endpoint shows an error and redirects."""
        mock_post.return_value = MagicMock(status_code=400)
        mock_post.return_value.text = "invalid_grant"

        response = self.client.get(
            reverse("cognito_callback"),
            {"code": "bad-code"},
        )
        self.assertRedirects(
            response,
            reverse("index"),
            fetch_redirect_response=False,
        )

    @patch("tcf_website.views.auth.authenticate")
    @patch("tcf_website.views.auth.requests.post")
    def test_cognito_callback_authenticate_none_redirects_index(
        self, mock_post, mock_authenticate
    ):
        """Valid tokens but unknown user still fail closed to index."""
        mock_post.return_value = MagicMock(status_code=200)
        mock_post.return_value.json.return_value = {"id_token": "x"}
        mock_authenticate.return_value = None

        response = self.client.get(
            reverse("cognito_callback"),
            {"code": "auth-code"},
        )
        self.assertRedirects(
            response,
            reverse("index"),
            fetch_redirect_response=False,
        )


class ScheduleAddCourseRedirectTestCase(TCFDataTestCase):
    """Add-to-schedule POST success respects ``next`` like other schedule actions."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.user1)

    def test_add_course_success_honors_safe_next(self):
        """After adding a section, ``next`` can return to browse."""
        schedule = Schedule.objects.create(
            name="Add flow",
            user=self.user1,
            semester=self.semester,
        )
        target = reverse("browse")
        post_url = reverse("schedule_add_course", args=[self.course.pk])
        response = self.client.post(
            post_url,
            {
                "schedule_id": str(schedule.pk),
                "selection": f"{self.section_course.pk}:{self.instructor.pk}",
                "semester": str(self.semester.pk),
                "next": target,
            },
        )
        self.assertRedirects(response, target, fetch_redirect_response=False)

    def test_add_course_success_rejects_malicious_next(self):
        """Off-site ``next`` is dropped; redirect stays on schedule builder."""
        schedule = Schedule.objects.create(
            name="Add flow 2",
            user=self.user1,
            semester=self.semester,
        )
        post_url = reverse("schedule_add_course", args=[self.course.pk])
        response = self.client.post(
            post_url,
            {
                "schedule_id": str(schedule.pk),
                "selection": f"{self.section_course.pk}:{self.instructor.pk}",
                "semester": str(self.semester.pk),
                "next": "https://evil.example/",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("schedule"), response.url)
        self.assertIn(str(schedule.pk), response.url)
