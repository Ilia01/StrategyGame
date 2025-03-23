from django.urls import path
from .views import HomeView, GameDetailView, LeaveGameView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('game/<int:game_id>/', GameDetailView.as_view(), name='game_detail'),
    path('game/<int:game_id>/leave/', LeaveGameView.as_view(), name='leave_game'),
]