from django.db import transaction
from game.utils.game_helpers import get_starting_position
from game.core.models import Player, Building, Unit

class PlayerService:
    @transaction.atomic
    def add_player(self, user, game):
        """Add a new player to the game with starting resources and units"""
        if not game.is_active:
            raise ValueError("Cannot join inactive game")
            
        if game.is_full:
            raise ValueError("Game is full")
            
        if game.players.filter(user=user).exists():
            raise ValueError("Already in game")

        player = Player.objects.create(
            user=user,
            game=game,
            player_number=game.active_players.count() + 1
        )

        starting_position = get_starting_position(
            game.map_data, 
            player.player_number,
            game.map_size
        )

        Building.objects.create(
            player=player,
            building_type='base',
            x_position=starting_position['x'],
            y_position=starting_position['y'],
            health=300,
            resource_production=10
        )

        Unit.objects.create(
            player=player,
            unit_type='infantry',
            x_position=starting_position['x'] + 1,
            y_position=starting_position['y'],
            health=100,
            attack=10,
            defense=5,
            movement_range=2,
            attack_range=1
        )

        return player

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
            "is_active": player.is_active # debatable
        }