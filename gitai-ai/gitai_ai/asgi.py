import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import top.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gitai_ai.settings')

application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            top.routing.websocket_urlpatterns
        )
    ),
})