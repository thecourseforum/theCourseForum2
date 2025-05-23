# Generated by Django 4.2.20 on 2025-05-02 20:34

import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0020_review_toxicity_category_review_toxicity_rating"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClubCategory",
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
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("slug", models.SlugField(max_length=255, unique=True)),
            ],
        ),
        migrations.AlterField(
            model_name="review",
            name="course",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.course",
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="instructor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.instructor",
            ),
        ),
        migrations.CreateModel(
            name="Club",
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
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "combined_name",
                    models.CharField(blank=True, editable=False, max_length=255),
                ),
                ("application_required", models.BooleanField(default=False)),
                ("photo_url", models.CharField(blank=True, max_length=255)),
                ("meeting_time", models.CharField(blank=True, max_length=255)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="tcf_website.clubcategory",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="review",
            name="club",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="tcf_website.club",
            ),
        ),
        migrations.AddIndex(
            model_name="club",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["combined_name"],
                name="club_combined_name",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]
