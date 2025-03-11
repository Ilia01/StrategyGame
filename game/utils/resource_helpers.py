def get_building_cost(building_type):
    """Return the resource cost of a building type."""
    costs = {"barracks": 50, "farm": 30, "mine": 40}
    return costs.get(building_type, 0)

def get_unit_cost(unit_type):
    """Return the resource cost of a unit type."""
    costs = {"infantry": 20, "archer": 30, "cavalry": 40, "siege": 60}
    return costs.get(unit_type, 0)
