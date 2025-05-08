from django.urls import path
from .views import fetch_agents, fetch_teams

urlpatterns = [
    path('agents/', fetch_agents, name='fetch_agents'),
    path('teams/', fetch_teams, name='fetch_teams'),
]
