from django.db import transaction
from game.core.models import Unit, Building
from game.utils.game_helpers import is_valid_attack, calculate_damage
from game.core.constants import UNIT_TYPES

class CombatService:
    def __init__(self):
        self.unit_types = UNIT_TYPES

    @transaction.atomic
    def process_attack(self, unit, target):
        """Process an attack between a unit and a target (unit or building)"""
        if not is_valid_attack(unit, target):
            raise ValueError("Invalid attack")
            
        damage = calculate_damage(unit, target)
        target.health -= damage
        
        if target.health <= 0:
            target.delete()
            return True, damage
        else:
            target.save()
            return False, damage

    def get_unit_stats(self, unit_type):
        """Get the base stats for a unit type"""
        return self.unit_types.get(unit_type, {})

    def calculate_combat_power(self, unit):
        """Calculate the total combat power of a unit"""
        stats = self.get_unit_stats(unit.unit_type)
        return (stats.get('attack', 0) + stats.get('defense', 0)) * (unit.health / 100)

    def get_effective_range(self, unit):
        """Get the effective range of a unit based on its type"""
        stats = self.get_unit_stats(unit.unit_type)
        return stats.get('attack_range', 1)

    def is_in_range(self, attacker, target):
        """Check if target is within attack range"""
        range = self.get_effective_range(attacker)
        dx = abs(attacker.x_position - target.x_position)
        dy = abs(attacker.y_position - target.y_position)
        return dx + dy <= range