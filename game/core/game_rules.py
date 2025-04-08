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
    },
    'UNIT_TYPES': {
        'WORKER': {
            'name': 'worker',
            'display': 'Worker',
            'cost': 50,
            'description': 'Basic unit for resource gathering and construction',
            'attack': 2,
            'defense': 2,
            'movement': 2,
            'range': 1
        },
        'WARRIOR': {
            'name': 'warrior',
            'display': 'Warrior',
            'cost': 100,
            'description': 'Basic combat unit for close-range fighting',
            'attack': 5,
            'defense': 5,
            'movement': 2,
            'range': 1
        },
        'ARCHER': {
            'name': 'archer',
            'display': 'Archer',
            'cost': 125,
            'description': 'Ranged combat unit',
            'attack': 6,
            'defense': 3,
            'movement': 2,
            'range': 2
        }
    },
    'BUILDING_TYPES': {
        'TOWN_CENTER': {
            'name': 'town_center',
            'display': 'Town Center',
            'cost': 200,
            'description': 'Main building for resource collection and unit training',
            'health': 200,
            'production': 10
        },
        'BARRACKS': {
            'name': 'barracks',
            'display': 'Barracks',
            'cost': 100,
            'description': 'Military building for training combat units',
            'health': 150,
            'production': 5
        },
        'TOWER': {
            'name': 'tower',
            'display': 'Tower',
            'cost': 75,
            'description': 'Defensive structure with ranged attack',
            'health': 100,
            'attack': 4,
            'range': 3
        }
    },
    'TERRAIN_TYPES': {
        'PLAINS': {
            'name': 'plains',
            'movement_cost': 1,
            'defense_bonus': 0
        },
        'FOREST': {
            'name': 'forest',
            'movement_cost': 2,
            'defense_bonus': 0.2  # 20% defense bonus
        },
        'MOUNTAIN': {
            'name': 'mountain',
            'movement_cost': 3,
            'defense_bonus': 0.3  # 30% defense bonus
        },
        'WATER': {
            'name': 'water',
            'movement_cost': None,  # Impassable
            'defense_bonus': -0.5  # 50% defense penalty
        }
    },
    'GAME_SETTINGS': {
        'MAX_PLAYERS': 4,
        'MIN_PLAYERS': 2,
        'STARTING_RESOURCES': 500,
        'RESOURCE_GAIN_PER_TURN': 50,
        'MAX_TURNS': 100,
        'MAP_SIZES': [16, 24, 32],  # Valid map sizes
        'TURN_TIME_LIMIT': 300,  # 5 minutes per turn
        'INITIAL_UNITS': [
            {'type': 'WORKER', 'count': 2},
            {'type': 'WARRIOR', 'count': 1}
        ],
        'INITIAL_BUILDINGS': [
            {'type': 'TOWN_CENTER', 'count': 1}
        ]
    }
}