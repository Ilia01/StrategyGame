import json
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from game.models import Game, Player, Unit, Building #Turn
from game.utils.game_helpers import (
    generate_map,
    get_starting_position,
    # is_player_turn,
    # is_valid_move,
    # is_valid_attack,
    # calculate_damage,
    # is_valid_build_position,
    # advance_game_if_all_turns_complete,
    # calculate_visibility_map,
)
from game.utils.resource_helpers import get_building_cost

@api_view(["POST"])
@login_required
def create_game(request):
    """API endpoint to create a new game."""
    name = request.data.get("name", f"{request.user.username}'s Game")
    map_size = int(request.data.get("map_size", 10))
    max_players = int(request.data.get("max_players", 2))
    
    game = Game.objects.create(name=name, map_size=map_size, max_players=max_players)
    map_data = generate_map(map_size)
    game.set_map(map_data)
    game.save()

    player = Player.objects.create(user=request.user, game=game, player_number=1)
    starting_position = get_starting_position(map_data, 1, map_size)
    
    Building.objects.create(
        player=player,
        building_type="base",
        x_position=starting_position["x"],
        y_position=starting_position["y"],
    )
    Unit.objects.create(
        player=player,
        unit_type="infantry",
        x_position=starting_position["x"] + 1,
        y_position=starting_position["y"],
    )

    return Response({"game_id": game.id}, status=status.HTTP_201_CREATED)

@api_view(["POST"])
@login_required
def join_game(request, game_id):
    """API endpoint to join an existing game."""
    game = get_object_or_404(Game, pk=game_id)
    player_count = Player.objects.filter(game=game).count()

    if player_count >= game.max_players:
        return Response({"error": "Game is full"}, status=status.HTTP_400_BAD_REQUEST)
    if Player.objects.filter(user=request.user, game=game).exists():
        return Response({"error": "Already in game"}, status=status.HTTP_400_BAD_REQUEST)

    player_number = player_count + 1
    player = Player.objects.create(user=request.user, game=game, player_number=player_number)
    map_data = game.get_map()
    starting_position = get_starting_position(map_data, player_number, game.map_size)
    
    Building.objects.create(
        player=player,
        building_type="base",
        x_position=starting_position["x"],
        y_position=starting_position["y"],
    )
    Unit.objects.create(
        player=player,
        unit_type="infantry",
        x_position=starting_position["x"] + 1,
        y_position=starting_position["y"],
    )
    return Response({"success": True}, status=status.HTTP_200_OK)

# Similarly, you would place take_turn and game_state here.
