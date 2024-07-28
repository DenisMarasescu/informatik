# Generated by Django 5.0.2 on 2024-07-27 17:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_user_bio_user_profile_picture_user_social_links'),
    ]

    operations = [
        migrations.CreateModel(
            name='Badge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('image', models.ImageField(blank=True, upload_to='badge_images/')),
            ],
        ),
        migrations.AddField(
            model_name='user',
            name='badges',
            field=models.ManyToManyField(blank=True, related_name='users', to='accounts.badge'),
        ),
    ]
