/**
 * Turn-Based Strategy Game
 * Game constants
 */

// Terrain colors
export const TERRAIN_COLORS = {
  plains: "#a0d6a0",
  forest: "#2d862d",
  mountain: "#8c8c8c",
  water: "#4da6ff",
};

// Unit costs
export const UNIT_COSTS = {
  infantry: 20,
  archer: 30,
  cavalry: 40,
  siege: 60,
};

// Building costs
export const BUILDING_COSTS = {
  barracks: 50,
  farm: 30,
  mine: 40,
};

// Unit stats
export const UNIT_STATS = {
  infantry: {
    health: 100,
    attack: 30,
    range: 1,
    movement: 2,
  },
  archer: {
    health: 70,
    attack: 40,
    range: 3,
    movement: 2,
  },
  cavalry: {
    health: 120,
    attack: 35,
    range: 1,
    movement: 4,
  },
  siege: {
    health: 80,
    attack: 60,
    range: 2,
    movement: 1,
  },
};

// Building stats
export const BUILDING_STATS = {
  base: {
    health: 300,
    resourcesPerTurn: 10,
  },
  barracks: {
    health: 200,
    resourcesPerTurn: 0,
  },
  farm: {
    health: 100,
    resourcesPerTurn: 5,
  },
  mine: {
    health: 150,
    resourcesPerTurn: 8,
  },
};
