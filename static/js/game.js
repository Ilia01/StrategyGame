import { ConstantsManager } from './managers/ConstantsManager.js';
import { WebSocketManager } from './managers/WebSocketManager.js';

export class Game {
  constructor(gameId, playerId) {
    this.gameId = gameId;
    this.playerId = playerId;
    this.gameState = null;
    this.selectedEntity = null;
    this.constants = new ConstantsManager();
    this.wsManager = new WebSocketManager(gameId, this.handleWebSocketMessage.bind(this));
    this.init();
  }

  async init() {
    try {
      await this.constants.initialize();
      this.wsManager.connect();
      
      // Initialize game UI
      this.setupBoard();
      this.setupEventListeners();
    } catch (error) {
      console.error('Failed to initialize game:', error);
    }
  }

  handleWebSocketMessage(data) {
    switch (data.type) {
      case 'game_state':
        this.updateGameState(data.state);
        break;
      case 'game_update':
        this.handleGameUpdate(data.update_type, data.data);
        break;
      case 'chat_message':
        this.handleChatMessage(data.username, data.message);
        break;
      case 'error':
        this.handleError(data.message);
        break;
    }
  }

  handleGameUpdate(updateType, data) {
    switch (updateType) {
      case 'move_unit':
        this.updateUnitPosition(data.unit);
        break;
      case 'attack':
        this.handleAttackResult(data.attacker, data.target);
        break;
      case 'build':
        this.addBuilding(data.building);
        break;
      case 'train_unit':
        this.addUnit(data.unit);
        break;
      case 'end_turn':
        this.handleTurnEnd(data.current_turn);
        break;
    }
  }

  updateUnitPosition(unit) {
    const unitElement = document.querySelector(`[data-id="${unit.id}"]`);
    if (unitElement) {
      unitElement.dataset.x = unit.x;
      unitElement.dataset.y = unit.y;
      this.renderBoard();
    }
  }

  handleAttackResult(attacker, target) {
    if (target && target.health <= 0) {
      const targetElement = document.querySelector(`[data-id="${target.id}"]`);
      if (targetElement) {
        targetElement.remove();
      }
    }
    this.renderBoard();
  }

  addBuilding(building) {
    this.gameState.buildings.push(building);
    this.renderBoard();
  }

  addUnit(unit) {
    this.gameState.units.push(unit);
    this.renderBoard();
  }

  handleTurnEnd(currentTurn) {
    this.gameState.current_turn = currentTurn;
    this.updateUI();
  }

