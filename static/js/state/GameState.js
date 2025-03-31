export class GameState {
    constructor() {
        this.reset();
    }

    reset() {
        this.map = null;
        this.mapSize = 0;
        this.units = new Map();
        this.buildings = new Map();
        this.resources = {
            gold: 0,
            wood: 0,
            stone: 0
        };
        this.currentTurn = 0;
        this.currentPlayer = null;
        this.players = new Map();
        this.gameStatus = 'waiting'; // waiting, in_progress, finished
        this.winner = null;
        this.lastUpdate = null;
    }

    update(newState) {

        // Update map if changed
        if (newState.map_data) {
            this.mapSize = newState.map_data.size;
            this.map = newState.map_data.terrain;
        }

        if (newState.units) {
            this.units.clear();
            newState.units.forEach(unit => {
                this.units.set(unit.id, unit);
            });
        }

        if (newState.buildings) {
            this.buildings.clear();
            newState.buildings.forEach(building => {
                this.buildings.set(building.id, building);
            });
        }

        if (newState.resources) {
            this.resources = { ...this.resources, ...newState.resources };
        }

        if (newState.current_turn !== undefined) {
            this.currentTurn = newState.current_turn;
        }
        if (newState.current_player !== undefined) {
            this.currentPlayer = newState.current_player;
        }
        if (newState.players) {
            this.players.clear();
            newState.players.forEach(player => {
                this.players.set(player.id, player);
            });
        }
        if (newState.game_status) {
            this.gameStatus = newState.game_status;
        }
        if (newState.winner !== undefined) {
            this.winner = newState.winner;
        }

        this.lastUpdate = new Date();
    }

    getMapCell(x, y) {
        if (!this.map || x < 0 || y < 0 || x >= this.mapSize || y >= this.mapSize) {
            console.warn(`Invalid cell coordinates: (${x}, ${y})`);
            return null;
        }
        const terrain = this.map[y][x];
        return { terrain };
    }

    getMapSize() {
        return this.mapSize;
    }

    getUnit(unitId) {
        return this.units.get(unitId);
    }

    getBuilding(buildingId) {
        return this.buildings.get(buildingId);
    }

    getPlayer(playerId) {
        return this.players.get(playerId);
    }

    getUnitsAtPosition(x, y) {
        return Array.from(this.units.values()).filter(unit =>
            unit.x === x && unit.y === y
        );
    }

    getBuildingsAtPosition(x, y) {
        return Array.from(this.buildings.values()).filter(building =>
            building.x === x && building.y === y
        );
    }

    isCurrentPlayer(playerId) {
        return this.currentPlayer === playerId;
    }

    isGameFinished() {
        return this.gameStatus === 'finished';
    }

    hasWinner() {
        return this.winner !== null;
    }

    getResourceAmount(resourceType) {
        return this.resources[resourceType] || 0;
    }

    canAfford(costs) {
        return Object.entries(costs).every(([resource, amount]) =>
            this.getResourceAmount(resource) >= amount
        );
    }

    spendResources(costs) {
        if (!this.canAfford(costs)) {
            return false;
        }
        Object.entries(costs).forEach(([resource, amount]) => {
            this.resources[resource] -= amount;
        });
        return true;
    }

    isInPlayerTerritory(x, y, playerId) {
        // Get all buildings owned by the player
        const playerBuildings = this.buildings.filter(building => building.player_id === playerId);
        
        // If player has no buildings, they have no territory
        if (playerBuildings.length === 0) return false;
        
        // Check if the cell is adjacent to any of the player's buildings
        return playerBuildings.some(building => {
            const dx = Math.abs(building.x - x);
            const dy = Math.abs(building.y - y);
            // Consider cells adjacent to buildings (including diagonals) as territory
            return dx <= 1 && dy <= 1;
        });
    }
} 