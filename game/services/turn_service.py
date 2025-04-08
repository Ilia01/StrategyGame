from django.db import transaction
from django.utils import timezone
from game.core.models import Turn, Game, Player

class TurnService:
    @transaction.atomic
    def create_turn(self, game, player, turn_number):
        """Create a new turn for a player"""
        return Turn.objects.create(
            game=game,
            player=player,
            turn_number=turn_number
        )

    @transaction.atomic
    def complete_turn(self, turn):
        """Mark a turn as completed"""
        turn.completed = True
        turn.completed_at = timezone.now()
        turn.save()

    def get_current_turn(self, game, player):
        """Get the current turn for a player in a game"""
        return Turn.objects.filter(
            game=game,
            player=player,
            turn_number=game.current_turn
        ).first()

    def get_completed_turns(self, game):
        """Get all completed turns for a game"""
        return Turn.objects.filter(
            game=game,
            completed=True
        ).order_by('turn_number')

    def is_turn_completed(self, game, player):
        """Check if the current turn is completed for a player"""
        turn = self.get_current_turn(game, player)
        return turn and turn.completed 