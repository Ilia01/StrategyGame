import random
from django.utils import timezone
from game.core.models import Game, Player, Unit, Building, Turn
from game.core.constants import TERRAIN_TYPES

def generate_map(size):
    """Generate a random map with various terrain types."""
    terrain_types = list(TERRAIN_TYPES.values())
    weights = [t['spawn_weight'] for t in terrain_types]
    map_data = {"size": size, "terrain": []}
    
    for _ in range(size):
        row = []
        for _ in range(size):
            terrain = random.choices(
                [t['name'] for t in terrain_types], 
                weights=weights
            )[0]
            row.append(terrain)
        map_data["terrain"].append(row)
    return map_data

def get_terrain_movement_cost(terrain):
    """Get movement cost for a terrain type."""
    for terrain_data in TERRAIN_TYPES.values():
        if terrain_data['name'] == terrain:
            return terrain_data['movement_cost']
    return 1

def get_starting_position(map_data, player_number, map_size):
    """Determine starting position based on player number."""
    positions = [
        {"x": 1, "y": 1},
        {"x": map_size - 2, "y": map_size - 2},  
        {"x": 1, "y": map_size - 2},     
        {"x": map_size - 2, "y": 1},     
    ]
    idx = min(player_number - 1, len(positions) - 1)
    position = positions[idx]
    map_data.terrain[position["y"]][position["x"]] = "plains"
    return position

def is_player_turn(game, player):
    """Check if it's the player's turn."""
    if not game.players.exists():
        return False
    try:
        current_player = game.players.all()[game.current_player_index]
        return player.id == current_player.id
    except IndexError:
        return False

def is_valid_move(unit, x, y, game):
    """Check if a move is valid."""
    if x < 0 or y < 0 or x >= game.map_size or y >= game.map_size:
        return False
    distance = abs(unit.x_position - x) + abs(unit.y_position - y)
    if distance > unit.movement_range:
        return False
    if Unit.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False
    if Building.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False
    map_data = game.get_map()
    terrain = map_data["terrain"][y][x]
    if terrain == "water":
        return False
    return True

def is_valid_attack(unit, target):
    """Check if an attack is valid."""
    distance = abs(unit.x_position - target.x_position) + abs(unit.y_position - target.y_position)
    return distance <= unit.attack_range

def calculate_damage(attacker, defender):
    """Calculate damage for an attack."""
    if hasattr(defender, "defense"):
        base_damage = max(1, attacker.attack - defender.defense)
    else:
        base_damage = attacker.attack
    return base_damage + random.randint(0, 3)

def is_valid_build_position(x, y, game):
    """Check if a position is valid for building."""
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

def advance_game_if_all_turns_complete(game):
    """Advance the game if all players have completed their turn."""
    player_count = Player.objects.filter(game=game).count()
    completed_turns = Turn.objects.filter(
        game=game, turn_number=game.current_turn, completed=True
    ).count()

    if completed_turns >= player_count:
        Unit.objects.filter(game=game).update(has_moved=False, has_attacked=False)
        for player in Player.objects.filter(game=game):
            base_income = 5
            farm_income = Building.objects.filter(player=player, building_type="farm").count() * 3
            mine_income = Building.objects.filter(player=player, building_type="mine").count() * 5
            player.resources += base_income + farm_income + mine_income
            player.save()
        game.current_turn += 1
        game.save()

def _add_visible_cells(x, y, visibility_range, game_size, visible_cells):
    """Helper function to add visible cells for a given position."""
    for dx in range(-visibility_range, visibility_range + 1):
        for dy in range(-visibility_range, visibility_range + 1):
            if abs(dx) + abs(dy) <= visibility_range:
                new_x, new_y = x + dx, y + dy
                if 0 <= new_x < game_size and 0 <= new_y < game_size:
                    visible_cells.add((new_x, new_y))

def calculate_visibility_map(game, player):
    """Calculate which cells are visible to the player (fog-of-war)."""
    visibility_range = 3
    visible_cells = set()
    entities = list(Unit.objects.filter(player=player))
    entities.extend(Building.objects.filter(player=player))
    for entity in entities:
        x, y = entity.x_position, entity.y_position
        _add_visible_cells(x, y, visibility_range, game.map_size, visible_cells)
    return list(visible_cells)
