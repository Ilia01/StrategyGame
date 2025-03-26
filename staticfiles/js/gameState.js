export class GameState {
    constructor() {
        this.reset();
    }

    reset() {
        this.id = null;
        this.map_size = 0;
        this.map = [];
        this.units = [];
        this.buildings = [];
        this.players = [];
        this.current_turn = 1;
        this.current_player_id = null;
        this.game_status = 'waiting'; // waiting, in_progress, finished
        this.winner_id = null;
        this.resources = {
            gold: 0,
            wood: 0,
            stone: 0
        };
        this.lastUpdate = null;
    }

    update(data) {
        this.id = data.id;
        this.map_size = data.map_size;
        this.map = data.map;
        this.units = data.units;
        this.buildings = data.buildings;
        this.players = data.players;
        this.current_turn = data.current_turn;
        this.current_player_id = data.current_player_id;
        this.game_status = data.game_status;
        this.winner_id = data.winner_id;
        this.resources = data.resources;
        this.lastUpdate = new Date();
    }

    getCurrentPlayer() {
        return this.players.find(p => p.id === this.current_player_id);
    }

    getPlayerById(playerId) {
        return this.players.find(p => p.id === playerId);
    }

    getPlayerUnits(playerId) {
        return this.units.filter(u => u.player_id === playerId);
    }

    getPlayerBuildings(playerId) {
        return this.buildings.filter(b => b.player_id === playerId);
    }

    getUnitById(unitId) {
        return this.units.find(u => u.id === unitId);
    }

    getBuildingById(buildingId) {
        return this.buildings.find(b => b.id === buildingId);
    }

    getUnitsAtPosition(x, y) {
        return this.units.filter(u => u.x_position === x && u.y_position === y);
    }

    getBuildingsAtPosition(x, y) {
        return this.buildings.filter(b => b.x_position === x && b.y_position === y);
    }

    isCurrentPlayer(playerId) {
        return this.current_player_id === playerId;
    }

    isGameFinished() {
        return this.game_status === 'finished';
    }

    isGameInProgress() {
        return this.game_status === 'in_progress';
    }

    isWaitingForPlayers() {
        return this.game_status === 'waiting';
    }

    getWinner() {
        if (!this.winner_id) return null;
        return this.getPlayerById(this.winner_id);
    }

    getPlayerResources(playerId) {
        const player = this.getPlayerById(playerId);
        return player ? player.resources : null;
    }

    getTerrainAt(x, y) {
        if (x < 0 || x >= this.map_size || y < 0 || y >= this.map_size) {
            return null;
        }
        return this.map[y][x];
    }

    isValidPosition(x, y) {
        return x >= 0 && x < this.map_size && y >= 0 && y < this.map_size;
    }

    isPositionOccupied(x, y) {
        return this.getUnitsAtPosition(x, y).length > 0 || 
               this.getBuildingsAtPosition(x, y).length > 0;
    }

    getDistance(x1, y1, x2, y2) {
        return Math.abs(x2 - x1) + Math.abs(y2 - y1);
    }

    isInRange(x1, y1, x2, y2, range) {
        return this.getDistance(x1, y1, x2, y2) <= range;
    }

    getAdjacentPositions(x, y) {
        const positions = [];
        const directions = [
            { dx: 0, dy: -1 }, // up
            { dx: 1, dy: 0 },  // right
            { dx: 0, dy: 1 },  // down
            { dx: -1, dy: 0 }  // left
        ];

        directions.forEach(dir => {
            const newX = x + dir.dx;
            const newY = y + dir.dy;
            if (this.isValidPosition(newX, newY)) {
                positions.push({ x: newX, y: newY });
            }
        });

        return positions;
    }

    getPositionsInRange(x, y, range) {
        const positions = [];
        for (let dx = -range; dx <= range; dx++) {
            for (let dy = -range; dy <= range; dy++) {
                const newX = x + dx;
                const newY = y + dy;
                if (this.isValidPosition(newX, newY) && 
                    this.getDistance(x, y, newX, newY) <= range) {
                    positions.push({ x: newX, y: newY });
                }
            }
        }
        return positions;
    }

    getValidMovePositions(unit) {
        const positions = this.getPositionsInRange(
            unit.x_position,
            unit.y_position,
            unit.movement_range
        );
        return positions.filter(pos => !this.isPositionOccupied(pos.x, pos.y));
    }

    getValidAttackPositions(unit) {
        const positions = this.getPositionsInRange(
            unit.x_position,
            unit.y_position,
            unit.attack_range
        );
        return positions.filter(pos => {
            const targetUnit = this.getUnitsAtPosition(pos.x, pos.y)[0];
            const targetBuilding = this.getBuildingsAtPosition(pos.x, pos.y)[0];
            return (targetUnit && targetUnit.player_id !== unit.player_id) ||
                   (targetBuilding && targetBuilding.player_id !== unit.player_id);
        });
    }

    getValidBuildPositions(playerId) {
        const positions = [];
        const playerBuildings = this.getPlayerBuildings(playerId);
        
        // Get positions adjacent to player's buildings
        playerBuildings.forEach(building => {
            const adjacentPositions = this.getAdjacentPositions(
                building.x_position,
                building.y_position
            );
            positions.push(...adjacentPositions);
        });

        // Remove duplicates and occupied positions
        return positions.filter((pos, index, self) =>
            index === self.findIndex(p => p.x === pos.x && p.y === pos.y) &&
            !this.isPositionOccupied(pos.x, pos.y)
        );
    }
} 