import { ConstantsManager } from './managers/ConstantsManager.js';

export class Game {
  constructor(gameId, playerId) {
    this.gameId = gameId;
    this.playerId = playerId;
    this.gameState = null;
    this.selectedEntity = null;
    this.constants = new ConstantsManager();
    this.init();
  }

  async init() {
    try {
      await this.constants.initialize();
      
      this.setupWebSocket();
      
      // Initialize game UI
      this.setupBoard();
      this.setupEventListeners();
    } catch (error) {
      console.error('Failed to initialize game:', error);
    }
  }

  setupWebSocket() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.socket = new WebSocket(
      `${wsProtocol}//${window.location.host}/ws/game/${this.gameId}/`
    );

    this.socket.onopen = () => {
      document.getElementById('connection-status').innerHTML = `
        <i class="fas fa-plug text-green-500"></i>
        <span class="text-green-500">Connected</span>
      `;
      this.requestGameState();
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'game_state') {
        this.updateGameState(data.state);
      }
    };

    this.socket.onclose = () => {
      document.getElementById('connection-status').innerHTML = `
        <i class="fas fa-plug text-red-500"></i>
        <span class="text-red-500">Disconnected</span>
      `;
    };
  }

  setupBoard() {
    this.boardElement = document.getElementById('game-board');
    this.actionInfo = document.getElementById('action-info');
    this.endTurnBtn = document.getElementById('end-turn-btn');
  }

  setupEventListeners() {
    this.endTurnBtn.addEventListener('click', () => this.endTurn());

    // Build buttons
    document.getElementById('build-btn')?.addEventListener('click', () => {
      this.actionInfo.textContent = 'Select a location to build';
      this.actionInfo.classList.remove('hidden');
    });
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

    const stats = entity.type === 'unit' 
      ? this.constants.getUnitStats(entity.unit_type)
      : this.constants.getBuildingStats(entity.building_type);

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

  handleCellClick(x, y) {
    if (!this.isCurrentPlayer()) return;

    const entity = this.findEntityAt(x, y);
    
    if (entity && entity.player_id === parseInt(this.playerId)) {
      this.selectEntity(entity);
    } else if (this.selectedEntity) {
      this.handleAction(x, y);
    }
  }

  isCurrentPlayer() {
    return this.gameState?.current_player_id === parseInt(this.playerId);
  }

  updateUI() {
    document.getElementById('current-turn').textContent = this.gameState.current_turn;
    document.getElementById('current-player').textContent = 
      this.gameState.current_player_username || 'None';

    if (this.playerId) {
      const player = this.gameState.players.find(p => p.id === parseInt(this.playerId));
      if (player) {
        document.getElementById('player-resources').textContent = player.resources;
      }
    }

    this.renderPlayerList();
  }

  requestGameState() {
    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify({ type: 'request_game_state' }));
    }
  }

  endTurn() {
    fetch(`/api/games/${this.gameId}/take_turn/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
      },
      body: JSON.stringify({ actions: [] })
    })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        alert(data.error);
      } else {
        this.requestGameState();
      }
    });
  }

  setupBuildOptions() {
    const buildMenu = document.getElementById('build-menu');
    if (!buildMenu) return;

    const buildings = this.constants.buildings;
    buildMenu.innerHTML = Object.values(buildings)
      .filter(building => building.name !== 'base')
      .map(building => `
        <button 
          class="build-option bg-gray-200 hover:bg-gray-300 text-sm font-medium py-1 px-2 rounded"
          data-building="${building.name}"
        >
          ${building.display} (${building.cost})
        </button>
      `).join('');
  }
}
