# Generated by Django 4.2.3 on 2024-02-27 08:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_remove_course_teacher_course_teachers"),
    ]

    operations = [
        migrations.AlterField(
            model_name="course",
            name="entrance_code",
            field=models.CharField(blank=True, max_length=50, unique=True),
        ),
        migrations.CreateModel(
            name="Homework",
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
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("deadline", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="homeworks",
                        to="accounts.course",
                    ),
                ),
            ],
        ),
    ]
