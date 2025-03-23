from game.core.models import Unit, Building
from game.utils.game_helpers import is_valid_attack, calculate_damage

class CombatService:
    @staticmethod
    def process_attack(unit, target):
        if not is_valid_attack(unit, target):
            raise ValueError("Invalid attack")
            
        damage = calculate_damage(unit, target)
        target.health -= damage
        
        if target.health <= 0:
            target.delete()
            return True
        else:
            target.save()
            return False