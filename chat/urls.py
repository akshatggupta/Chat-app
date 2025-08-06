from django.urls import path

from . import views


urlpatterns = [
    path("", views.index, name="index"),
    path('/chat/login/', views.login_view, name='login'),
    path("<str:room_name>/", views.room, name="room"),
    
]