import { GameBoard } from './gameBoard.js';
import { ActionPanel } from './actionPanel.js';
import { ChatPanel } from './chatPanel.js';
import { GameState } from './gameState.js';
import { WebSocketManager } from './websocket.js';

export class Game {
    constructor(gameId, playerId) {
        this.gameId = gameId;
        this.playerId = playerId;
        this.state = new GameState();
        this.websocket = new WebSocketManager(this);
        this.gameBoard = new GameBoard(this);
        this.actionPanel = new ActionPanel(this);
        this.chatPanel = new ChatPanel(this);
    }

    async initialize() {
        try {
            // Fetch initial game state
            const response = await fetch(`/api/games/${this.gameId}/state/`);
            if (!response.ok) {
                throw new Error('Failed to fetch game state');
            }
            const data = await response.json();
            
            // Update game state
            this.state.update(data);
            
            // Initialize components
            this.gameBoard.initialize(this.state);
            this.actionPanel.updateActionButtons();
            this.chatPanel.updatePlayerList(this.state.players);
            
            // Connect WebSocket
            this.websocket.connect();
            
            // Start game loop
            this.startGameLoop();
            
            // Add system message
            this.chatPanel.addMessage({
                type: 'system_message',
                content: 'Game initialized successfully'
            });
        } catch (error) {
            console.error('Failed to initialize game:', error);
            this.showError('Failed to initialize game. Please refresh the page.');
        }
    }

    startGameLoop() {
        // Update game state every 5 seconds
        setInterval(() => {
            this.updateGameState();
        }, 5000);
    }

    async updateGameState() {
        try {
            const response = await fetch(`/api/games/${this.gameId}/state/`);
            if (!response.ok) {
                throw new Error('Failed to fetch game state');
            }
            const data = await response.json();
            
            // Update game state
            this.state.update(data);
            
            // Update UI components
            this.gameBoard.update(this.state);
            this.actionPanel.updateActionButtons();
            this.chatPanel.updatePlayerList(this.state.players);
            
            // Check for game end
            if (this.state.isGameFinished()) {
                const winner = this.state.getWinner();
                this.chatPanel.addMessage({
                    type: 'game_event',
                    content: winner ? 
                        `Game Over! ${winner.name} wins!` : 
                        'Game Over! It\'s a draw!'
                });
            }
        } catch (error) {
            console.error('Failed to update game state:', error);
        }
    }

    async processTurn(actions) {
        try {
            const response = await fetch(`/api/games/${this.gameId}/take_turn/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ actions })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Failed to process turn');
            }

            const data = await response.json();
            
            // Update game state
            this.state.update(data);
            
            // Update UI components
            this.gameBoard.update(this.state);
            this.actionPanel.updateActionButtons();
            this.chatPanel.updatePlayerList(this.state.players);
            
            // Add turn completion message
            this.chatPanel.addMessage({
                type: 'game_event',
                content: 'Turn completed successfully'
            });
        } catch (error) {
            console.error('Failed to process turn:', error);
            this.showError(error.message || 'Failed to process turn');
        }
    }

    async getCombatStats(unitId) {
        try {
            const response = await fetch(`/api/games/${this.gameId}/combat_stats/${unitId}/`);
            if (!response.ok) {
                throw new Error('Failed to fetch combat stats');
            }
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch combat stats:', error);
            return null;
        }
    }

    onWebSocketMessage(message) {
        switch (message.type) {
            case 'game_state_update':
                this.state.update(message.data);
                this.gameBoard.update(this.state);
                this.actionPanel.updateActionButtons();
                this.chatPanel.updatePlayerList(this.state.players);
                break;
                
            case 'chat_message':
            case 'game_event':
            case 'combat_event':
            case 'system_message':
                this.chatPanel.addMessage(message);
                break;
                
            case 'player_joined':
                this.chatPanel.addMessage({
                    type: 'system_message',
                    content: `${message.player_name} has joined the game`
                });
                break;
                
            case 'player_left':
                this.chatPanel.addMessage({
                    type: 'system_message',
                    content: `${message.player_name} has left the game`
                });
                break;
                
            case 'turn_started':
                this.chatPanel.addMessage({
                    type: 'game_event',
                    content: `Turn ${message.turn_number} started - ${message.player_name}'s turn`
                });
                break;
        }
    }

    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-4 py-2 rounded shadow-lg';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Remove after 5 seconds
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
} 