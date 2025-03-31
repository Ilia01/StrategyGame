import { MapManager } from './MapManager.js';
import { EntityManager } from './EntityManager.js';
import { ContextMenuManager } from './ContextMenuManager.js';
import { ModalManager } from './ModalManager.js';

export class UIManager {
    constructor(game) {
        this.game = game;
        this.container = document.getElementById('game-board');
        if (!this.container) {
            console.error('Game board container not found');
            return;
        }

        // Initialize managers
        this.mapManager = new MapManager(game);
        this.entityManager = new EntityManager(game, this.mapManager);
        this.contextMenuManager = new ContextMenuManager(game, this.entityManager);
        this.modalManager = new ModalManager(game);

        // Initialize state
        this.chatMessages = [];
        this.maxChatMessages = 50;
        this.currentAction = null;

        // Get essential buttons
        this.endTurnButton = document.getElementById('end-turn-btn');
        this.cancelActionButton = document.getElementById('cancel-action-btn');

        // Bind event handlers
        this.bindEvents();
    }

    bindEvents() {
        // Map events
        this.container.addEventListener('click', this.handleMapClick.bind(this));
        this.container.addEventListener('mousemove', this.handleMapHover.bind(this));
        this.container.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            this.handleMapClick(e);
        });

        // End turn and cancel action buttons
        this.endTurnButton.addEventListener('click', () => this.game.endTurn());
        this.cancelActionButton.addEventListener('click', () => this.cancelAction());

        // Chat events
        const chatButton = document.getElementById('send-chat-btn');
        const chatInput = document.getElementById('chat-input');
        chatButton.addEventListener('click', () => this.handleChatSend());
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleChatSend();
        });

        // Update turn and player info
        document.getElementById('current-turn').textContent = this.game.state.currentTurn;
        document.getElementById('current-player').textContent = this.game.state.getPlayer(this.game.state.currentPlayer)?.name || 'Unknown';
    }

    setAction(action) {
        this.currentAction = action;
        this.updateActionButtons();
    }

    cancelAction() {
        this.currentAction = null;
        this.entityManager.clearSelection();
        this.updateActionButtons();
        this.render();
    }

    updateActionButtons() {
        const isCurrentPlayer = this.game.state.isCurrentPlayer(this.game.state.currentPlayer);
        this.endTurnButton.disabled = !isCurrentPlayer;
        this.cancelActionButton.classList.toggle('hidden', !this.currentAction);
    }

    render() {
        this.mapManager.renderMap();
        this.entityManager.renderEntities();
        this.renderResources();
        this.renderInfo();
        this.renderChat();
        this.updateActionButtons();
    }

    renderResources() {
        const resources = this.game.state.resources;
        document.getElementById('player-resources').textContent = resources.gold;
    }

    renderInfo() {
        const info = this.entityManager.getSelectedInfo();
        document.getElementById('selection-info').innerHTML = info ? this.formatSelectedInfo(info) : 'No unit or building selected';
    }

    formatSelectedInfo(info) {
        if (info.type === 'unit') {
            return `
                <div class="unit-details">
                    <h3>${info.info.type}</h3>
                    <p>Health: ${info.info.health}</p>
                    <p>Movement: ${info.info.movement}</p>
                    <p>Attack: ${info.info.attack}</p>
                    <p>Defense: ${info.info.defense}</p>
                </div>
            `;
        }
        if (info.type === 'building') {
            return `
                <div class="building-details">
                    <h3>${info.info.type}</h3>
                    <p>Health: ${info.info.health}</p>
                    ${info.info.production ? `
                        <p>Production: ${info.info.production}</p>
                    ` : ''}
                </div>
            `;
        }
        return null;
    }

    renderChat() {
        const messagesContainer = document.getElementById('chat-messages');
        messagesContainer.innerHTML = this.chatMessages
            .map(msg => `<div class="chat-message">${msg}</div>`)
            .join('');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    handleMapClick(event) {
        if (event.button === 2) {
            this.contextMenuManager.showContextMenu(event);
        }
    }

    handleMapHover(event) {
        this.mapManager.handleMapHover(event);
    }

    handleChatSend() {
        const message = document.getElementById('chat-input').value.trim();
        if (message) {
            this.game.chatClient.sendMessage(message);
        }
    }

    addChatMessage(message) {
        this.chatMessages.push(message);
        if (this.chatMessages.length > this.maxChatMessages) {
            this.chatMessages.shift();
        }
        this.renderChat();
    }

    showError(message) {
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        this.container.appendChild(errorElement);

        setTimeout(() => {
            errorElement.remove();
        }, 3000);
    }

    // Modal access methods for other managers
    showBuildingModal(x, y) {
        this.modalManager.showBuildingModal(x, y);
    }

    showTrainingModal() {
        this.modalManager.showTrainingModal();
    }
}