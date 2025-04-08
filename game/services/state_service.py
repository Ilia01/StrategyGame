from .turn_service import TurnService
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch, Count
from django.utils import timezone
from django.db import transaction
from .base import BaseStateService
from game.core.models import Game, Player, Unit, Building
from game.api.serializers.game import GameSerializer
from game.core.game_rules import GAME_RULES
from django.db import models

class GameStateService(BaseStateService):
    def __init__(self):
        self.turn_service = TurnService()

    def get_game_state(self, game_id, user):
        """Get complete game state"""
        game = self._get_game_with_relations(game_id)
        
        return {
            "game_id": game.id,
            "name": game.name,
            "current_turn": game.current_turn,
            "current_player": self._get_current_player_data(game),
            "map_data": self._get_map_data(game),
            "players": self._get_players_data(game),
            "units": self._get_units_data(game),
            "buildings": self._get_buildings_data(game),
            "is_active": game.is_active
        }

    def get_current_player(self, game):
        """Get the current player for a game"""
        if not game.players.exists():
            return None
        return game.players.all()[game.current_player_index]

    def get_active_players(self, game):
        """Get all active players in a game"""
        return game.players.filter(is_active=True)

    def is_game_full(self, game):
        """Check if game has maximum number of players"""
        return self.get_active_players(game).count() >= game.max_players

    @transaction.atomic
    def advance_turn(self, game):
        """Advance to the next turn"""
        game.current_turn += 1
        game.current_player_index = (game.current_player_index + 1) % self.get_active_players(game).count()
        game.save()

    @transaction.atomic
    def deactivate_game(self, game):
        """Deactivate a game"""
        game.is_active = False
        game.save()

    def _get_game_with_relations(self, game_id):
        """Get game with all related data"""
        return Game.objects.select_related(
            'created_by'
        ).prefetch_related(
            'players__user',
            'players__units',
            'players__buildings'
        ).get(id=game_id)

    def get_home_page_state(self, user):
        active_games = Game.objects.filter(
            is_active=True
        ).select_related('created_by').annotate(
            player_count=Count('players', filter=models.Q(players__is_active=True))
        )
        # .prefetch_related(
        #     Prefetch('players', queryset=Player.objects.select_related('user')),
        #     'players__units',
        #     'players__buildings'
        
        my_games = active_games.filter(players__user=user).distinct()
        available_games = active_games.exclude(players__user=user).distinct()
        serialized_games = GameSerializer(active_games, many=True).data

        return {
            'active_games': available_games,
            'my_games': my_games,
            'serialized_games': serialized_games,
            'game_rules': self._get_game_rules()
        }

    def _get_player_context(self, game, user):
        try:
            player = Player.objects.select_related('user').get(user=user, game=game)
            current_player = self.get_current_player(game)
            return {
                'player': player,
                'is_player': True,
                'player_number': player.player_number,
                'player_resources': player.resources,
                'is_current_player': current_player and current_player.id == player.id
            }
        except Player.DoesNotExist:
            return {
                'player': None,
                'is_player': False,
                'can_join': game.active_players.count() < game.max_players
            }

    def _get_game_rules(self):
        return [
            {
                'title': section_data.get('title'),
                'description': section_data.get('description'),
                'items': section_data.get('items', [])
            }
            for section_data in GAME_RULES.values()
        ]

    def _get_current_player_data(self, game):
        """Get current player data for game state"""
        current_player = self.get_current_player(game)
        if not current_player:
            return None
            
        return {
            'id': current_player.id,
            'username': current_player.user.username,
            'player_number': current_player.player_number,
            'resources': current_player.resources
        }

    def _get_map_data(self, game):
        """Get map data including terrain and dimensions"""
        return {
            'size': game.map_size,
            'terrain': game.map_data["terrain"],
            'width': game.map_size,
            'height': game.map_size
        }

    def _get_players_data(self, game):
        """Get data for all players in the game"""
        players = game.players.select_related('user').all()
        return [
            {
                'id': player.id,
                'username': player.user.username,
                'player_number': player.player_number,
                'resources': player.resources,
                'is_active': player.is_active,
                'statistics': self._get_player_statistics(player)
            }
            for player in players
        ]

    def _get_player_statistics(self, player):
        """Get statistics for a player"""
        return {
            'unit_count': player.units.count(),
            'building_count': player.buildings.count(),
            'total_combat_power': self._calculate_total_combat_power(player),
            'resource_production': self._calculate_resource_production(player)
        }

    def _calculate_total_combat_power(self, player):
        """Calculate total combat power of player's units"""
        return sum(unit.get_combat_power() for unit in player.units.all())

    def _calculate_resource_production(self, player):
        """Calculate total resource production from buildings"""
        return sum(building.resource_production for building in player.buildings.all())

    def _get_units_data(self, game):
        """Get data for all units in the game"""
        units = Unit.objects.filter(player__game=game).select_related('player')
        return [
            {
                'id': unit.id,
                'type': unit.unit_type,
                'player_id': unit.player_id,
                'x': unit.x_position,
                'y': unit.y_position,
                'health': unit.health,
                'attack': unit.attack,
                'defense': unit.defense,
                'movement_range': unit.movement_range,
                'attack_range': unit.attack_range,
                'has_moved': unit.has_moved,
                'has_attacked': unit.has_attacked
            }
            for unit in units
        ]

    def _get_buildings_data(self, game):
        """Get data for all buildings in the game"""
        buildings = Building.objects.filter(player__game=game).select_related('player')
        return [
            {
                'id': building.id,
                'type': building.building_type,
                'player_id': building.player_id,
                'x': building.x_position,
                'y': building.y_position,
                'health': building.health,
                'resource_production': building.resource_production
            }
            for building in buildings
        ]

    def get_game_summary(self, game):
        """Get summary data for game listing"""
        return {
            'id': game.id,
            'name': game.name,
            'created_by': game.created_by.username,
            'map_size': game.map_size,
            'player_count': game.active_players.count(),
            'max_players': game.max_players,
            'current_turn': game.current_turn,
            'is_active': game.is_active,
            'created_at': game.created_at
        }