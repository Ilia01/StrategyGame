export class ActionPanel {
    constructor(game) {
        this.game = game;
        this.container = document.getElementById('action-panel');
        this.selectedUnit = null;
        this.selectedBuilding = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Unit action buttons
        this.container.querySelector('#move-unit').addEventListener('click', () => {
            if (this.selectedUnit) {
                this.game.gameBoard.actionMode = 'move';
                this.updateActionButtons();
            }
        });

        this.container.querySelector('#attack').addEventListener('click', () => {
            if (this.selectedUnit) {
                this.game.gameBoard.actionMode = 'attack';
                this.updateActionButtons();
            }
        });

        // Building action buttons
        this.container.querySelector('#train-unit').addEventListener('click', () => {
            if (this.selectedBuilding && this.selectedBuilding.building_type === 'barracks') {
                this.showUnitTrainingModal();
            }
        });

        // Cancel action button
        this.container.querySelector('#cancel-action').addEventListener('click', () => {
            this.game.gameBoard.clearSelection();
            this.updateActionButtons();
        });

        // End turn button
        this.container.querySelector('#end-turn').addEventListener('click', () => {
            this.game.processTurn([]);
        });
    }

    selectUnit(unit) {
        this.selectedUnit = unit;
        this.selectedBuilding = null;
        this.updateActionButtons();
        this.updateUnitInfo();
    }

    selectBuilding(building) {
        this.selectedBuilding = building;
        this.selectedUnit = null;
        this.updateActionButtons();
        this.updateBuildingInfo();
    }

    updateActionButtons() {
        const moveButton = this.container.querySelector('#move-unit');
        const attackButton = this.container.querySelector('#attack');
        const trainButton = this.container.querySelector('#train-unit');
        const cancelButton = this.container.querySelector('#cancel-action');
        const endTurnButton = this.container.querySelector('#end-turn');

        // Reset all buttons
        [moveButton, attackButton, trainButton, cancelButton, endTurnButton].forEach(button => {
            button.disabled = true;
            button.classList.remove('bg-blue-500', 'hover:bg-blue-600');
            button.classList.add('bg-gray-500', 'cursor-not-allowed');
        });

        // Enable relevant buttons based on selection
        if (this.selectedUnit) {
            moveButton.disabled = false;
            moveButton.classList.remove('bg-gray-500', 'cursor-not-allowed');
            moveButton.classList.add('bg-blue-500', 'hover:bg-blue-600');

            attackButton.disabled = false;
            attackButton.classList.remove('bg-gray-500', 'cursor-not-allowed');
            attackButton.classList.add('bg-blue-500', 'hover:bg-blue-600');
        } else if (this.selectedBuilding) {
            if (this.selectedBuilding.building_type === 'barracks') {
                trainButton.disabled = false;
                trainButton.classList.remove('bg-gray-500', 'cursor-not-allowed');
                trainButton.classList.add('bg-blue-500', 'hover:bg-blue-600');
            }
        }

        // Always enable end turn button
        endTurnButton.disabled = false;
        endTurnButton.classList.remove('bg-gray-500', 'cursor-not-allowed');
        endTurnButton.classList.add('bg-green-500', 'hover:bg-green-600');

        // Show/hide cancel button based on action mode
        if (this.game.gameBoard.actionMode) {
            cancelButton.disabled = false;
            cancelButton.classList.remove('bg-gray-500', 'cursor-not-allowed');
            cancelButton.classList.add('bg-red-500', 'hover:bg-red-600');
        }
    }

    updateUnitInfo() {
        if (!this.selectedUnit) {
            this.container.querySelector('#unit-info').innerHTML = '';
            return;
        }

        const unitInfo = this.container.querySelector('#unit-info');
        unitInfo.innerHTML = `
            <div class="p-4 bg-gray-800 rounded-lg">
                <h3 class="text-lg font-bold mb-2">${this.selectedUnit.unit_type}</h3>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span>Health:</span>
                        <span>${this.selectedUnit.health}/100</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Attack:</span>
                        <span>${this.selectedUnit.attack_power}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Defense:</span>
                        <span>${this.selectedUnit.defense}</span>
                    </div>
                    <div class="flex justify-between">
                        <span>Movement:</span>
                        <span>${this.selectedUnit.movement_range}</span>
                    </div>
                </div>
            </div>
        `;
    }

    updateBuildingInfo() {
        if (!this.selectedBuilding) {
            this.container.querySelector('#building-info').innerHTML = '';
            return;
        }

        const buildingInfo = this.container.querySelector('#building-info');
        buildingInfo.innerHTML = `
            <div class="p-4 bg-gray-800 rounded-lg">
                <h3 class="text-lg font-bold mb-2">${this.selectedBuilding.building_type}</h3>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span>Health:</span>
                        <span>${this.selectedBuilding.health}/300</span>
                    </div>
                    ${this.selectedBuilding.building_type === 'barracks' ? `
                        <div class="flex justify-between">
                            <span>Training:</span>
                            <span>${this.selectedBuilding.training_progress || 0}%</span>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    showUnitTrainingModal() {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center';
        modal.innerHTML = `
            <div class="bg-gray-800 p-6 rounded-lg">
                <h3 class="text-xl font-bold mb-4">Train Unit</h3>
                <div class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <button class="unit-type-btn p-4 bg-gray-700 rounded hover:bg-gray-600" data-type="infantry">
                            <i class="fas fa-user-shield text-2xl mb-2"></i>
                            <div>Infantry</div>
                            <div class="text-sm text-gray-400">Cost: 100</div>
                        </button>
                        <button class="unit-type-btn p-4 bg-gray-700 rounded hover:bg-gray-600" data-type="archer">
                            <i class="fas fa-bow-arrow text-2xl mb-2"></i>
                            <div>Archer</div>
                            <div class="text-sm text-gray-400">Cost: 150</div>
                        </button>
                        <button class="unit-type-btn p-4 bg-gray-700 rounded hover:bg-gray-600" data-type="cavalry">
                            <i class="fas fa-horse text-2xl mb-2"></i>
                            <div>Cavalry</div>
                            <div class="text-sm text-gray-400">Cost: 200</div>
                        </button>
                        <button class="unit-type-btn p-4 bg-gray-700 rounded hover:bg-gray-600" data-type="siege">
                            <i class="fas fa-catapult text-2xl mb-2"></i>
                            <div>Siege</div>
                            <div class="text-sm text-gray-400">Cost: 300</div>
                        </button>
                    </div>
                    <button class="w-full p-2 bg-red-500 rounded hover:bg-red-600" id="cancel-training">
                        Cancel
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add event listeners
        modal.querySelectorAll('.unit-type-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const unitType = btn.dataset.type;
                this.game.processTurn([{
                    type: 'train_unit',
                    building_id: this.selectedBuilding.id,
                    unit_type: unitType
                }]);
                modal.remove();
            });
        });

        modal.querySelector('#cancel-training').addEventListener('click', () => {
            modal.remove();
        });
    }
} 