  handleChatMessage(username, message) {
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
      const messageElement = document.createElement('div');
      messageElement.className = 'chat-message mb-2';
      messageElement.innerHTML = `
        <span class="font-bold text-blue-400">${username}:</span>
        <span class="ml-2">${message}</span>
      `;
      messagesContainer.appendChild(messageElement);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  handleError(message) {
    // Show error message to user
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message bg-red-500 text-white p-4 rounded-lg mb-4';
    errorElement.textContent = message;
    document.querySelector('.container').prepend(errorElement);
    setTimeout(() => errorElement.remove(), 5000);
  }

  setupBoard() {
    this.boardElement = document.getElementById('game-board');
    this.actionInfo = document.getElementById('action-info');
    this.endTurnBtn = document.getElementById('end-turn');
    this.renderBoard();
  }

  setupEventListeners() {
    // End Turn Button
    this.endTurnBtn.addEventListener('click', () => this.endTurn());

    // Action Buttons
    document.getElementById('move-unit')?.addEventListener('click', () => {
      this.setActionMode('move');
    });

    document.getElementById('attack')?.addEventListener('click', () => {
      this.setActionMode('attack');
    });

    document.getElementById('train-unit')?.addEventListener('click', () => {
      this.setActionMode('train');
    });

    document.getElementById('build')?.addEventListener('click', () => {
      this.setActionMode('build');
    });

    // Cancel Action Button
    document.getElementById('cancel-action')?.addEventListener('click', () => {
      this.cancelAction();
    });

    // Chat Input
    const messageInput = document.getElementById('message-input');
    const sendMessageBtn = document.getElementById('send-message');
    
    if (messageInput && sendMessageBtn) {
      const sendMessage = () => {
        const message = messageInput.value.trim();
        if (message) {
          this.wsManager.sendChatMessage(this.getCurrentUsername(), message);
          messageInput.value = '';
        }
      };

      sendMessageBtn.addEventListener('click', sendMessage);
      messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
      });
    }
  }

  setActionMode(mode) {
    this.actionMode = mode;
    document.getElementById('cancel-action').classList.remove('hidden');
    this.actionInfo.textContent = `Select ${mode === 'move' ? 'destination' : 'target'} for ${mode} action`;
    this.actionInfo.classList.remove('hidden');
  }

  cancelAction() {
    this.actionMode = null;
    this.selectedEntity = null;
    document.getElementById('cancel-action').classList.add('hidden');
    this.actionInfo.classList.add('hidden');
  }

  handleCellClick(x, y) {
    if (!this.isCurrentPlayer()) return;

    if (this.actionMode) {
      this.handleAction(x, y);
    } else {
      const entity = this.findEntityAt(x, y);
      if (entity && entity.player_id === this.playerId) {
        this.selectEntity(entity);
      }
    }
  }

  handleAction(x, y) {
    if (!this.selectedEntity) return;

    switch (this.actionMode) {
      case 'move':
        this.wsManager.sendGameAction('move_unit', {
          unit_id: this.selectedEntity.id,
          x: x,
          y: y
        });
        break;
      case 'attack':
        const target = this.findEntityAt(x, y);
        if (target && target.player_id !== this.playerId) {
          this.wsManager.sendGameAction('attack', {
            attacker_id: this.selectedEntity.id,
            target_id: target.id
          });
        }
        break;
      case 'build':
        this.wsManager.sendGameAction('build', {
          building_type: this.selectedBuildingType,
          x: x,
          y: y
        });
        break;
      case 'train':
        this.wsManager.sendGameAction('train_unit', {
          unit_type: this.selectedUnitType,
          x: x,
          y: y
        });
        break;
    }

    this.cancelAction();
  }

  selectEntity(entity) {
    this.selectedEntity = entity;
    this.updateEntityInfo(entity);
  }

  updateEntityInfo(entity) {
    const infoElement = entity.type === 'unit' ? 
      document.getElementById('unit-info') : 
      document.getElementById('building-info');

    if (infoElement) {
      const stats = entity.type === 'unit' ? 
        this.constants.getUnitStats(entity.unit_type) : 
        this.constants.getBuildingStats(entity.building_type);

      infoElement.innerHTML = `
        <div class="bg-gray-700 p-4 rounded-lg">
          <h4 class="font-bold text-lg mb-2">${stats?.display || 'Unknown'}</h4>
          <div class="grid grid-cols-2 gap-2">
            <div>Health: ${entity.health}</div>
            ${entity.type === 'unit' ? `
              <div>Attack: ${stats?.attack || 0}</div>
              <div>Defense: ${stats?.defense || 0}</div>
              <div>Movement: ${entity.movement_range}</div>
              <div>Attack Range: ${entity.attack_range}</div>
            ` : ''}
          </div>
        </div>
      `;
    }
  }

  endTurn() {
    this.wsManager.sendGameAction('end_turn', {});
  }

  getCurrentUsername() {
    const currentPlayer = this.gameState?.players.find(p => p.id === this.playerId);
    return currentPlayer?.username || 'Anonymous';
  }

  isCurrentPlayer() {
    return this.gameState?.current_player_id === this.playerId;
  }

  updateGameState(state) {
    this.gameState = state;
    this.renderBoard();
    this.updateUI();
  }

  renderBoard() {
    if (!this.gameState || !this.constants) return;

    this.boardElement.style.gridTemplateColumns = `repeat(${this.gameState.map_size}, 50px)`;
    this.boardElement.innerHTML = '';

    for (let y = 0; y < this.gameState.map_size; y++) {
      for (let x = 0; x < this.gameState.map_size; x++) {
        const cell = this.createCell(x, y);
        this.boardElement.appendChild(cell);
      }
    }
  }

  createCell(x, y) {
    const cell = document.createElement('div');
    cell.className = 'board-cell border border-gray-300';
    cell.dataset.x = x;
    cell.dataset.y = y;

    const terrain = this.gameState.map_data.terrain[y][x];
    const terrainInfo = this.constants.getTerrainInfo(terrain);
    cell.classList.add(this.getTerrainColorClass(terrain));

    const entity = this.findEntityAt(x, y);
    if (entity) {
      const entityElement = this.createEntityElement(entity);
      cell.appendChild(entityElement);
    }

    cell.addEventListener('click', () => this.handleCellClick(x, y));
    return cell;
  }

  getTerrainColorClass(terrainType) {
    switch (terrainType) {
      case 'plains': return 'bg-green-300';
      case 'forest': return 'bg-green-700';
      case 'mountain': return 'bg-gray-500';
      case 'water': return 'bg-blue-500';
      default: return 'bg-white';
    }
  }

  createEntityElement(entity) {
    const element = document.createElement('div');
    element.className = `entity ${entity.type} flex flex-col items-center justify-center`;
    element.dataset.id = entity.id;
    element.dataset.type = entity.type;
    element.dataset.playerId = entity.player_id;

    const stats = entity.type === 'unit' ? 
      this.constants.getUnitStats(entity.unit_type) : 
      this.constants.getBuildingStats(entity.building_type);

    element.innerHTML = `
      <div class="entity-icon text-xl font-bold">${stats?.display || '?'}</div>
      <div class="entity-stats flex flex-col items-center">
        <div class="health-bar bg-red-500 h-1 w-full" style="width: ${entity.health}%"></div>
        ${entity.type === 'unit' ? `
          <div class="stat attack text-sm text-red-700">${stats?.attack || 0}</div>
          <div class="stat defense text-sm text-blue-700">${stats?.defense || 0}</div>
        ` : ''}
      </div>
    `;

    return element;
  }

  findEntityAt(x, y) {
    const unit = this.gameState.units.find(u => u.x === x && u.y === y);
    if (unit) return { ...unit, type: 'unit' };

    const building = this.gameState.buildings.find(b => b.x === x && b.y === y);
    if (building) return { ...building, type: 'building' };

    return null;
  }

  updateUI() {
    document.getElementById('current-turn').textContent = this.gameState.current_turn;
    document.getElementById('current-player').textContent = 
      this.gameState.current_player_username || 'None';

    if (this.playerId) {
      const player = this.gameState.players.find(p => p.id === this.playerId);
      if (player) {
        document.getElementById('player-resources').textContent = player.resources;
      }
    }

    this.renderPlayerList();
  }

  renderPlayerList() {
    const playerList = document.getElementById('player-list');
    if (!playerList) return;

    playerList.innerHTML = this.gameState.players.map(player => `
      <div class="player-item flex items-center justify-between p-2 bg-gray-700 rounded">
        <span class="font-medium">${player.username}</span>
        <span class="text-sm text-gray-400">
          ${player.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>
    `).join('');
  }
}
