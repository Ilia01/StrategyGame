class GameApi {
    constructor() {
        this.baseUrl = '/api/games';
    }

    async fetchHandler(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCsrfToken()
            }
        };

        const response = await fetch(
            `${this.baseUrl}${endpoint}`,
            { ...defaultOptions, ...options }
        );

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || `Failed to ${options.method || 'GET'} ${endpoint}`);
        }

        return response.json();
    }

    async getGameConstants() {
        return await this.fetchHandler("/constants");
    }

    async getGameState(gameId) {
        return await this.fetchHandler(`/${gameId}/state/`);
    }

    async moveUnit(gameId, unitId, x, y) {
        return await this.fetchHandler(`/${gameId}/move_unit/`, {
            method: 'POST',
            body: JSON.stringify({ unit_id: unitId, x, y }),
        });
    }

    async buildStructure(gameId, buildingType, x, y) {
        console.log("Building structure:", { buildingType, x, y });
        return await this.fetchHandler(`/${gameId}/build_structure/`, {
            method: 'POST',
            body: JSON.stringify({ building_type: buildingType, x, y }),
        });
    }

    async trainUnit(gameId, buildingId, unitType) {
        return await this.fetchHandler(`/${gameId}/train_unit/`, {
            method: 'POST',
            body: JSON.stringify({ building_id: buildingId, unit_type: unitType }),
        });
    }

    async takeTurn(gameId, actions) {
        return await this.fetchHandler(`/${gameId}/take_turn/`, {
            method: 'POST',
            body: JSON.stringify({ actions }),
        });
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

export default new GameApi();