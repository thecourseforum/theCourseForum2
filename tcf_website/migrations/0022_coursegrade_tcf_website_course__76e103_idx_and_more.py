# Generated by Django 4.2.20 on 2025-05-04 01:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0021_clubcategory_alter_review_course_and_more"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="coursegrade",
            index=models.Index(
                fields=["course"], name="tcf_website_course__76e103_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="courseinstructorgrade",
            index=models.Index(
                fields=["course", "instructor"], name="tcf_website_course__4f81de_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="courseinstructorgrade",
            index=models.Index(
                fields=["instructor", "course"], name="tcf_website_instruc_e12a74_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="courseinstructorgrade",
            index=models.Index(
                fields=["course"], name="tcf_website_course__192290_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="courseinstructorgrade",
            index=models.Index(
                fields=["instructor"], name="tcf_website_instruc_4bb151_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(
                fields=["instructor", "course"], name="tcf_website_instruc_bbc502_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="review",
            index=models.Index(
                fields=["instructor"], name="tcf_website_instruc_dd1304_idx"
            ),
        ),
    ]
