from game.core.constants import BUILDING_TYPES, UNIT_TYPES

def get_building_cost(building_type):
    """Return the resource cost for a building."""
    for building_data in BUILDING_TYPES.values():
        if building_data['name'] == building_type:
            return building_data['cost']
    return 0

def get_unit_cost(unit_type):
    """Return the resource cost for a unit."""
    for unit_data in UNIT_TYPES.values():
        if unit_data['name'] == unit_type:
            return unit_data['cost']
    return 0
