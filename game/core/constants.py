# Game Configuration Constants
GAME_MIN_MAP_SIZE = 10
GAME_MAX_MAP_SIZE = 30
GAME_MIN_PLAYERS = 2
GAME_MAX_PLAYERS = 4

# Map Size Options
MAP_SIZE_CHOICES = [
    (10, "Small (10x10)"),
    (15, "Medium (15x15)"),
    (20, "Large (20x20)"),
]

# Player Count Options
MAX_PLAYERS_CHOICES = [
    (2, "2 Players"),
    (3, "3 Players"),
    (4, "4 Players"),
]

# Unit Types and Stats
UNIT_TYPES = {
    'INFANTRY': {
        'name': 'infantry',
        'display': 'Infantry',
        'health': 100,
        'attack': 10,
        'defense': 5,
        'movement_range': 2,
        'attack_range': 1,
        'cost': 20
    },
    'ARCHER': {
        'name': 'archer',
        'display': 'Archer',
        'health': 70,
        'attack': 15,
        'defense': 3,
        'movement_range': 2,
        'attack_range': 3,
        'cost': 30
    },
    'CAVALRY': {
        'name': 'cavalry',
        'display': 'Cavalry',
        'health': 120,
        'attack': 12,
        'defense': 7,
        'movement_range': 4,
        'attack_range': 1,
        'cost': 40
    },
    'SIEGE': {
        'name': 'siege',
        'display': 'Siege Engine',
        'health': 80,
        'attack': 20,
        'defense': 4,
        'movement_range': 1,
        'attack_range': 2,
        'cost': 60
    }
}

# Building Types and Stats
BUILDING_TYPES = {
    'BASE': {
        'name': 'base',
        'display': 'Base',
        'health': 300,
        'resource_production': 10,
        'cost': 0
    },
    'BARRACKS': {
        'name': 'barracks',
        'display': 'Barracks',
        'health': 200,
        'resource_production': 0,
        'cost': 50
    },
    'FARM': {
        'name': 'farm',
        'display': 'Farm',
        'health': 100,
        'resource_production': 5,
        'cost': 30
    },
    'MINE': {
        'name': 'mine',
        'display': 'Mine',
        'health': 150,
        'resource_production': 8,
        'cost': 40
    }
}

# Terrain Types
TERRAIN_TYPES = {
    'PLAINS': {
        'name': 'plains',
        'movement_cost': 1,
        'spawn_weight': 0.6
    },
    'FOREST': {
        'name': 'forest',
        'movement_cost': 2,
        'spawn_weight': 0.2
    },
    'MOUNTAIN': {
        'name': 'mountain',
        'movement_cost': 3,
        'spawn_weight': 0.1
    },
    'WATER': {
        'name': 'water',
        'movement_cost': float('inf'),
        'spawn_weight': 0.1
    }
}