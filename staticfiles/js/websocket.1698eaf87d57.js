export class WebSocketManager {
    constructor(game) {
        this.game = game;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // 1 second
        this.isConnecting = false;
    }

    connect() {
        if (this.isConnecting) return;
        this.isConnecting = true;

        try {
            // Get WebSocket URL from Django template
            const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${wsProtocol}//${window.location.host}/ws/game/${this.game.gameId}/`;
            
            this.socket = new WebSocket(wsUrl);
            
            this.socket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnecting = false;
                this.reconnectAttempts = 0;
                this.updateConnectionStatus('connected');
                
                // Send initial message with player ID
                this.send({
                    type: 'player_join',
                    player_id: this.game.playerId
                });
            };
            
            this.socket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.game.onWebSocketMessage(message);
                } catch (error) {
                    console.error('Failed to parse WebSocket message:', error);
                }
            };
            
            this.socket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnecting = false;
                this.updateConnectionStatus('disconnected');
                
                // Attempt to reconnect if not max attempts
                if (this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.attemptReconnect();
                } else {
                    this.updateConnectionStatus('failed');
                    this.game.chatPanel.addMessage({
                        type: 'system_message',
                        content: 'Connection lost. Please refresh the page.'
                    });
                }
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.isConnecting = false;
                this.updateConnectionStatus('error');
            };
        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.isConnecting = false;
            this.updateConnectionStatus('error');
        }
    }

    attemptReconnect() {
        this.reconnectAttempts++;
        this.updateConnectionStatus('reconnecting');
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
    }

    send(message) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            return false;
        }

        try {
            this.socket.send(JSON.stringify(message));
            return true;
        } catch (error) {
            console.error('Failed to send WebSocket message:', error);
            return false;
        }
    }

    updateConnectionStatus(status) {
        const statusElement = document.getElementById('connection-status');
        if (!statusElement) return;

        // Remove all status classes
        statusElement.classList.remove(
            'bg-green-500',
            'bg-yellow-500',
            'bg-red-500',
            'bg-gray-500'
        );

        // Add appropriate status class and text
        switch (status) {
            case 'connected':
                statusElement.classList.add('bg-green-500');
                statusElement.textContent = 'Connected';
                break;
                
            case 'reconnecting':
                statusElement.classList.add('bg-yellow-500');
                statusElement.textContent = 'Reconnecting...';
                break;
                
            case 'disconnected':
            case 'error':
            case 'failed':
                statusElement.classList.add('bg-red-500');
                statusElement.textContent = status === 'failed' ? 'Connection Failed' : 'Disconnected';
                break;
                
            default:
                statusElement.classList.add('bg-gray-500');
                statusElement.textContent = 'Unknown';
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
            this.isConnecting = false;
            this.updateConnectionStatus('disconnected');
        }
    }
} 