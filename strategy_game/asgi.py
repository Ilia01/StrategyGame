"""
ASGI config for strategy_game project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "strategy_game.settings")

# Initialize Django
django.setup()

# Import these after Django is set up

# Define a function to get the application


def get_application():
    # Import routing here after Django is fully set up
    import game.routing

    return ProtocolTypeRouter(
        {
            "http": get_asgi_application(),
            "websocket": AuthMiddlewareStack(
                URLRouter(game.routing.websocket_urlpatterns)
            ),
        }
    )


# Get the application
application = get_application()
