from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from game.core.models import Game, Player, Unit, Building, Turn
from game.utils.game_helpers import (
    generate_map,
    get_starting_position,
    is_valid_build_position,
    is_valid_move,
    is_valid_attack,
    calculate_damage,
    advance_game_if_all_turns_complete
)

class GameService:
    @staticmethod
    @transaction.atomic
    def create_game(user, name, map_size, max_players):
        """Create a new game and initial player setup"""
        game = Game.objects.create(
            name=name,
            map_size=map_size,
            max_players=max_players,
            created_by=user
        )
        map_data = generate_map(map_size)
        game.set_map(map_data)
        game.save()

        # Create first player
        GameService.add_player_to_game(user, game)
        return game

    @staticmethod
    @transaction.atomic
    def add_player_to_game(user, game):
        """Add a new player to the game"""
        player_count = Player.objects.filter(game=game).count()
        if player_count >= game.max_players:
            raise ValueError("Game is full")
            
        if Player.objects.filter(user=user, game=game).exists():
            raise ValueError("Already in game")

        player_number = player_count + 1
        player = Player.objects.create(
            user=user,
            game=game,
            player_number=player_number
        )

        # Setup starting position
        map_data = game.get_map()
        starting_position = get_starting_position(map_data, player_number, game.map_size)
        
        # Create initial buildings and units
        Building.objects.create(
            player=player,
            building_type=Building.BASE,
            x_position=starting_position["x"],
            y_position=starting_position["y"]
        )
        
        Unit.objects.create(
            player=player,
            unit_type=Unit.INFANTRY,
            x_position=starting_position["x"] + 1,
            y_position=starting_position["y"]
        )
        
        return player

    @staticmethod
    @transaction.atomic
    def process_turn_actions(game, player, actions):
        """Process all actions for a player's turn"""
        for action in actions:
            action_type = action.get("type")
            
            if action_type == "build":
                GameService._handle_build_action(player, action)
            elif action_type == "move_unit":
                GameService._handle_move_action(game, player, action)
            elif action_type == "attack":
                GameService._handle_attack_action(game, player, action)

        # Create turn record
        Turn.objects.create(
            game=game,
            player=player,
            turn_number=game.current_turn,
            actions=actions,
            completed=True,
            completed_at=timezone.now()
        )

        advance_game_if_all_turns_complete(game)

    @staticmethod
    def _handle_build_action(player, action):
        """Handle building construction"""
        building_type = action.get("building_type")
        x = action.get("x")
        y = action.get("y")
        
        if not is_valid_build_position(x, y, player.game):
            raise ValueError(f"Invalid build position: {x}, {y}")
            
        Building.objects.create(
            player=player,
            building_type=building_type,
            x_position=x,
            y_position=y
        )

    @staticmethod
    def _handle_move_action(game, player, action):
        """Handle unit movement"""
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

    @staticmethod
    def _handle_attack_action(game, player, action):
        """Handle unit attacks"""
        unit_id = action.get("unit_id")
        target_x = action.get("target_x")
        target_y = action.get("target_y")
        
        unit = get_object_or_404(Unit, id=unit_id, player=player)
        target = (
            Unit.objects.filter(
                game=game,
                x_position=target_x,
                y_position=target_y
            ).exclude(player=player).first()
        )
        
        if not target:
            target = (
                Building.objects.filter(
                    game=game,
                    x_position=target_x,
                    y_position=target_y
                ).exclude(player=player).first()
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