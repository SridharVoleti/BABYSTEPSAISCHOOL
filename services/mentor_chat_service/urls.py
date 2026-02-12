# 2025-11-14: Mentor Chat Service - URL routing
from django.urls import path
from . import views

app_name = "mentor_chat"

urlpatterns = [
    path('chat/', views.chat, name='chat'),
    path('health/', views.health_check, name='health'),
]