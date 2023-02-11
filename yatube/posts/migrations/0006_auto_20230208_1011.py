# Generated by Django 2.2.16 on 2023-02-08 06:11

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0005_auto_20230207_2339'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='author',
            field=models.ForeignKey(help_text='Добавьте комментарий', on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL),
        ),
    ]