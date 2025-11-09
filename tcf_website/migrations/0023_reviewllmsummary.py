from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Create ReviewLLMSummary model for cached LLM summaries."""

    dependencies = [
        ("tcf_website", "0022_coursegrade_tcf_website_course__76e103_idx_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReviewLLMSummary",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("summary_text", models.TextField(blank=True)),
                ("model_id", models.CharField(blank=True, max_length=255)),
                ("source_review_count", models.PositiveIntegerField(default=0)),
                ("last_review_id", models.PositiveIntegerField(default=0)),
                ("source_metadata", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "club",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="tcf_website.club",
                    ),
                ),
                (
                    "course",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="tcf_website.course",
                    ),
                ),
                (
                    "instructor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="tcf_website.instructor",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["course", "instructor"],
                        name="tcf_website_reviewllmsum_course_instr_idx",
                    ),
                    models.Index(
                        fields=["club"], name="tcf_website_reviewllmsum_club_idx"
                    ),
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="reviewllmsummary",
            constraint=models.UniqueConstraint(
                condition=models.Q(club__isnull=True),
                fields=("course", "instructor"),
                name="unique_review_llm_summary_course_instructor",
            ),
        ),
        migrations.AddConstraint(
            model_name="reviewllmsummary",
            constraint=models.UniqueConstraint(
                condition=models.Q(club__isnull=False),
                fields=("club",),
                name="unique_review_llm_summary_club",
            ),
        ),
    ]
