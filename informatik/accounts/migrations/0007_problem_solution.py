# Generated by Django 4.2.3 on 2024-02-27 09:59

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0006_homework_grading_criteria_homework_problems"),
    ]

    operations = [
        migrations.CreateModel(
            name="Problem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
                ("index", models.IntegerField(blank=True, null=True)),
                (
                    "homework",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="probleme",
                        to="accounts.homework",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Solution",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("text", models.TextField()),
                ("grade", models.IntegerField(blank=True, null=True)),
                ("feedback", models.TextField(blank=True, null=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                (
                    "problem",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solutions",
                        to="accounts.problem",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="solutions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
