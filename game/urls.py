from django.urls import path
from .views import (
    home,
    game_detail,
    create_game,
    join_game,
    take_turn,
    game_state,
)

urlpatterns = [
    path("", home, name="home"),
    path("game/<int:game_id>/", game_detail, name="game_detail"),
    # API endpoints
    path("api/create_game/", create_game, name="create_game"),
    path("api/join_game/<int:game_id>/", join_game, name="join_game"),
    path("api/take_turn/<int:game_id>/", take_turn, name="take_turn"),
    path("api/game_state/<int:game_id>/", game_state, name="game_state"),
]
