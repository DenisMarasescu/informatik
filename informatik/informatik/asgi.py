import os
import django
django.setup()
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path
from starlette.staticfiles import StaticFiles
from pathlib import Path
from django.conf import settings
# settings.configure()
from problem_generator import consumers
from problem_generator.routing import websocket_urlpatterns
from channels.auth import AuthMiddlewareStack

# Define BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'informatik.settings')


# Get Django ASGI application
django_asgi_app = get_asgi_application()

# Define a custom ASGI application that serves static files
class CustomStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http' and scope['path'].startswith(settings.STATIC_URL):
            adjusted_path = scope['path'][len(settings.STATIC_URL):]
            print(f"Serving static file: {adjusted_path}")
            scope['path'] = adjusted_path
            await super().__call__(scope, receive, send)
        else:
            await django_asgi_app(scope, receive, send)

# ASGI application
application = ProtocolTypeRouter({
    "http": CustomStaticFiles(directory=settings.STATIC_ROOT),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
