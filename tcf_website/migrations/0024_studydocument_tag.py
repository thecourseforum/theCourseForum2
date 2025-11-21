from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0023_remove_sectionenrollment_section_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=64, unique=True)),
                ("slug", models.SlugField(blank=True, max_length=64, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name="StudyDocument",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("file", models.FileField(upload_to="study_docs/%Y/%m/%d")),
                ("mime_type", models.CharField(blank=True, max_length=128)),
                ("size", models.PositiveIntegerField(default=0)),
                ("is_public", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "course",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="study_documents", to="tcf_website.Course"),
                ),
                (
                    "uploader",
                    models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="uploaded_documents", to=settings.AUTH_USER_MODEL),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="studydocument",
            index=models.Index(fields=["course", "created_at"], name="tcf_website_studydocument_course_created_at_idx"),
        ),
        migrations.AddField(
            model_name="studydocument",
            name="tags",
            field=models.ManyToManyField(blank=True, related_name="documents", to="tcf_website.Tag"),
        ),
    ]