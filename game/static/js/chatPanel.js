export class ChatPanel {
    constructor(game) {
        this.game = game;
        this.container = document.getElementById('chat-panel');
        this.messages = [];
        this.setupEventListeners();
    }

    setupEventListeners() {
        const sendButton = this.container.querySelector('#send-message');
        const messageInput = this.container.querySelector('#message-input');

        sendButton.addEventListener('click', () => {
            this.sendMessage(messageInput.value);
            messageInput.value = '';
        });

        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage(messageInput.value);
                messageInput.value = '';
            }
        });
    }

    sendMessage(content) {
        if (!content.trim()) return;

        const message = {
            type: 'chat_message',
            content: content,
            timestamp: new Date().toISOString()
        };

        this.game.websocket.send(message);
    }

    addMessage(message) {
        this.messages.push(message);
        this.renderMessages();
    }

    renderMessages() {
        const messagesContainer = this.container.querySelector('#messages');
        messagesContainer.innerHTML = '';

        this.messages.forEach(message => {
            const messageElement = document.createElement('div');
            messageElement.className = 'p-2 mb-2 rounded';

            // Different styles for different message types
            switch (message.type) {
                case 'chat_message':
                    messageElement.classList.add('bg-gray-700');
                    messageElement.innerHTML = `
                        <div class="flex items-center mb-1">
                            <span class="font-bold text-blue-400">${message.player_name}</span>
                            <span class="text-gray-400 text-sm ml-2">${this.formatTimestamp(message.timestamp)}</span>
                        </div>
                        <div class="text-gray-200">${message.content}</div>
                    `;
                    break;

                case 'game_event':
                    messageElement.classList.add('bg-gray-800', 'text-yellow-400');
                    messageElement.innerHTML = `
                        <div class="flex items-center">
                            <i class="fas fa-info-circle mr-2"></i>
                            <span>${message.content}</span>
                        </div>
                    `;
                    break;

                case 'combat_event':
                    messageElement.classList.add('bg-gray-800', 'text-red-400');
                    messageElement.innerHTML = `
                        <div class="flex items-center">
                            <i class="fas fa-skull-crossbones mr-2"></i>
                            <span>${message.content}</span>
                        </div>
                    `;
                    break;

                case 'system_message':
                    messageElement.classList.add('bg-gray-800', 'text-green-400');
                    messageElement.innerHTML = `
                        <div class="flex items-center">
                            <i class="fas fa-cog mr-2"></i>
                            <span>${message.content}</span>
                        </div>
                    `;
                    break;
            }

            messagesContainer.appendChild(messageElement);
        });

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    clearMessages() {
        this.messages = [];
        this.renderMessages();
    }

    updatePlayerList(players) {
        const playerList = this.container.querySelector('#player-list');
        playerList.innerHTML = '';

        players.forEach(player => {
            const playerElement = document.createElement('div');
            playerElement.className = 'p-2 mb-1 rounded bg-gray-700 flex items-center justify-between';
            
            const playerInfo = document.createElement('div');
            playerInfo.className = 'flex items-center';
            
            // Add player color indicator
            const colorIndicator = document.createElement('div');
            colorIndicator.className = 'w-3 h-3 rounded-full mr-2';
            colorIndicator.style.backgroundColor = player.color;
            playerInfo.appendChild(colorIndicator);
            
            // Add player name
            const nameSpan = document.createElement('span');
            nameSpan.textContent = player.name;
            playerInfo.appendChild(nameSpan);
            
            playerElement.appendChild(playerInfo);
            
            // Add player status
            const statusSpan = document.createElement('span');
            statusSpan.className = 'text-sm text-gray-400';
            statusSpan.textContent = player.is_current_turn ? 'Current Turn' : '';
            playerElement.appendChild(statusSpan);
            
            playerList.appendChild(playerElement);
        });
    }
} 