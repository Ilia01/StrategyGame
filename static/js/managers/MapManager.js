export class MapManager {
    constructor(game) {
        this.game = game;
        this.container = document.getElementById('game-board');
        this.gridContainer = this.container.querySelector('.board-grid');
        this.mapOverlay = this.container.querySelector('.board-overlay');
        this.hoveredCell = null;
        this.clickedCell = null;

        if (!this.container || !this.gridContainer || !this.mapOverlay) {
            console.error('Required map elements not found');
            return;
        }
    }

    renderMap() {
        const mapSize = this.game.state.getMapSize();
        if (!mapSize) {
            console.error('Invalid map size');
            return;
        }

        this.gridContainer.innerHTML = '';

        const containerWidth = this.container.offsetWidth - 32;
        const containerHeight = this.container.offsetHeight - 32;

        const minDimension = Math.min(containerWidth, containerHeight);
        const cellSize = Math.max(32, Math.floor((minDimension - (mapSize + 1)) / mapSize));
        const gridSize = cellSize * mapSize + (mapSize + 1);

        this.configureGridContainer(cellSize, mapSize, gridSize);
        this.createMapCells(cellSize, mapSize);
        this.configureOverlay(gridSize);
    }

    configureGridContainer(cellSize, mapSize, gridSize) {
        this.gridContainer.style.display = 'grid';
        this.gridContainer.style.width = `${gridSize}px`;
        this.gridContainer.style.height = `${gridSize}px`;
        this.gridContainer.style.gap = '1px';
        this.gridContainer.style.padding = '1px';
        this.gridContainer.style.gridTemplateColumns = `repeat(${mapSize}, ${cellSize}px)`;
        this.gridContainer.style.gridTemplateRows = `repeat(${mapSize}, ${cellSize}px)`;
        this.gridContainer.style.margin = '0 auto';
    }

    createMapCells(cellSize, mapSize) {
        for (let y = 0; y < mapSize; y++) {
            for (let x = 0; x < mapSize; x++) {
                const cell = this.createMapCell(x, y, cellSize);
                this.gridContainer.appendChild(cell);
            }
        }
    }

    createMapCell(x, y, cellSize) {
        const cell = document.createElement('div');
        cell.className = 'map-cell';
        cell.dataset.x = x;
        cell.dataset.y = y;
        cell.style.width = `${cellSize}px`;
        cell.style.height = `${cellSize}px`;

        const mapCell = this.game.state.getMapCell(x, y);
        if (mapCell && mapCell.terrain) {
            cell.classList.add(`terrain-${mapCell.terrain}`);
        } else {
            cell.classList.add('terrain-unknown');
        }

        return cell;
    }

    configureOverlay(gridSize) {
        if (this.mapOverlay) {
            this.mapOverlay.style.position = 'absolute';
            this.mapOverlay.style.top = '1px';
            this.mapOverlay.style.left = '1px';
            this.mapOverlay.style.width = `${gridSize - 2}px`;
            this.mapOverlay.style.height = `${gridSize - 2}px`;
            this.mapOverlay.style.pointerEvents = 'none';
            this.mapOverlay.style.zIndex = '10';
        }
    }

    handleMapClick(event) {
        if (event.button === 2) {
            event.preventDefault();
            const cell = event.target.closest('.map-cell');
            if (!cell) {
                console.log('No map cell clicked');
                return;
            }
            this.clickedCell = { 
                x: parseInt(cell.dataset.x), 
                y: parseInt(cell.dataset.y) 
            };
            return this.clickedCell;
        }
        return null;
    }

    handleMapHover(event) {
        const cell = event.target.closest('.map-cell');
        if (!cell) return;

        if (this.hoveredCell) {
            this.hoveredCell.classList.remove('hovered');
        }

        cell.classList.add('hovered');
        this.hoveredCell = cell;
    }

    getCellSize() {
        const cell = this.gridContainer.querySelector('.map-cell');
        return cell ? cell.offsetWidth : 32;
    }

    getClickedCell() {
        return this.clickedCell;
    }

    clearClickedCell() {
        this.clickedCell = null;
    }
} 