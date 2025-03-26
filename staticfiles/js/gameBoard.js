export class GameBoard {
    constructor(game) {
        this.game = game;
        this.container = document.getElementById('game-board');
        this.selectedUnit = null;
        this.selectedCell = null;
        this.actionMode = null; // 'move', 'attack', 'build'
        this.grid = [];
    }

    initialize(gameState) {
        this.gameState = gameState;
        this.createGrid();
        this.render();
        this.setupEventListeners();
    }

    update(gameState) {
        this.gameState = gameState;
        this.render();
    }

    createGrid() {
        const mapSize = this.gameState.map_size;
        this.container.style.gridTemplateColumns = `repeat(${mapSize}, 1fr)`;
        
        for (let y = 0; y < mapSize; y++) {
            this.grid[y] = [];
            for (let x = 0; x < mapSize; x++) {
                const cell = document.createElement('div');
                cell.className = 'aspect-square border border-gray-300 dark:border-gray-600 relative';
                cell.dataset.x = x;
                cell.dataset.y = y;
                this.grid[y][x] = cell;
                this.container.appendChild(cell);
            }
        }
    }

    render() {
        // Clear existing content
        for (let y = 0; y < this.gameState.map_size; y++) {
            for (let x = 0; x < this.gameState.map_size; x++) {
                const cell = this.grid[y][x];
                cell.innerHTML = '';
                cell.className = 'aspect-square border border-gray-300 dark:border-gray-600 relative';
                
                // Add terrain
                const terrain = this.gameState.map[y][x];
                cell.classList.add(`terrain-${terrain}`);
                
                // Add units
                const unit = this.getUnitAt(x, y);
                if (unit) {
                    this.renderUnit(cell, unit);
                }
                
                // Add buildings
                const building = this.getBuildingAt(x, y);
                if (building) {
                    this.renderBuilding(cell, building);
                }
                
                // Add selection highlight
                if (this.selectedCell && 
                    this.selectedCell.dataset.x === x.toString() && 
                    this.selectedCell.dataset.y === y.toString()) {
                    cell.classList.add('ring-2', 'ring-blue-500');
                }
            }
        }
    }

    renderUnit(cell, unit) {
        const unitDiv = document.createElement('div');
        unitDiv.className = `absolute inset-0 flex items-center justify-center unit-${unit.unit_type}`;
        
        // Add unit icon
        const icon = document.createElement('i');
        icon.className = this.getUnitIcon(unit.unit_type);
        unitDiv.appendChild(icon);
        
        // Add health bar
        const healthBar = document.createElement('div');
        healthBar.className = 'absolute bottom-0 left-0 right-0 h-1 bg-gray-200';
        const healthFill = document.createElement('div');
        healthFill.className = 'h-full bg-green-500';
        healthFill.style.width = `${(unit.health / 100) * 100}%`;
        healthBar.appendChild(healthFill);
        unitDiv.appendChild(healthBar);
        
        cell.appendChild(unitDiv);
    }

    renderBuilding(cell, building) {
        const buildingDiv = document.createElement('div');
        buildingDiv.className = `absolute inset-0 flex items-center justify-center building-${building.building_type}`;
        
        // Add building icon
        const icon = document.createElement('i');
        icon.className = this.getBuildingIcon(building.building_type);
        buildingDiv.appendChild(icon);
        
        // Add health bar
        const healthBar = document.createElement('div');
        healthBar.className = 'absolute bottom-0 left-0 right-0 h-1 bg-gray-200';
        const healthFill = document.createElement('div');
        healthFill.className = 'h-full bg-green-500';
        healthFill.style.width = `${(building.health / 300) * 100}%`;
        healthBar.appendChild(healthFill);
        buildingDiv.appendChild(healthBar);
        
        cell.appendChild(buildingDiv);
    }

    setupEventListeners() {
        this.container.addEventListener('click', (e) => {
            const cell = e.target.closest('[data-x][data-y]');
            if (!cell) return;
            
            const x = parseInt(cell.dataset.x);
            const y = parseInt(cell.dataset.y);
            
            this.handleCellClick(x, y);
        });
    }

    handleCellClick(x, y) {
        if (!this.actionMode) return;
        
        const unit = this.getUnitAt(x, y);
        const building = this.getBuildingAt(x, y);
        
        switch (this.actionMode) {
            case 'move':
                if (this.selectedUnit && this.isValidMove(x, y)) {
                    this.game.processTurn([{
                        type: 'move_unit',
                        unit_id: this.selectedUnit.id,
                        x: x,
                        y: y
                    }]);
                    this.clearSelection();
                }
                break;
                
            case 'attack':
                if (this.selectedUnit && this.isValidAttack(x, y)) {
                    this.game.processTurn([{
                        type: 'attack',
                        unit_id: this.selectedUnit.id,
                        target_x: x,
                        target_y: y
                    }]);
                    this.clearSelection();
                }
                break;
                
            case 'build':
                if (this.isValidBuildPosition(x, y)) {
                    this.game.processTurn([{
                        type: 'build',
                        building_type: this.selectedBuildingType,
                        x: x,
                        y: y
                    }]);
                    this.clearSelection();
                }
                break;
        }
    }

    selectUnit(unit) {
        this.selectedUnit = unit;
        this.actionMode = null;
        this.updateSelection();
    }

    selectCell(x, y) {
        this.selectedCell = this.grid[y][x];
        this.updateSelection();
    }

    clearSelection() {
        this.selectedUnit = null;
        this.selectedCell = null;
        this.actionMode = null;
        this.selectedBuildingType = null;
        this.render();
    }

    updateSelection() {
        this.render();
        if (this.selectedCell) {
            this.selectedCell.classList.add('ring-2', 'ring-blue-500');
        }
    }

    getUnitAt(x, y) {
        return this.gameState.units.find(u => u.x_position === x && u.y_position === y);
    }

    getBuildingAt(x, y) {
        return this.gameState.buildings.find(b => b.x_position === x && b.y_position === y);
    }

    isValidMove(x, y) {
        if (!this.selectedUnit) return false;
        
        const dx = Math.abs(x - this.selectedUnit.x_position);
        const dy = Math.abs(y - this.selectedUnit.y_position);
        const distance = dx + dy;
        
        return distance <= this.selectedUnit.movement_range &&
               !this.getUnitAt(x, y) &&
               !this.getBuildingAt(x, y);
    }

    isValidAttack(x, y) {
        if (!this.selectedUnit) return false;
        
        const target = this.getUnitAt(x, y) || this.getBuildingAt(x, y);
        if (!target) return false;
        
        const dx = Math.abs(x - this.selectedUnit.x_position);
        const dy = Math.abs(y - this.selectedUnit.y_position);
        const distance = dx + dy;
        
        return distance <= this.selectedUnit.attack_range &&
               target.player_id !== this.selectedUnit.player_id;
    }

    isValidBuildPosition(x, y) {
        return !this.getUnitAt(x, y) && !this.getBuildingAt(x, y);
    }

    getUnitIcon(unitType) {
        const icons = {
            'infantry': 'fas fa-user-shield',
            'archer': 'fas fa-bow-arrow',
            'cavalry': 'fas fa-horse',
            'siege': 'fas fa-catapult'
        };
        return icons[unitType] || 'fas fa-question';
    }

    getBuildingIcon(buildingType) {
        const icons = {
            'base': 'fas fa-home',
            'barracks': 'fas fa-fort',
            'farm': 'fas fa-wheat',
            'mine': 'fas fa-mountain'
        };
        return icons[buildingType] || 'fas fa-question';
    }
} 