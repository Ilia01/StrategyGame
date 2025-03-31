export class ModalManager {
    constructor(game) {
        this.game = game;
        this.buildingModal = document.getElementById('building-modal');
        this.trainingModal = document.getElementById('training-modal');
        this.buildingCards = document.getElementById('building-cards');
        this.unitCards = document.getElementById('unit-cards');
        this.confirmBuildButton = document.getElementById('confirm-building');
        this.confirmTrainingButton = document.getElementById('confirm-training');
        this.selectedBuildingType = null;
        this.selectedUnitType = null;
        this.buildLocation = null;

        this.initializeEventListeners();
    }

    initializeEventListeners() {
        // Building modal events
        document.getElementById('close-building-modal').addEventListener('click', () => this.hideBuildingModal());
        document.getElementById('cancel-building').addEventListener('click', () => this.hideBuildingModal());
        this.confirmBuildButton.addEventListener('click', () => this.confirmBuildingSelection());

        // Training modal events
        document.getElementById('close-training-modal').addEventListener('click', () => this.hideTrainingModal());
        document.getElementById('cancel-training').addEventListener('click', () => this.hideTrainingModal());
        this.confirmTrainingButton.addEventListener('click', () => this.confirmUnitTraining());
    }

    showBuildingModal(x, y) {
        console.log('Showing building modal at:', { x, y });
        this.buildLocation = { x, y };
        this.renderBuildingCards();
        this.buildingModal.classList.add('active');
    }

    hideBuildingModal() {
        this.buildingModal.classList.remove('active');
        this.confirmBuildButton.disabled = true;
        this.selectedBuildingType = null;
        this.buildLocation = null;
    }

    showTrainingModal() {
        this.trainingModal.classList.add('active');
        this.renderUnitCards();
    }

    hideTrainingModal() {
        this.trainingModal.classList.remove('active');
        this.selectedUnitType = null;
        this.confirmTrainingButton.disabled = true;
    }

    renderBuildingCards() {
        console.log('Rendering building cards');
        const buildings = this.game.gameConstants?.building_types;
        if (!buildings) {
            console.error('Building types not available');
            return;
        }

        this.buildingCards.innerHTML = '';

        Object.values(buildings).forEach(building => {
            const card = this.createBuildingCard(building);
            this.buildingCards.appendChild(card);
        });
    }

    createBuildingCard(building) {
        const card = document.createElement('div');
        card.className = 'action-card';
        card.dataset.buildingType = building.name;

        card.innerHTML = `
            <div class="action-card-header">
                <div class="action-card-title">${building.display}</div>
                <div class="action-card-cost">
                    <i class="fas fa-coins mr-1"></i>
                    ${building.cost}
                </div>
            </div>
            <div class="action-card-stats">
                <div>Health: ${building.health}</div>
                <div>Production: ${building.resource_production}/turn</div>
            </div>
        `;

        card.addEventListener('click', () => {
            console.log('Building card clicked:', building.name);
            this.selectBuildingType(building.name);
        });

        return card;
    }

    renderUnitCards() {
        const units = this.game.getUnitTypes();
        this.unitCards.innerHTML = '';

        units.forEach(unit => {
            const card = this.createUnitCard(unit);
            this.unitCards.appendChild(card);
        });
    }

    createUnitCard(unit) {
        const card = document.createElement('div');
        card.className = 'action-card';
        card.dataset.unitType = unit.name;

        card.innerHTML = `
            <div class="action-card-header">
                <div class="action-card-title">${unit.display}</div>
                <div class="action-card-cost">
                    <i class="fas fa-coins mr-1"></i>
                    ${unit.cost}
                </div>
            </div>
            <div class="action-card-description">
                ${unit.description || 'No description available'}
            </div>
            <div class="action-card-stats">
                <div>Health: ${unit.health}</div>
                <div>Attack: ${unit.attack}</div>
                <div>Defense: ${unit.defense}</div>
                <div>Range: ${unit.attack_range}</div>
            </div>
        `;

        card.addEventListener('click', () => this.selectUnitType(unit.name));
        return card;
    }

    selectBuildingType(buildingType) {
        console.log('Selecting building type:', buildingType);
        this.selectedBuildingType = buildingType;
        this.confirmBuildButton.disabled = false;

        this.buildingCards.querySelectorAll('.action-card').forEach(card => {
            card.classList.toggle('selected', card.dataset.buildingType === buildingType);
        });

        const event = new CustomEvent('buildingSelected', {
            detail: { buildingType }
        });
        this.buildingModal.dispatchEvent(event);
    }

    selectUnitType(unitType) {
        this.selectedUnitType = unitType;
        this.confirmTrainingButton.disabled = false;

        this.unitCards.querySelectorAll('.action-card').forEach(card => {
            card.classList.toggle('selected', card.dataset.unitType === unitType);
        });
    }

    confirmBuildingSelection() {
        console.log('Confirming building selection:', this.selectedBuildingType);
        if (!this.selectedBuildingType || !this.buildLocation) {
            this.game.uiManager.showError('Please select a building type');
            return;
        }

        this.game.buildStructure(
            this.selectedBuildingType,
            this.buildLocation.x,
            this.buildLocation.y
        );

        this.hideBuildingModal();
    }

    confirmUnitTraining() {
        if (!this.selectedUnitType || !this.game.entityManager.getSelectedBuilding()) {
            return;
        }

        this.game.trainUnit(
            this.game.entityManager.getSelectedBuilding().id,
            this.selectedUnitType
        );
        this.hideTrainingModal();
    }
} 