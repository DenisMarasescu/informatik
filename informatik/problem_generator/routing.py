# problem_generator/routing.py
from django.urls import path
from . import consumers
from .notification_consumers import NotificationConsumer

websocket_urlpatterns = [
    path('ws/chat/<str:username>/', consumers.ChatConsumer.as_asgi()),
    path('ws/notifications/', NotificationConsumer.as_asgi()),
]