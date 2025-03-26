from .constants import UNIT_TYPES, BUILDING_TYPES, TERRAIN_TYPES

GAME_RULES = {
    'basic_rules': {
        'title': 'Basic Rules',
        'description': 'Each turn, players can build structures, train units, and move/attack with their existing units. Resources are earned each turn based on your buildings.'
    },
    'units': {
        'title': 'Units',
        'items': [
            {
                'name': unit_data['display'],
                'description': f"Health: {unit_data['health']}, Attack: {unit_data['attack']}, Defense: {unit_data['defense']}, Movement: {unit_data['movement_range']}, Range: {unit_data['attack_range']}, Cost: {unit_data['cost']}"
            }
            for unit_data in UNIT_TYPES.values()
        ]
    },
    'buildings': {
        'title': 'Buildings',
        'items': [
            {
                'name': building_data['display'],
                'description': f"Health: {building_data['health']}, Resource Production: {building_data['resource_production']}, Cost: {building_data['cost']}"
            }
            for building_data in BUILDING_TYPES.values()
        ]
    },
    'terrain': {
        'title': 'Terrain Types',
        'items': [
            {
                'name': terrain_data['name'].title(),
                'description': f"Movement Cost: {terrain_data['movement_cost']}"
            }
            for terrain_data in TERRAIN_TYPES.values()
        ]
    },
    'resources': {
        'title': 'Resources',
        'description': 'Earn resources from your base (10/turn), farms (5/turn), and mines (8/turn). Use resources to build structures and train units.'
    },
    'victory': {
        'title': 'Victory Conditions',
        'description': 'Destroy the enemy base or eliminate all enemy units and buildings to win the game.'
    }
}