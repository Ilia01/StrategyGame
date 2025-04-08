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

        turn = Turn.objects.get_or_create(
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

        turn.completed = True
        turn.completed_at = timezone.now()
        turn.save()

        advance_game_if_all_turns_complete(game)

        return True

    def process_action(self, game_id, user_or_player, action_type, action_data):
        """Process a game action"""
        game = Game.objects.get(id=game_id)
        
        if isinstance(user_or_player, Player):
            player = user_or_player
        else:
            player = Player.objects.get(game=game, user=user_or_player)

        if not game.is_active:
            raise ValueError("Game is not active")

        try:
            current_player = game.players.all()[game.current_player_index]
            if current_player != player:
                raise ValueError("Not your turn")
        except (IndexError, Player.DoesNotExist):
            raise ValueError("Invalid game state")

        action_handlers = {
            'move_unit': self._handle_move_action,
            'attack': self._handle_attack_action,
            'build': self._handle_build_action,
            'train_unit': self._handle_train_action,
            'end_turn': self._handle_end_turn_action
        }

        handler = action_handlers.get(action_type)
        if not handler:
            raise ValueError(f"Invalid action type: {action_type}")

        return handler(game, player, action_data)

    def _handle_build_action(self, game, player, action_data):
        """Handle building construction"""
        building_type = action_data.get('building_type')
        x = action_data.get('x')
        y = action_data.get('y')
        
        if not all([building_type, x is not None, y is not None]):
            raise ValueError("Missing required fields for building action")

        if not is_valid_build_position(x, y, game):
            raise ValueError("Invalid build position")

        # Get building cost from constants
        building_data = BUILDING_TYPES.get(building_type)
        if not building_data:
            raise ValueError(f"Invalid building type: {building_type}")

        cost = building_data.get('cost', {})
        if not cost:
            raise ValueError(f"No cost defined for building type: {building_type}")

        # Check if player has enough resources
        for resource, amount in cost.items():
            if player.resources.get(resource, 0) < amount:
                raise ValueError(f"Insufficient {resource} for building {building_type}")

        # Create the building
        Building.objects.create(
            player=player,
            building_type=building_type,
            x_position=x,
            y_position=y,
            health=building_data.get('health', 200)
        )
        
        # Deduct resources
        for resource, amount in cost.items():
            player.resources[resource] -= amount
            player.save()

        return {"message": f"Successfully built {building_type}"}

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
        
        barracks = Building.objects.get(
            id=barracks_id,
            player=handler.player,
            building_type='barracks'
        )

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