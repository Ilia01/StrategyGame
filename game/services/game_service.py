from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Prefetch
from game.core.models import Game, Player, Unit, Building, Turn
from game.utils.game_helpers import (
    generate_map,
    get_starting_position,
    is_valid_build_position,
    is_valid_move,
    is_valid_attack,
    calculate_damage
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
            map_data=generate_map(map_size)
        )
        
        game.add_player(user)
        return game

    def get_game_state(self, game_id, user):
        """Get the current state of a game for a user"""
        return self.state_service.get_game_state(game_id, user)

    def get_home_page_state(self, user):
        """Get the state for the home page"""
        return self.state_service.get_home_page_state(user)

    @transaction.atomic
    def manage_player_in_game(self, user, game, action='add'):
        """Add or remove a player from a game"""
        if action == 'add':
            return game.add_player(user)
        elif action == 'remove':
            player = game.players.get(user=user)
            player.deactivate()
            return True
        raise ValueError(f"Invalid action: {action}")

    @transaction.atomic
    def process_turn_actions(self, game, player, actions):
        """Process a player's turn actions"""
        if game.current_player != player:
            raise ValueError("Not your turn")

        turn = Turn.objects.create(
            game=game,
            player=player,
            turn_number=game.current_turn
        )

        try:
            result = self.action_service.process_turn_actions(game, player, actions)
            turn.complete()
            game.next_turn()
            return result
        except Exception as e:
            turn.delete()
            raise e

    def get_unit_stats(self, unit_type):
        """Get the stats for a unit type"""
        return self.combat_service.get_unit_stats(unit_type)

    def calculate_combat_power(self, unit):
        """Calculate the combat power of a unit"""
        return self.combat_service.calculate_combat_power(unit)

    def is_in_attack_range(self, attacker, target):
        """Check if a target is within attack range"""
        return self.combat_service.is_in_range(attacker, target)
    
    def build_structure(self, game, player, building_type, x, y):
        """Build a structure on the map"""
        return self.action_service.process_action(game, player, 'build', {
            'building_type': building_type,
            'x': x,
            'y': y
        })
