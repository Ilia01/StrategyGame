import gameApi from './api/gameApi.js';
import chatClient from './api/chatClient.js';
import { GameState } from './state/GameState.js';
import { UIManager } from './managers/UIManager.js';

export class Game {
    constructor(gameId, container) {
        this.gameId = gameId;
        this.container = container;
        this.state = new GameState();
        this.uiManager = new UIManager(this);
        this.chatClient = chatClient;
        this.gameConstants = null;
        this.isInitialized = false;
        this.buildingTypes = null;
        this.unitTypes = null;

        this.init();
    }

    async init() {
        try {
            this.gameConstants = await gameApi.getGameConstants();
            this.isInitialized = true;

            this.chatClient.connect(this.gameId);
            this.chatClient.onMessage(this.handleChatMessage.bind(this));

            this.startStatePolling();
            await this.pollGameState();
        } catch (error) {
            console.error('Failed to initialize game:', error);
            this.uiManager.showError('Failed to initialize game. Please refresh the page.');
        }
    }

    async startStatePolling() {
        await this.pollGameState();
        this.statePollingInterval = setInterval(() => this.pollGameState(), 5000);
    }

    async pollGameState() {
        try {
            const newState = await gameApi.getGameState(this.gameId);
            this.state.update(newState);
            this.uiManager.render();

            if (this.state.isGameFinished()) {
                this.handleGameEnd();
            }
        } catch (error) {
            console.error('Failed to poll game state:', error);
            this.uiManager.showError('Failed to update game state. Please refresh the page.');
        }
    }

    async moveUnit(x, y) {
        if (!this.isInitialized) return;
        try {
            await gameApi.moveUnit(this.gameId, this.uiManager.selectedUnit.id, x, y);
            await this.pollGameState();
        } catch (error) {
            this.uiManager.showError(error.message || 'Failed to move unit');
        }
    }

    async buildStructure(buildingType, x, y) {
        if (!this.isInitialized) {
            this.uiManager.showError('Game not initialized');
            return;
        }

        if (!buildingType) {
            this.uiManager.showError('Please select a building type');
            return;
        }

        if (!this.gameId) {
            this.uiManager.showError('Game ID not available');
            return;
        }

        try {
            console.log('Building structure:', { buildingType, x, y });
            
            // if (!this.isValidBuildLocation(x, y, buildingType)) {
            //     this.uiManager.showError('Cannot build here');
            //     return;
            // }

            console.log('Making build API call to:', `/api/games/${this.gameId}/build_structure/`);
            const response = await gameApi.buildStructure(this.gameId, buildingType, x, y);
            console.log('Build API response:', response);
            
            await this.pollGameState();
            
            this.uiManager.showError('Building placed successfully');
        } catch (error) {
            console.error('Build failed:', error.message);
            this.uiManager.showError(error.message || 'Failed to build structure');
        }
    }

    async trainUnit(buildingId, unitType) {
        if (!this.isInitialized) return;
        try {
            await gameApi.trainUnit(this.gameId, buildingId, unitType);
            await this.pollGameState();
        } catch (error) {
            this.uiManager.showError(error.message || 'Failed to train unit');
        }
    }

    async attackUnit(x, y) {
        if (!this.isInitialized) return;
        try {
            await gameApi.attackUnit(this.gameId, this.uiManager.selectedUnit.id, x, y);
            await this.pollGameState();
        } catch (error) {
            this.uiManager.showError(error.message || 'Failed to attack unit');
        }
    }

    async endTurn() {
        if (!this.isInitialized) return;
        try {
            await gameApi.takeTurn(this.gameId, []);
            await this.pollGameState();
        } catch (error) {
            this.uiManager.showError(error.message || 'Failed to end turn');
        }
    }

    handleChatMessage(data) {
        if (data.type === 'chat_message') {
            this.uiManager.addChatMessage(data);
        }
    }

    handleGameEnd() {
        // Stop polling
        clearInterval(this.statePollingInterval);

        // Show game end message
        const winner = this.state.getPlayer(this.state.winner);
        const message = winner ?
            `Game Over! ${winner.name} has won!` :
            'Game Over! It\'s a draw!';

        this.uiManager.showError(message);

        // Disable all game controls
        this.uiManager.updateActionButtons();
    }

    async fetchConstants() {
        try {
            const response = await fetch(`/api/games/constants/`);
            if (!response.ok) throw new Error('Failed to fetch game constants');

            const data = await response.json();
            this.buildingTypes = data.building_types;
            this.unitTypes = data.unit_types;

            console.log('Fetched game constants:', {
                buildingTypes: this.buildingTypes,
                unitTypes: this.unitTypes
            });
        } catch (error) {
            console.error('Error fetching game constants:', error);
            throw error;
        }
    }

    getBuildingTypes() {
        if (!this.buildingTypes) {
            console.error('Building types not initialized');
            return [];
        }
        return Object.values(this.buildingTypes);
    }

    getUnitTypes() {
        if (!this.unitTypes) {
            console.error('Unit types not initialized');
            return [];
        }
        return Object.values(this.unitTypes);
    }
}

