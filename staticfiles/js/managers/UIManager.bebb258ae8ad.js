import { TERRAIN_COLORS, UNIT_STATS } from '../utils/constants.js';
import { getUnitTypeIcon, getBuildingTypeIcon } from '../utils/helpers.js';

export class UIManager {
    constructor(gameStateManager) {
        this.gameStateManager = gameStateManager;
        this.selectedEntity = null;
        this.pendingAction = null;
        
        // Initialize UI elements
        this.boardElement = document.getElementById('game-board');
        this.actionInfo = document.getElementById('action-info');
        this.cancelActionBtn = document.getElementById('cancel-action-btn');
        this.endTurnBtn = document.getElementById('end-turn-btn');
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.cancelActionBtn.addEventListener('click', () => this.cancelAction());
        this.endTurnBtn.addEventListener('click', () => this.submitTurn());
    }

    renderBoard() {
        const state = this.gameStateManager.state;
        if (!state) return;

        this.boardElement.innerHTML = '';
        const size = state.map_size;

        for (let y = 0; y < size; y++) {
            const row = document.createElement('div');
            row.className = 'board-row';

            for (let x = 0; x < size; x++) {
                const cell = this.createCell(x, y);
                row.appendChild(cell);
            }

            this.boardElement.appendChild(row);
        }
    }

    createCell(x, y) {
        const state = this.gameStateManager.state;
        const cell = document.createElement('div');
        cell.className = 'board-cell';
        cell.dataset.x = x;
        cell.dataset.y = y;

        // Apply terrain
        const terrain = state.map_data.terrain[y][x];
        cell.style.backgroundColor = TERRAIN_COLORS[terrain];

        // Add unit or building if present
        const entity = this.getEntityAt(x, y);
        if (entity) {
            const entityElement = this.createEntityElement(entity);
            cell.appendChild(entityElement);
        }

        cell.addEventListener('click', () => this.handleCellClick(x, y));
        return cell;
    }

    createEntityElement(entity) {
        const element = document.createElement('div');
        element.className = `entity ${entity.type}`;
        element.dataset.id = entity.id;
        element.dataset.type = entity.type;
        element.dataset.playerId = entity.player_id;

        // Add icon based on type
        element.innerHTML = entity.type === 'unit' 
            ? getUnitTypeIcon(entity.unit_type)
            : getBuildingTypeIcon(entity.building_type);

        // Add health bar
        const healthBar = document.createElement('div');
        healthBar.className = 'health-bar';
        healthBar.style.width = `${entity.health}%`;
        element.appendChild(healthBar);

        return element;
    }

    handleCellClick(x, y) {
        if (!this.gameStateManager.isCurrentPlayer()) return;

        if (this.pendingAction) {
            this.executePendingAction(x, y);
        } else {
            const entity = this.getEntityAt(x, y);
            if (entity && entity.player_id === this.gameStateManager.playerId) {
                this.selectEntity(entity);
            }
        }
    }

    // ... other UI methods
}