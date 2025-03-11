from random import choices, randint

def generate_map(size):
    """Generate a random map with varied terrain."""
    terrain_types = ["plains", "forest", "mountain", "water"]
    map_data = {"size": size, "terrain": []}
    for y in range(size):
        row = []
        for x in range(size):
            # Weighting makes plains more common.
            terrain = choices(terrain_types, weights=[0.6, 0.2, 0.1, 0.1])[0]
            row.append(terrain)
        map_data["terrain"].append(row)
    return map_data

def get_starting_position(map_data, player_number, map_size):
    """Determine a starting position based on the player's number."""
    positions = [
        {"x": 1, "y": 1},                # Player 1: top-left
        {"x": map_size - 2, "y": map_size - 2},  # Player 2: bottom-right
        {"x": 1, "y": map_size - 2},       # Player 3: bottom-left
        {"x": map_size - 2, "y": 1},       # Player 4: top-right
    ]
    idx = min(player_number - 1, len(positions) - 1)
    position = positions[idx]
    # Ensure that starting position is plains.
    map_data["terrain"][position["y"]][position["x"]] = "plains"
    return position

def is_player_turn(game, player):
    """Check if it's the given player's turn."""
    current_player_number = (game.current_turn - 1) % game.max_players + 1
    return player.player_number == current_player_number

def is_valid_move(unit, x, y, game):
    """Determine if a move is valid."""
    if x < 0 or y < 0 or x >= game.map_size or y >= game.map_size:
        return False
    if abs(unit.x_position - x) + abs(unit.y_position - y) > unit.movement_range:
        return False
    # Check for collisions.
    from game.models import Unit, Building  # Import locally if needed
    if Unit.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False
    if Building.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False
    terrain = game.get_map()["terrain"][y][x]
    if terrain == "water":
        return False
    return True

def is_valid_attack(unit, target):
    """Check if the target is within attack range."""
    distance = abs(unit.x_position - target.x_position) + abs(unit.y_position - target.y_position)
    return distance <= unit.attack_range

def calculate_damage(attacker, defender):
    """Calculate damage based on attack and defense, plus a small random factor."""
    base_damage = (max(1, attacker.attack - getattr(defender, "defense", 0))
                   if hasattr(defender, "defense") else attacker.attack)
    return base_damage + randint(0, 3)

def is_valid_build_position(x, y, game):
    """Check if a building can be placed at the given position."""
    if x < 0 or y < 0 or x >= game.map_size or y >= game.map_size:
        return False
    from game.models import Unit, Building
    if Unit.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False
    if Building.objects.filter(game=game, x_position=x, y_position=y).exists():
        return False
    terrain = game.get_map()["terrain"][y][x]
    return terrain not in ["water", "mountain"]

def advance_game_if_all_turns_complete(game):
    """Advance the game state if all players have finished their turns."""
    from game.models import Player, Unit, Building, Turn
    player_count = Player.objects.filter(game=game).count()
    completed_turns = Turn.objects.filter(game=game, turn_number=game.current_turn, completed=True).count()
    if completed_turns >= player_count:
        Unit.objects.filter(game=game).update(has_moved=False, has_attacked=False)
        for player in Player.objects.filter(game=game):
            base_income = 5
            farm_income = player.buildings.filter(building_type="farm").count() * 3
            mine_income = player.buildings.filter(building_type="mine").count() * 5
            player.resources += base_income + farm_income + mine_income
            player.save()
        game.current_turn += 1
        game.save()

def calculate_visibility_map(game, player):
    """Determine which cells the player can see based on their units/buildings."""
    visibility_range = 3
    visible_cells = set()
    from game.models import Unit, Building
    entities = list(Unit.objects.filter(player=player)) + list(Building.objects.filter(player=player))
    for entity in entities:
        x, y = entity.x_position, entity.y_position
        for dx in range(-visibility_range, visibility_range + 1):
            for dy in range(-visibility_range, visibility_range + 1):
                if abs(dx) + abs(dy) <= visibility_range:
                    new_x, new_y = x + dx, y + dy
                    if 0 <= new_x < game.map_size and 0 <= new_y < game.map_size:
                        visible_cells.add((new_x, new_y))
    return list(visible_cells)
