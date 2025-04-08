from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth import get_user_model
from game.core.models import Player, Game, Unit, Building
from game.core.game_rules import GAME_RULES
from django.core.exceptions import ValidationError

class PlayerService:
    def can_join_game(self, game, user):
        """Check if a user can join a game"""
        if not game.is_active:
            return False, "Game is not active"
            
        if game.players.filter(user=user).exists():
            return False, "You are already in this game"
            
        active_players = game.players.filter(is_active=True)
        if active_players.count() >= game.max_players:
            return False, "Game is full"
            
        return True, None

    @transaction.atomic
    def add_player(self, game, user):
        """Add a player to a game with initial setup"""
        active_players = game.players.filter(is_active=True)
        player = Player.objects.create(
            game=game,
            user=user,
            player_number=active_players.count() + 1,
            resources=GAME_RULES.get("INITIAL_RESOURCES"),
        )
        
        self._initialize_player_state(player)
        return player

    @transaction.atomic
    def deactivate_player(self, player):
        """Deactivate a player and their entities"""
        player.is_active = False
        player.save()
        
        Unit.objects.filter(player=player).update(is_active=False)
        Building.objects.filter(player=player).update(is_active=False)

    def get_player_resources(self, player):
        """Get player's current resources"""
        return player.resources

    def update_resources(self, player, amount):
        """Update player's resources"""
        player.resources += amount
        player.save()

    def has_enough_resources(self, player, cost):
        """Check if player has enough resources"""
        return player.resources >= cost

    @transaction.atomic
    def _initialize_player_state(self, player):
        """Initialize a new player's starting units and buildings"""
        starting_units = GAME_RULES.get("STARTING_UNITS", {})
        for unit_type, count in starting_units.items():
            for _ in range(count):
                Unit.objects.create(
                    player=player,
                    unit_type=unit_type,
                    x_position=player.game.map_size // 2,
                    y_position=player.game.map_size // 2
                )
                
        starting_buildings = GAME_RULES.get("STARTING_BUILDINGS", {})
        for building_type, count in starting_buildings.items():
            for _ in range(count):
                Building.objects.create(
                    player=player,
                    building_type=building_type,
                    x_position=player.game.map_size // 2,
                    y_position=player.game.map_size // 2
                )

    def is_player_in_game(self, user, game_id):
        """Check if user is a player in the game"""
        return Player.objects.filter(
            game_id=game_id,
            user=user,
            is_active=True
        ).exists()

    def get_player_data(self, player):
        """Get player data for state updates"""
        return {
            "id": player.id, 
            "username": player.user.username,
            "player_number": player.player_number,
            "resources": player.resources,
            "is_active": player.is_active
        }

    @transaction.atomic
    def remove_player(self, user, game):
        """Remove a player from the game"""
        try:
            player = Player.objects.get(user=user, game=game)
        except Player.DoesNotExist:
            raise ValueError("Player not in game")

        player.deactivate()
        player.units.all().delete()
        player.buildings.all().delete()

        if game.active_players.count() == 0:
            game.deactivate()
            
        return True