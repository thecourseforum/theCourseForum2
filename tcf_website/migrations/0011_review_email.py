# Generated by Django 4.2.8 on 2024-03-11 15:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tcf_website", "0010_trigram_extension"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="email",
            field=models.CharField(default=""),
        ),
    ]
