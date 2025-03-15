from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import json

from game.models import Game, Player, Unit, Building, Turn
from game.utils.game_helpers import (
    generate_map,
    get_starting_position,
    is_player_turn,
    is_valid_move,
    is_valid_attack,
    calculate_damage,
    is_valid_build_position,
    advance_game_if_all_turns_complete,
    calculate_visibility_map,
)
from game.utils.resource_helpers import get_building_cost

@api_view(["POST"])
@login_required
def create_game(request):
    """API endpoint to create a new game."""
    if request.method == "POST":
        name = request.data.get("name", f"{request.user.username}'s Game")
        map_size = int(request.data.get("map_size", 10))
        max_players = int(request.data.get("max_players", 2))

        game = Game.objects.create(
            name=name, map_size=map_size, max_players=max_players
        )

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

    return Response(status=status.HTTP_400_BAD_REQUEST)

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

@api_view(["POST"])
@login_required
def take_turn(request, game_id):
    """API endpoint to submit a turn."""
    game = get_object_or_404(Game, pk=game_id)
    player = get_object_or_404(Player, user=request.user, game=game)

    if not is_player_turn(game, player):
        return Response({"error": "Not your turn"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        actions = request.data.get("actions", [])

        for action in actions:
            action_type = action.get("type")

            if action_type == "build":
                building_type = action.get("building_type")
                x = action.get("x")
                y = action.get("y")
                cost = get_building_cost(building_type)

                if not is_valid_build_position(x, y, game):
                    raise ValueError(f"Invalid build position: {x}, {y}")

                if player.resources < cost:
                    raise ValueError(f"Insufficient resources for {building_type}")

                Building.objects.create(
                    player=player,
                    building_type=building_type,
                    x_position=x,
                    y_position=y,
                )
                player.resources -= cost
                player.save()

            elif action_type == "move_unit":
                unit_id = action.get("unit_id")
                x = action.get("x")
                y = action.get("y")

                unit = get_object_or_404(Unit, id=unit_id, player=player)
                if not is_valid_move(unit, x, y, game):
                    raise ValueError(f"Invalid move for unit {unit_id}")

                unit.x_position = x
                unit.y_position = y
                unit.has_moved = True
                unit.save()

            elif action_type == "attack":
                unit_id = action.get("unit_id")
                target_x = action.get("target_x")
                target_y = action.get("target_y")

                unit = get_object_or_404(Unit, id=unit_id, player=player)
                target = (
                    Unit.objects.filter(game=game, x_position=target_x, y_position=target_y)
                    .exclude(player=player)
                    .first()
                )
                if not target:
                    target = (
                        Building.objects.filter(game=game, x_position=target_x, y_position=target_y)
                        .exclude(player=player)
                        .first()
                    )
                if not target:
                    raise ValueError("No valid target found")
                if not is_valid_attack(unit, target):
                    raise ValueError("Invalid attack")
                damage = calculate_damage(unit, target)
                target.health -= damage
                if target.health <= 0:
                    target.delete()
                else:
                    target.save()
                unit.has_attacked = True
                unit.save()

        Turn.objects.create(
            game=game,
            player=player,
            turn_number=game.current_turn,
            actions=json.dumps(actions),
            completed=True,
            completed_at=timezone.now(),
        )

        advance_game_if_all_turns_complete(game)
        return Response({"success": True}, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({"error": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(["GET"])
@login_required
def game_state(request, game_id):
    """API endpoint to get current game state."""
    game = get_object_or_404(Game, pk=game_id)
    try:
        player = Player.objects.get(user=request.user, game=game)
    except Player.DoesNotExist:
        player = None

    game_data = {
        "id": game.id,
        "name": game.name,
        "current_turn": game.current_turn,
        "map_size": game.map_size,
        "map_data": game.get_map(),
        "current_player_id": None,
        "players": [],
        "units": [],
        "buildings": [],
    }

    for p in Player.objects.filter(game=game):
        if p.player_number == (game.current_turn - 1) % game.max_players + 1:
            game_data["current_player_id"] = p.id
        game_data["players"].append({
            "id": p.id,
            "username": p.user.username,
            "player_number": p.player_number,
            "resources": p.resources,
        })

    if player:
        for unit in Unit.objects.filter(game=game):
            game_data["units"].append({
                "id": unit.id,
                "type": unit.unit_type,
                "x": unit.x_position,
                "y": unit.y_position,
                "player_id": unit.player_id,
                "health": unit.health,
                "has_moved": unit.has_moved,
                "has_attacked": unit.has_attacked,
            })
        for building in Building.objects.filter(game=game):
            game_data["buildings"].append({
                "id": building.id,
                "type": building.building_type,
                "x": building.x_position,
                "y": building.y_position,
                "player_id": building.player_id,
                "health": building.health,
            })
        visibility_map = calculate_visibility_map(game, player)
        game_data["visibility_map"] = visibility_map

    return Response(game_data, status=status.HTTP_200_OK)
