# Generated by Django 4.2.20 on 2025-05-14 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conversation",
            name="is_cto_chat",
            field=models.BooleanField(default=False),
        ),
    ]
