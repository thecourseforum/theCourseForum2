"""Bedrock request contract, summary persistence, and offline command behavior."""

from io import StringIO
from unittest.mock import Mock, patch

import boto3
from botocore.exceptions import NoCredentialsError
from botocore.stub import Stubber
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase, override_settings

from tcf_website.management.commands import generate_ai_summaries as summaries
from tcf_website.models import ReviewLLMSummary

from .test_utils import setup

MODEL_ID = "us.amazon.nova-lite-v1:0"
COMMAND_MODULE = "tcf_website.management.commands.generate_ai_summaries"


def bedrock_response(text=" Clear lectures and challenging assignments. ", **kwargs):
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": text}]}},
        "stopReason": "end_turn",
        "usage": {"inputTokens": 100, "outputTokens": 10, "totalTokens": 110},
        "metrics": {"latencyMs": 100},
        **kwargs,
    }


@override_settings(CACHALOT_ENABLED=False)
class BedrockSummaryTests(TestCase):
    def setUp(self):
        setup(self)
        self.row = {
            "course_id": self.course.id,
            "instructor_id": self.instructor.id,
            "review_count": 2,
        }
        # Explicit dummy credentials prevent credential discovery or network access.
        self.bedrock = boto3.client(
            "bedrock-runtime",
            region_name="us-east-1",
            aws_access_key_id="testing",
            aws_secret_access_key="testing",
        )
        self.addCleanup(self.bedrock.close)

    def test_converse_request_and_saved_summary(self):
        with Stubber(self.bedrock) as stubber:
            stubber.add_response("converse", bedrock_response())
            result = summaries.summarize_one(self.bedrock, self.row, MODEL_ID, False)
            stubber.assert_no_pending_responses()

        self.assertEqual(result[0], "saved")
        saved = ReviewLLMSummary.objects.get(
            course=self.course, instructor=self.instructor
        )
        self.assertEqual(
            saved.summary_text, "Clear lectures and challenging assignments."
        )
        self.assertEqual(saved.model_id, MODEL_ID)
        self.assertEqual(saved.source_review_count, 2)

    def test_prompt_excludes_hidden_and_toxic_reviews(self):
        self.review1.hidden = True
        self.review1.save()
        self.review2.toxicity_rating = settings.TOXICITY_THRESHOLD
        self.review2.save()
        client = Mock()
        client.converse.return_value = bedrock_response()

        summaries.summarize_one(client, self.row, MODEL_ID, False)

        request = client.converse.call_args.kwargs
        self.assertEqual(request["modelId"], MODEL_ID)
        self.assertIn("Write 3-5 sentences", request["system"][0]["text"])
        self.assertEqual(request["messages"][0]["role"], "user")
        prompt = request["messages"][0]["content"][0]["text"]
        self.assertNotIn(self.review1.text, prompt)
        self.assertNotIn(self.review2.text, prompt)

    def test_failed_responses_preserve_existing_summary(self):
        saved = ReviewLLMSummary.objects.create(
            course=self.course,
            instructor=self.instructor,
            summary_text="Existing summary",
            model_id="previous-model",
            source_review_count=10,
        )
        for response in (
            bedrock_response(" "),
            bedrock_response(stopReason="max_tokens"),
            bedrock_response(stopReason="content_filtered"),
            {"stopReason": "end_turn", "output": {}},
        ):
            with self.subTest(response=response):
                client = Mock()
                client.converse.return_value = response
                self.assertIsNone(
                    summaries.summarize_one(client, self.row, MODEL_ID, False)
                )
                saved.refresh_from_db()
                self.assertEqual(saved.summary_text, "Existing summary")
                self.assertEqual(saved.model_id, "previous-model")
                self.assertEqual(saved.source_review_count, 10)

    def test_aws_service_errors_fail_pair_without_saving(self):
        for code in (
            "ThrottlingException",
            "AccessDeniedException",
            "ValidationException",
        ):
            with self.subTest(code=code), Stubber(self.bedrock) as stubber:
                stubber.add_client_error("converse", service_error_code=code)
                self.assertIsNone(
                    summaries.summarize_one(self.bedrock, self.row, MODEL_ID, False)
                )
        self.assertFalse(ReviewLLMSummary.objects.exists())

    def test_dry_run_never_invokes_bedrock_or_saves(self):
        client = Mock()
        result = summaries.summarize_one(client, self.row, MODEL_ID, True)
        self.assertEqual(result[0], "dry_run")
        client.converse.assert_not_called()
        self.assertFalse(ReviewLLMSummary.objects.exists())


class BedrockCommandTests(SimpleTestCase):
    def setUp(self):
        self.pairs = [{"course_id": 1, "instructor_id": 2, "review_count": 5}]
        pairs_patch = patch.object(
            summaries.Command, "_get_pairs", return_value=self.pairs
        )
        pairs_patch.start()
        self.addCleanup(pairs_patch.stop)

    @override_settings(BEDROCK_MODEL_ID=MODEL_ID)
    def test_default_model_and_cli_override(self):
        for model in (None, "us.amazon.nova-pro-v1:0"):
            with (
                self.subTest(model=model),
                patch(f"{COMMAND_MODULE}.create_client") as create_client,
                patch(
                    f"{COMMAND_MODULE}.summarize_one", return_value=("saved", "ok")
                ) as summarize,
            ):
                options = {} if model is None else {"model": model}
                call_command("generate_ai_summaries", stdout=StringIO(), **options)
                self.assertEqual(summarize.call_args.args[2], model or MODEL_ID)
                create_client.return_value.close.assert_called_once()

    def test_dry_run_does_not_discover_aws_credentials(self):
        with (
            patch(f"{COMMAND_MODULE}.create_client") as create_client,
            patch(
                f"{COMMAND_MODULE}.summarize_one", return_value=("dry_run", "preview")
            ),
        ):
            call_command("generate_ai_summaries", dry_run=True, stdout=StringIO())
            create_client.assert_not_called()

    def test_missing_credentials_become_command_error(self):
        with (
            patch(f"{COMMAND_MODULE}.create_client", side_effect=NoCredentialsError()),
            self.assertRaisesMessage(
                CommandError, "Could not initialize Amazon Bedrock"
            ),
        ):
            call_command("generate_ai_summaries", stdout=StringIO())

    def test_pair_failure_is_reported_and_client_closed(self):
        with (
            patch(f"{COMMAND_MODULE}.create_client") as create_client,
            patch(f"{COMMAND_MODULE}.summarize_one", return_value=None),
            self.assertRaisesMessage(CommandError, "1 pair(s) failed."),
        ):
            call_command("generate_ai_summaries", stdout=StringIO())
        create_client.return_value.close.assert_called_once()
