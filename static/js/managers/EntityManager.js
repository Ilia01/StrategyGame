export class EntityManager {
    constructor(game, mapManager) {
        this.game = game;
        this.mapManager = mapManager;
        this.selectedUnit = null;
        this.selectedBuilding = null;
    }

    renderEntities() {
        this.renderUnits();
        this.renderBuildings();
    }

    renderUnits() {
        const mapOverlay = this.mapManager.mapOverlay;
        if (!mapOverlay) {
            console.error('Cannot render units: map overlay not initialized');
            return;
        }

        const cellSize = this.mapManager.getCellSize();
        const gapSize = 1;

        this.game.state.units.forEach(unit => {
            const unitElement = this.createUnitElement(unit, cellSize, gapSize);
            mapOverlay.appendChild(unitElement);
        });
    }

    renderBuildings() {
        const mapOverlay = this.mapManager.mapOverlay;
        if (!mapOverlay) return;

        const cellSize = this.mapManager.getCellSize();
        const gapSize = 1;

        this.game.state.buildings.forEach(building => {
            const buildingElement = this.createBuildingElement(building, cellSize, gapSize);
            mapOverlay.appendChild(buildingElement);
        });
    }

    createUnitElement(unit, cellSize, gapSize) {
        const unitElement = document.createElement('div');
        unitElement.className = `entity unit ${unit.type} ${this.selectedUnit?.id === unit.id ? 'selected' : ''}`;

        const xPos = (unit.x * (cellSize + gapSize)) + gapSize;
        const yPos = (unit.y * (cellSize + gapSize)) + gapSize;

        this.setEntityPosition(unitElement, xPos, yPos, cellSize);
        this.setEntityData(unitElement, 'unit', unit);

        return unitElement;
    }

    createBuildingElement(building, cellSize, gapSize) {
        const buildingElement = document.createElement('div');
        buildingElement.className = `entity building ${building.type} ${this.selectedBuilding?.id === building.id ? 'selected' : ''}`;

        const xPos = (building.x * (cellSize + gapSize)) + gapSize;
        const yPos = (building.y * (cellSize + gapSize)) + gapSize;

        this.setEntityPosition(buildingElement, xPos, yPos, cellSize);
        this.setEntityData(buildingElement, 'building', building);

        return buildingElement;
    }

    setEntityPosition(element, xPos, yPos, cellSize) {
        element.style.position = 'absolute';
        element.style.left = `${xPos}px`;
        element.style.top = `${yPos}px`;
        element.style.width = `${cellSize}px`;
        element.style.height = `${cellSize}px`;
    }

    setEntityData(element, type, entity) {
        element.dataset[`${type}Id`] = entity.id;
        element.dataset.x = entity.x;
        element.dataset.y = entity.y;
    }

    selectAtPosition(x, y) {
        const units = this.game.state.getUnitsAtPosition(x, y);
        const buildings = this.game.state.getBuildingsAtPosition(x, y);

        if (units.length > 0) {
            this.selectedUnit = units[0];
            this.selectedBuilding = null;
        } else if (buildings.length > 0) {
            this.selectedBuilding = buildings[0];
            this.selectedUnit = null;
        } else {
            this.selectedUnit = null;
            this.selectedBuilding = null;
        }

        return {
            selectedUnit: this.selectedUnit,
            selectedBuilding: this.selectedBuilding
        };
    }

    getSelectedInfo() {
        if (this.selectedUnit) {
            return {
                type: 'unit',
                info: {
                    type: this.selectedUnit.type,
                    health: this.selectedUnit.health,
                    movement: this.selectedUnit.movement,
                    attack: this.selectedUnit.attack,
                    defense: this.selectedUnit.defense
                }
            };
        }
        if (this.selectedBuilding) {
            return {
                type: 'building',
                info: {
                    type: this.selectedBuilding.type,
                    health: this.selectedBuilding.health,
                    production: this.selectedBuilding.production
                }
            };
        }
        return null;
    }

    getSelectedUnit() {
        return this.selectedUnit;
    }

    getSelectedBuilding() {
        return this.selectedBuilding;
    }

    clearSelection() {
        this.selectedUnit = null;
        this.selectedBuilding = null;
    }
} 