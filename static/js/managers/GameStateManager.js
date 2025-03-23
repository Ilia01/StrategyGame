export class GameStateManager {
    constructor(gameId, playerId) {
        this.gameId = gameId;
        this.playerId = playerId;
        this.state = null;
        this.listeners = new Set();
    }

    updateState(newState) {
        this.state = newState;
        this.notifyListeners();
    }

    addListener(callback) {
        this.listeners.add(callback);
    }

    removeListener(callback) {
        this.listeners.delete(callback);
    }

    notifyListeners() {
        this.listeners.forEach(callback => callback(this.state));
    }

    isCurrentPlayer() {
        return this.state?.current_player_id === this.playerId;
    }

    getVisibleCells() {
        // Implement fog of war logic
        return this.state?.visible_cells || [];
    }
}