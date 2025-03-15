from django.urls import path
from .views import (
    api_views,
    web_views
)

urlpatterns = [
    path("", web_views.home, name="home"),
    path("game/<int:game_id>/", api_views.game_state, name="game_detail"),
    # API endpoints
    path("api/create_game/", api_views.create_game, name="create_game"),
    path("api/join_game/<int:game_id>/", api_views.join_game, name="join_game"),
    path("api/take_turn/<int:game_id>/", api_views.take_turn, name="take_turn"),
    path("api/game_state/<int:game_id>/", api_views.game_state, name="game_state"),
]
