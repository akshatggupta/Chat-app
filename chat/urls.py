from django.urls import path
from . import views

urlpatterns = [
    path("", views.anonymous_chat, name="anonymous_chat"),     # Anonymous chat at /
    path("rooms/", views.index, name="index"),                # Room selection at /rooms/
    path("login/", views.login_view, name='login'),           # /login/
    path("chat/<str:room_name>/", views.room, name="room"),   # /chat/roomname/
]