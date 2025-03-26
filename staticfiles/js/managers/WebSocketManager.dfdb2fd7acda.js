export class WebSocketManager {
    constructor(gameId, onMessage) {
        this.gameId = gameId;
        this.onMessage = onMessage;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }

    connect() {
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.socket = new WebSocket(
            `${wsProtocol}//${window.location.host}/ws/game/${this.gameId}/`
        );

        this.socket.onopen = () => {
            this.reconnectAttempts = 0;
            this.updateConnectionStatus(true);
            this.requestGameState();
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.onMessage(data);
        };

        this.socket.onclose = () => {
            this.updateConnectionStatus(false);
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            this.updateConnectionStatus(false);
        };
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.innerHTML = `
                <i class="fas fa-plug ${connected ? 'text-green-500' : 'text-red-500'}"></i>
                <span class="${connected ? 'text-green-500' : 'text-red-500'}">
                    ${connected ? 'Connected' : 'Disconnected'}
                </span>
            `;
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                this.connect();
            }, this.reconnectDelay * this.reconnectAttempts);
        } else {
            console.error('Max reconnection attempts reached');
            this.updateConnectionStatus(false);
        }
    }

    requestGameState() {
        this.send({
            type: 'request_game_state'
        });
    }

    sendChatMessage(username, message) {
        this.send({
            type: 'chat_message',
            username: username,
            message: message
        });
    }

    sendGameAction(actionType, actionData) {
        this.send({
            type: 'game_action',
            action_type: actionType,
            action_data: actionData
        });
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.error('WebSocket is not connected');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
} 