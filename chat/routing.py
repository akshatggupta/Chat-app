# chat/routing.py
from django.urls import re_path

from . import consumers

# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/$', consumers.ChatConsumer.as_asgi()),  # Changed from AnonymousChatConsumer to ChatConsumer
    re_path(r'ws/$',consumers.ChatConsumer.as_asgi()),
]
