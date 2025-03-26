export class ConstantsManager {
    constructor() {
        this.constants = null;
        this.initialized = false;
    }

    async initialize() {
        try {
            const response = await fetch('/api/constants/');
            this.constants = await response.json();
            this.initialized = true;
        } catch (error) {
            console.error('Failed to load game constants:', error);
            throw error;
        }
    }

    get units() {
        return this.constants?.units || {};
    }

    get buildings() {
        return this.constants?.buildings || {};
    }

    get terrain() {
        return this.constants?.terrain || {};
    }

    get mapSizes() {
        return this.constants?.mapSizes || {};
    }

    get playerCounts() {
        return this.constants?.playerCounts || {};
    }

    getUnitStats(unitType) {
        return this.units[unitType.toUpperCase()] || null;
    }

    getBuildingStats(buildingType) {
        return this.buildings[buildingType.toUpperCase()] || null;
    }

    getTerrainInfo(terrainType) {
        return this.terrain[terrainType.toUpperCase()] || null;
    }
}