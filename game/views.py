from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib import messages
import json
from .models import Game, Player, Unit, Building, Turn
from .utils.game_helpers import (
    generate_map,
    get_starting_position,
    is_player_turn,
    is_valid_move,
    is_valid_attack,
    calculate_damage,
    is_valid_build_position,
)
from .utils.resource_helpers import get_building_cost
from random import random


def home(request):
    """Main page view showing active games"""
    active_games = Game.objects.filter(is_active=True)
    context = {"active_games": active_games}
    return render(request, "home.html", context)


@login_required
def game_detail(request, game_id):
    """View for a specific game"""
    game = get_object_or_404(Game, pk=game_id)
    try:
        player = Player.objects.get(user=request.user, game=game)
        is_player = True
    except Player.DoesNotExist:
        player = None
        is_player = False

    context = {
        "game": game,
        "player": player,
        "is_player": is_player,
        "game_id": game_id,
    }
    return render(request, "game_detail.html", context)


@api_view(["POST"])
@login_required
def create_game(request):
    """API endpoint to create a new game"""
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
    """API endpoint to join an existing game"""
    game = get_object_or_404(Game, pk=game_id)

    # Check if game is full
    player_count = Player.objects.filter(game=game).count()
    if player_count >= game.max_players:
        return Response({"error": "Game is full"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user is already in the game
    if Player.objects.filter(user=request.user, game=game).exists():
        return Response(
            {"error": "Already in game"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Create player
    player_number = player_count + 1
    player = Player.objects.create(
        user=request.user, game=game, player_number=player_number
    )

    # Create starting base
    map_data = game.get_map()
    starting_position = get_starting_position(map_data, player_number, game.map_size)
    Building.objects.create(
        player=player,
        building_type="base",
        x_position=starting_position["x"],
        y_position=starting_position["y"],
    )

    # Create starting units
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
    """API endpoint to submit a turn"""
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
                    game=game,
                    building_type=building_type,
                    x_position=x,
                    y_position=y,
                )
                player.resources -= cost
                player.save()

            elif action_type == "move_unit":
                # Handle unit movement
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
                # Handle attack action
                unit_id = action.get("unit_id")
                target_x = action.get("target_x")
                target_y = action.get("target_y")

                unit = get_object_or_404(Unit, id=unit_id, player=player)

                # Find target
                target = (
                    Unit.objects.filter(
                        game=game, x_position=target_x, y_position=target_y
                    )
                    .exclude(player=player)
                    .first()
                )

                if not target:
                    target = (
                        Building.objects.filter(
                            game=game, x_position=target_x, y_position=target_y
                        )
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

        # Mark turn as complete
        Turn.objects.create(
            game=game,
            player=player,
            turn_number=game.current_turn,
            actions=json.dumps(actions),
            completed=True,
            completed_at=timezone.now(),
        )

        # Check if all players have completed their turns
        advance_game_if_all_turns_complete(game)

        return Response({"success": True}, status=status.HTTP_200_OK)

    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response(
            {"error": "Server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def advance_game_if_all_turns_complete(game):
    """Check if all players have completed their turns and advance the game"""
    player_count = Player.objects.filter(game=game).count()
    completed_turns = Turn.objects.filter(
        game=game, turn_number=game.current_turn, completed=True
    ).count()

    if completed_turns >= player_count:
        # Reset unit movement and attack flags
        Unit.objects.filter(game=game).update(has_moved=False, has_attacked=False)

        # Add resources from buildings
        for player in Player.objects.filter(game=game):
            base_income = 5
            farm_income = (
                Building.objects.filter(player=player, building_type="farm").count() * 3
            )
            mine_income = (
                Building.objects.filter(player=player, building_type="mine").count() * 5
            )

            player.resources += base_income + farm_income + mine_income
            player.save()

        # Advance to next turn
        game.current_turn += 1
        game.save()


# Helper functions


def generate_map(size):
    """Generate a random map"""
    terrain_types = ["plains", "forest", "mountain", "water"]
    map_data = {"size": size, "terrain": []}

    # Generate terrain
    for y in range(size):
        row = []
        for x in range(size):
            # More plains than other terrain types
            weights = [0.6, 0.2, 0.1, 0.1]
            terrain = random.choices(terrain_types, weights=weights)[0]
            row.append(terrain)
        map_data["terrain"].append(row)

    return map_data


def get_starting_position(map_data, player_number, map_size):
    """Determine starting position based on player number"""
    positions = [
        {"x": 1, "y": 1},  # Player 1: top-left
        {"x": map_size - 2, "y": map_size - 2},  # Player 2: bottom-right
        {"x": 1, "y": map_size - 2},  # Player 3: bottom-left
        {"x": map_size - 2, "y": 1},  # Player 4: top-right
    ]

    # Ensure valid player number
    idx = min(player_number - 1, len(positions) - 1)

    # Make sure the position is on plains
    position = positions[idx]
    map_data["terrain"][position["y"]][position["x"]] = "plains"

    return position


def is_player_turn(game, player):
    """Check if it's the player's turn"""
    # In a sequential turn system, check if this player is next
    current_player_number = (game.current_turn - 1) % game.max_players + 1
    return player.player_number == current_player_number


def is_valid_move(unit, x, y, game):
    """Check if a move is valid"""
    # Check if destination is within map bounds
    if x < 0 or y < 0 or x >= game.map_size or y >= game.map_size:
        return False

    # Check if destination is within movement range
    distance = abs(unit.x_position - x) + abs(unit.y_position - y)
    if distance > unit.movement_range:
        return False

    # Check if destination is occupied
    if Unit.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False

    if Building.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False

    # Check terrain (simplified)
    map_data = game.get_map()
    terrain = map_data["terrain"][y][x]
    if terrain == "water":
        return False

    return True


def is_valid_attack(unit, target):
    """Check if an attack is valid"""
    # Check if target is within attack range
    distance = abs(unit.x_position - target.x_position) + abs(
        unit.y_position - target.y_position
    )
    return distance <= unit.attack_range


def calculate_damage(attacker, defender):
    """Calculate damage for an attack"""
    if hasattr(defender, "defense"):
        base_damage = max(1, attacker.attack - defender.defense)
    else:
        base_damage = attacker.attack

    return base_damage + random.randint(0, 3)


def is_valid_build_position(x, y, game):
    """Check if a position is valid for building"""
    if x < 0 or y < 0 or x >= game.map_size or y >= game.map_size:
        return False

    if Unit.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False

    if Building.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False

    map_data = game.get_map()
    terrain = map_data["terrain"][y][x]
    if terrain in ["water", "mountain"]:
        return False

    return True


def get_building_cost(building_type):
    """Get the cost of a building"""
    costs = {"barracks": 50, "farm": 30, "mine": 40}
    return costs.get(building_type, 0)


def get_unit_cost(unit_type):
    """Get the cost of a unit"""
    costs = {"infantry": 20, "archer": 30, "cavalry": 40, "siege": 60}
    return costs.get(unit_type, 0)


@api_view(["GET"])
@login_required
def game_state(request, game_id):
    """API endpoint to get current game state"""
    game = get_object_or_404(Game, pk=game_id)
    try:
        player = Player.objects.get(user=request.user, game=game)
    except Player.DoesNotExist:
        player = None

    # Collect game state data
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

    # Add players data
    for p in Player.objects.filter(game=game):
        if p.player_number == (game.current_turn - 1) % game.max_players + 1:
            game_data["current_player_id"] = p.id

        game_data["players"].append(
            {
                "id": p.id,
                "username": p.user.username,
                "player_number": p.player_number,
                "resources": p.resources,
            }
        )

    # Add units and buildings if user is a player
    if player:
        for unit in Unit.objects.filter(game=game):
            game_data["units"].append(
                {
                    "id": unit.id,
                    "type": unit.unit_type,
                    "x": unit.x_position,
                    "y": unit.y_position,
                    "player_id": unit.player_id,
                    "health": unit.health,
                    "has_moved": unit.has_moved,
                    "has_attacked": unit.has_attacked,
                }
            )

        for building in Building.objects.filter(game=game):
            game_data["buildings"].append(
                {
                    "id": building.id,
                    "type": building.building_type,
                    "x": building.x_position,
                    "y": building.y_position,
                    "player_id": building.player_id,
                    "health": building.health,
                }
            )

        # Add visibility data for fog of war
        visibility_map = calculate_visibility_map(game, player)
        game_data["visibility_map"] = visibility_map

    return Response(game_data, status=status.HTTP_200_OK)


def calculate_visibility_map(game, player):
    """Calculate which cells are visible to the player"""
    visibility_range = 3
    visible_cells = set()

    entities = list(Unit.objects.filter(player=player))
    entities.extend(Building.objects.filter(player=player))

    for entity in entities:
        x, y = entity.x_position, entity.y_position
        for dx in range(-visibility_range, visibility_range + 1):
            for dy in range(-visibility_range, visibility_range + 1):
                if abs(dx) + abs(dy) <= visibility_range:
                    new_x, new_y = x + dx, y + dy
                    if 0 <= new_x < game.map_size and 0 <= new_y < game.map_size:
                        visible_cells.add((new_x, new_y))

    return list(visible_cells)
