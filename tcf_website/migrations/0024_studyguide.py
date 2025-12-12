from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0023_remove_sectionenrollment_section_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudyGuide",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("google_doc_id", models.CharField(max_length=128, blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "course",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, to="tcf_website.course"
                    ),
                ),
            ],
        ),
    ]