# Generated by Django 5.0.2 on 2025-04-06 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("game", "0004_alter_game_map_data"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="game",
            name="map_size",
        ),
        migrations.AlterField(
            model_name="game",
            name="map_data",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
