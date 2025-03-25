from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('game/<int:game_id>/', views.GameDetailView.as_view(), name='game_detail'),
    path('game/<int:game_id>/join/', views.JoinGameView.as_view(), name='join_game'),
    path('game/<int:game_id>/leave/', views.LeaveGameView.as_view(), name='leave_game'),
]