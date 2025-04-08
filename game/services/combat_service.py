from django.db import transaction
from django.core.exceptions import ValidationError
from game.core.models import Unit, Building
from game.core.game_rules import GAME_RULES

class CombatService:
    def __init__(self):
        self.player_service = None  # Will be set by dependency injection

    def validate_attack(self, attacker, target):
        """Validate if an attack is legal"""
        if not attacker.is_active:
            raise ValidationError("Attacker unit is not active")
            
        if attacker.has_attacked:
            raise ValidationError("Unit has already attacked this turn")
            
        if attacker.health <= 0:
            raise ValidationError("Dead units cannot attack")

        # Check range
        dx = abs(target.x_position - attacker.x_position)
        dy = abs(target.y_position - attacker.y_position)
        attack_range = max(dx, dy)
        
        unit_stats = GAME_RULES['UNIT_TYPES'].get(attacker.unit_type, {})
        max_range = unit_stats.get('range', 1)
        
        if attack_range > max_range:
            raise ValidationError("Target is out of range")

    def calculate_damage(self, attacker, defender, terrain_type):
        """Calculate combat damage"""
        # Get base stats
        attacker_stats = GAME_RULES['UNIT_TYPES'].get(attacker.unit_type, {})
        base_attack = attacker_stats.get('attack', 0)
        
        # Apply terrain modifiers
        terrain_mod = self.get_terrain_modifier(terrain_type)
        
        # Calculate base damage
        damage = round(base_attack * terrain_mod)
        
        # Ensure minimum damage
        return max(1, damage)

    def get_terrain_modifier(self, terrain_type):
        """Get terrain combat modifier"""
        TERRAIN_MODIFIERS = {
            'forest': 0.8,  # 20% reduction
            'mountain': 0.7,  # 30% reduction
            'water': 0.5,    # 50% reduction
            'plains': 1.0    # No modification
        }
        return TERRAIN_MODIFIERS.get(terrain_type, 1.0)

    @transaction.atomic
    def process_attack(self, attacker, target, game_map):
        """Process an attack between units or against buildings"""
        # Validate the attack
        self.validate_attack(attacker, target)
        
        # Get terrain at target location
        terrain_type = game_map['terrain'][target.y_position * game_map['size'] + target.x_position]
        
        # Calculate and apply damage
        damage = self.calculate_damage(attacker, target, terrain_type)
        
        # Apply damage to target
        target.health -= damage
        if target.health <= 0:
            target.is_active = False
        target.save()
        
        # Mark attacker as having attacked
        attacker.has_attacked = True
        attacker.save()
        
        return {
            'damage_dealt': damage,
            'target_destroyed': not target.is_active,
            'target_health': max(0, target.health)
        }

    def can_attack(self, attacker, target):
        """Check if a unit can attack a target"""
        try:
            self.validate_attack(attacker, target)
            return True, None
        except ValidationError as e:
            return False, str(e)

    def get_attack_range(self, unit):
        """Get the attack range of a unit"""
        unit_stats = GAME_RULES['UNIT_TYPES'].get(unit.unit_type, {})
        return unit_stats.get('range', 1)

    def get_valid_targets(self, unit, game):
        """Get all valid targets for a unit"""
        if not unit.is_active or unit.has_attacked:
            return []
            
        attack_range = self.get_attack_range(unit)
        valid_targets = []
        
        # Check units
        for target in Unit.objects.filter(game=game, is_active=True):
            if target.player_id != unit.player_id:  # Don't attack own units
                dx = abs(target.x_position - unit.x_position)
                dy = abs(target.y_position - unit.y_position)
                if max(dx, dy) <= attack_range:
                    valid_targets.append(target)
                    
        # Check buildings
        for target in Building.objects.filter(game=game, is_active=True):
            if target.player_id != unit.player_id:  # Don't attack own buildings
                dx = abs(target.x_position - unit.x_position)
                dy = abs(target.y_position - unit.y_position)
                if max(dx, dy) <= attack_range:
                    valid_targets.append(target)
                    
        return valid_targets