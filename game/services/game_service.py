from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.exceptions import ValidationError
from game.core.models import Game, Player, Unit, Building, Turn
from game.utils.game_helpers import (
    generate_map,
    is_valid_move,
    is_valid_build_position
)
from game.core.game_rules import GAME_RULES
from .state_service import GameStateService
from .player_service import PlayerService
from .combat_service import CombatService
from .action_service import ActionService

class GameService:
    def __init__(self):
        self.combat_service = CombatService()
        self.action_service = ActionService(self.combat_service)
        self.state_service = GameStateService()
        self.player_service = PlayerService()

    @transaction.atomic
    def create_game(self, user, name, map_size, max_players):
        """Create a new game with initial setup"""
        game = Game.objects.create(
            name=name,
            map_size=map_size,
            max_players=max_players,
            created_by=user,
            map_data=generate_map(map_size),
        )
        
        self.add_player(game, user)
        return game

    def get_game_state(self, game_id, user):
        """Get the current state of a game for a user"""
        return self.state_service.get_game_state(game_id, user)

    def get_home_page_state(self, user):
        """Get the state for the home page"""
        return self.state_service.get_home_page_state(user)

    @transaction.atomic
    def add_player(self, game, user):
        """Add a new player to the game"""
        can_join, message = self.player_service.can_join_game(game, user)
        if not can_join:
            raise ValidationError(message)
        return self.player_service.add_player(game, user)

    @transaction.atomic
    def remove_player(self, game, user):
        """Remove a player from the game"""
        player = get_object_or_404(Player, game=game, user=user)
        self.player_service.deactivate_player(player)
        
        if not self.get_active_players(game).exists():
            self.deactivate_game(game)
        return True

    @transaction.atomic
    def process_turn_actions(self, game, player, actions):
        """Process a player's turn actions"""
        current_player = self.get_current_player(game)
        if current_player != player:
            raise ValidationError("Not your turn")

        turn = Turn.objects.create(
            game=game,
            player=player,
            turn_number=game.current_turn
        )

        try:
            result = self.action_service.process_turn_actions(game, player, actions)
            turn.completed = True
            turn.completed_at = timezone.now()
            turn.save()
            self.next_turn(game)
            return result
        except Exception as e:
            turn.delete()
            raise e

    def build_structure(self, game, player, building_type, x, y):
        """Build a structure at the specified coordinates"""
        if not game.is_active:
            raise ValidationError("Game is not active")

        current_player = self.get_current_player(game)
        if current_player != player:
            raise ValidationError("Not your turn")

        if not is_valid_build_position(game.map_data, x, y):
            raise ValidationError("Invalid build position")

        cost = GAME_RULES['BUILDING_COSTS'][building_type]
        if not self.player_service.has_enough_resources(player, cost):
            raise ValidationError("Not enough resources")

        building = Building.objects.create(
            player=player,
            building_type=building_type,
            x_position=x,
            y_position=y
        )

        self.player_service.update_resources(player, -cost)
        return building

    def move_unit(self, game, player, unit_id, x, y):
        """Move a unit to new coordinates"""
        if not game.is_active:
            raise ValidationError("Game is not active")

        current_player = self.get_current_player(game)
        if current_player != player:
            raise ValidationError("Not your turn")

        unit = get_object_or_404(Unit, id=unit_id, player=player)
        if unit.has_moved:
            raise ValidationError("Unit has already moved this turn")

        if not is_valid_move(unit, x, y, game.map_data):
            raise ValidationError("Invalid move position")

        unit.x_position = x
        unit.y_position = y
        unit.has_moved = True
        unit.save()
        return unit

    def train_unit(self, building, unit_type):
        """Train a new unit at a building"""
        game = building.player.game
        if not game.is_active:
            raise ValidationError("Game is not active")

        current_player = self.get_current_player(game)
        if current_player != building.player:
            raise ValidationError("Not your turn")

        cost = GAME_RULES['UNIT_COSTS'][unit_type]
        if not self.player_service.has_enough_resources(building.player, cost):
            raise ValidationError("Not enough resources")

        unit = Unit.objects.create(
            player=building.player,
            unit_type=unit_type,
            x_position=building.x_position,
            y_position=building.y_position
        )

        self.player_service.update_resources(building.player, -cost)
        return unit

    @transaction.atomic
    def next_turn(self, game):
        """Advance to the next turn"""
        active_players = self.get_active_players(game).count()
        if active_players == 0:
            raise ValidationError("No active players in game")
            
        game.current_turn += 1
        game.current_player_index = (game.current_player_index + 1) % active_players
        game.save()

        # Reset unit movement and attack flags
        Unit.objects.filter(player__game=game).update(
            has_moved=False,
            has_attacked=False
        )

    @transaction.atomic
    def deactivate_game(self, game):
        """Deactivate a game"""
        game.is_active = False
        game.save()

    def get_current_player(self, game):
        """Get the current player in the game"""
        if not game.players.exists():
            return None
        active_players = list(self.get_active_players(game))
        if not active_players:
            return None
        return active_players[game.current_player_index]

    def get_active_players(self, game):
        """Get all active players in the game"""
        return game.players.filter(is_active=True)

    def calculate_combat_stats(self, unit):
        """Calculate combat stats for a unit"""
        return {
            'combat_power': self.combat_service.calculate_combat_power(unit),
            'attack_range': self.combat_service.get_attack_range(unit)
        }
