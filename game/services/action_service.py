from django.db import transaction
from django.utils import timezone
from game.core.models import Building, Unit, Turn, Game, Player
from game.utils.game_helpers import (
    is_valid_build_position,
    is_valid_move,
    is_valid_attack,
    calculate_damage,
    advance_game_if_all_turns_complete
)
from game.utils.resource_helpers import get_building_cost, get_unit_cost

class BaseActionHandler:
    def __init__(self, player, combat_service):
        self.player = player
        self.game = player.game
        self.combat_service = combat_service

    def validate_resources(self, cost):
        if self.player.resources < cost:
            raise ValueError("Insufficient resources")
        return True

    def deduct_resources(self, cost):
        self.player.resources -= cost
        self.player.save()

    def validate_unit_action(self, unit, action_type):
        if action_type == 'move' and unit.has_moved:
            raise ValueError("Unit has already moved")
        if action_type == 'attack' and unit.has_attacked:
            raise ValueError("Unit has already attacked")
        return True

class ActionService:
    def __init__(self, combat_service):
        self.combat_service = combat_service
        self.action_handlers = {
            'build': self._handle_build_action,
            'move_unit': self._handle_move_action,
            'attack': self._handle_attack_action,
            'train_unit': self._handle_train_action
        }

    @transaction.atomic
    def process_turn_actions(self, game, player, actions):
        """Process all actions for a player's turn"""
        if not game.is_active:
            raise ValueError("Game is not active")

        current_player = game.get_current_player()
        if current_player != player:
            raise ValueError("Not your turn")

        # Create or get turn record
        turn, created = Turn.objects.get_or_create(
            game=game,
            player=player,
            turn_number=game.current_turn
        )

        if turn.completed:
            raise ValueError("Turn already completed")

        handler = BaseActionHandler(player, self.combat_service)
        for action in actions:
            action_type = action.get('type')
            if action_type not in self.action_handlers:
                raise ValueError(f"Invalid action type: {action_type}")
            self.action_handlers[action_type](handler, action)

        # Mark turn as completed
        turn.completed = True
        turn.completed_at = timezone.now()
        turn.save()

        # Check if all players have completed their turns
        advance_game_if_all_turns_complete(game)

        return True

    def process_action(self, game_id, user, action_type, action_data):
        """Process a game action"""
        game = Game.objects.get(id=game_id)
        player = Player.objects.get(game=game, user=user)

        if not game.is_active:
            raise ValueError("Game is not active")

        if game.get_current_player() != player:
            raise ValueError("Not your turn")

        action_handlers = {
            'move_unit': self._handle_move_unit,
            'attack': self._handle_attack,
            'build': self._handle_build,
            'train_unit': self._handle_train_unit,
            'end_turn': self._handle_end_turn
        }

        handler = action_handlers.get(action_type)
        if not handler:
            raise ValueError(f"Invalid action type: {action_type}")

        return handler(game, player, action_data)

    def _handle_build_action(self, handler, action):
        """Handle building construction"""
        building_type = action.get('building_type')
        x, y = action.get('x'), action.get('y')
        
        # Validate position
        if not is_valid_build_position(x, y, handler.game):
            raise ValueError("Invalid build position")

        # Check cost
        cost = get_building_cost(building_type)
        handler.validate_resources(cost)

        # Create building
        Building.objects.create(
            player=handler.player,
            building_type=building_type,
            x_position=x,
            y_position=y
        )
        
        # Deduct resources
        handler.deduct_resources(cost)

    def _handle_move_action(self, handler, action):
        """Handle unit movement"""
        unit = Unit.objects.get(id=action.get('unit_id'), player=handler.player)
        handler.validate_unit_action(unit, 'move')

        x, y = action.get('x'), action.get('y')

        if not is_valid_move(unit, x, y, handler.game):
            raise ValueError("Invalid move")

        unit.x_position = x
        unit.y_position = y
        unit.has_moved = True
        unit.save()

    def _handle_attack_action(self, handler, action):
        """Handle unit attacks"""
        unit = Unit.objects.get(id=action.get('unit_id'), player=handler.player)
        handler.validate_unit_action(unit, 'attack')

        target_x, target_y = action.get('target_x'), action.get('target_y')
        target = (Unit.objects.filter(
            game=handler.game,
            x_position=target_x,
            y_position=target_y
        ).first() or Building.objects.filter(
            game=handler.game,
            x_position=target_x,
            y_position=target_y
        ).first())

        if not target or target.player == handler.player:
            raise ValueError("Invalid target")

        if not handler.combat_service.is_in_range(unit, target):
            raise ValueError("Target out of range")

        destroyed, damage = handler.combat_service.process_attack(unit, target)
        unit.has_attacked = True
        unit.save()

        return {
            'damage': damage,
            'target_destroyed': destroyed,
            'target_type': 'unit' if isinstance(target, Unit) else 'building'
        }

    def _handle_train_action(self, handler, action):
        """Handle unit training"""
        barracks_id = action.get('barracks_id')
        unit_type = action.get('unit_type')
        
        # Verify barracks exists and belongs to player
        barracks = Building.objects.get(
            id=barracks_id,
            player=handler.player,
            building_type='barracks'
        )

        # Check cost
        cost = get_unit_cost(unit_type)
        handler.validate_resources(cost)

        unit_stats = handler.combat_service.get_unit_stats(unit_type)
        Unit.objects.create(
            player=handler.player,
            unit_type=unit_type,
            x_position=barracks.x_position + 1,
            y_position=barracks.y_position,
            health=unit_stats.get('health', 100),
            attack=unit_stats.get('attack', 10),
            defense=unit_stats.get('defense', 5),
            movement_range=unit_stats.get('movement_range', 2),
            attack_range=unit_stats.get('attack_range', 1)
        )

        # Deduct resources
        handler.deduct_resources(cost)