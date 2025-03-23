from django.apps import AppConfig

class GameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "game"

    def ready(self):
        try:
            import game.signals  # Import signals directly from game app
        except ImportError:
            pass
