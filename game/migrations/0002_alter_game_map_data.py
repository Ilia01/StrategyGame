# Generated by Django 5.0.2 on 2025-04-06 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="map_data",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
