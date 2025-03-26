/**
 * Turn-Based Strategy Game
 * Game board renderer
 */

import {
  calculateDistance,
  getTerrainMovementCost,
  getUnitTypeIcon,
  getBuildingTypeIcon,
} from "../utils/helpers.js";
import { UNIT_STATS } from "../utils/constants.js";

class GameCell extends HTMLElement {
  connectedCallback() {
    this.render();
  }

  render() {
    const { x, y, terrain } = this.dataset;
    this.className = `cell cell-${terrain}`;
  }
}

customElements.define("game-cell", GameCell);

export class GameBoard {
  constructor(gameState, playerId, onCellClick) {
    this.gameState = gameState;
    this.playerId = playerId;
    this.onCellClick = onCellClick;
    this.selectedCell = null;
    this.cellSize = 40;
    this.padding = 2;
    this.canvas = null;
    this.ctx = null;
    this.terrainPatterns = {};
    this.initializeBoard();
  }

  async initializeBoard() {
    const gameBoard = document.getElementById("game-board");
    if (!gameBoard) return;

    // Clear existing content
    gameBoard.innerHTML = "";

    // Create canvas
    this.canvas = document.createElement("canvas");
    this.canvas.style.width = "100%";
    this.canvas.style.height = "100%";
    this.canvas.style.display = "block";
    gameBoard.appendChild(this.canvas);

    // Get context
    this.ctx = this.canvas.getContext("2d");

    // Initialize terrain patterns
    await this.initializeTerrainPatterns();

    // Set canvas size based on game board size
    this.resizeCanvas();

    // Add event listeners
    this.canvas.addEventListener("click", (e) => this.handleClick(e));
    window.addEventListener("resize", () => this.resizeCanvas());

    // Initial render
    this.render();
  }

  async initializeTerrainPatterns() {
    const terrainTypes = ['plains', 'forest', 'mountain', 'water'];
    const patternSize = 20;
    const tempCanvas = document.createElement('canvas');
    tempCanvas.width = patternSize;
    tempCanvas.height = patternSize;
    const tempCtx = tempCanvas.getContext('2d');

    for (const terrain of terrainTypes) {
      switch (terrain) {
        case 'plains':
          // Light green pattern with subtle grass texture
          tempCtx.fillStyle = '#90be6d';
          tempCtx.fillRect(0, 0, patternSize, patternSize);
          tempCtx.strokeStyle = '#a3d082';
          tempCtx.lineWidth = 1;
          for (let i = 0; i < 8; i++) {
            const x = Math.random() * patternSize;
            const y = Math.random() * patternSize;
            tempCtx.beginPath();
            tempCtx.moveTo(x, y);
            tempCtx.lineTo(x + 2, y + 4);
            tempCtx.stroke();
          }
          break;

        case 'forest':
          // Dark green with tree-like shapes
          tempCtx.fillStyle = '#40916c';
          tempCtx.fillRect(0, 0, patternSize, patternSize);
          tempCtx.fillStyle = '#52b788';
          for (let i = 0; i < 3; i++) {
            const x = Math.random() * patternSize;
            const y = Math.random() * patternSize;
            tempCtx.beginPath();
            tempCtx.moveTo(x, y);
            tempCtx.lineTo(x + 4, y + 8);
            tempCtx.lineTo(x - 4, y + 8);
            tempCtx.fill();
          }
          break;

        case 'mountain':
          // Gray with triangle peaks
          tempCtx.fillStyle = '#6b705c';
          tempCtx.fillRect(0, 0, patternSize, patternSize);
          tempCtx.fillStyle = '#8b8c7a';
          tempCtx.beginPath();
          tempCtx.moveTo(patternSize/2, 2);
          tempCtx.lineTo(patternSize-2, patternSize-2);
          tempCtx.lineTo(2, patternSize-2);
          tempCtx.fill();
          break;

        case 'water':
          // Blue with wave patterns
          tempCtx.fillStyle = '#48cae4';
          tempCtx.fillRect(0, 0, patternSize, patternSize);
          tempCtx.strokeStyle = '#90e0ef';
          tempCtx.lineWidth = 1;
          for (let i = 0; i < patternSize; i += 4) {
            tempCtx.beginPath();
            tempCtx.moveTo(i, patternSize/2 + Math.sin(i/4) * 2);
            tempCtx.lineTo(i + 2, patternSize/2 + Math.cos(i/4) * 2);
            tempCtx.stroke();
          }
          break;
      }

      this.terrainPatterns[terrain] = this.ctx.createPattern(tempCanvas, 'repeat');
    }
  }

  resizeCanvas() {
    const gameBoard = document.getElementById("game-board");
    if (!gameBoard) return;

    const rect = gameBoard.getBoundingClientRect();
    this.canvas.width = rect.width;
    this.canvas.height = rect.height;
    this.render();
  }

  render() {
    if (!this.ctx || !this.gameState || !this.gameState.map_data?.terrain) return;

    const { width, height } = this.canvas;
    this.ctx.clearRect(0, 0, width, height);

    // Calculate grid dimensions
    const gridSize = this.gameState.map_size;
    const cellSize = Math.min(
      (width - (gridSize + 1) * this.padding) / gridSize,
      (height - (gridSize + 1) * this.padding) / gridSize
    );

    // Center the grid
    const startX = (width - (gridSize * (cellSize + this.padding) - this.padding)) / 2;
    const startY = (height - (gridSize * (cellSize + this.padding) - this.padding)) / 2;

    // Draw cells
    for (let y = 0; y < gridSize; y++) {
      for (let x = 0; x < gridSize; x++) {
        const cellX = startX + x * (cellSize + this.padding);
        const cellY = startY + y * (cellSize + this.padding);
        const cell = this.getCellData(x, y);

        // Draw terrain
        if (cell && cell.terrain_type) {
          const terrainType = cell.terrain_type.toLowerCase();
          if (this.terrainPatterns[terrainType]) {
            this.ctx.fillStyle = this.terrainPatterns[terrainType];
          } else {
            this.ctx.fillStyle = this.getTerrainColor(terrainType);
          }
        } else {
          this.ctx.fillStyle = "#2d3748"; // Default dark color
        }
        this.ctx.fillRect(cellX, cellY, cellSize, cellSize);

        // Draw cell border
        this.ctx.strokeStyle = "#4a5568";
        this.ctx.lineWidth = 1;
        this.ctx.strokeRect(cellX, cellY, cellSize, cellSize);

        // Draw cell content (units, buildings, resources)
        if (cell) {
          this.drawCellContent(cell, cellX, cellY, cellSize);
        }

        // Highlight selected cell
        if (this.selectedCell && this.selectedCell.x === x && this.selectedCell.y === y) {
          this.ctx.strokeStyle = "#4299e1";
          this.ctx.lineWidth = 2;
          this.ctx.strokeRect(cellX, cellY, cellSize, cellSize);
        }
      }
    }
  }

  getCellData(x, y) {
    if (!this.gameState || !this.gameState.map_data || !this.gameState.map_data.terrain) {
      return null;
    }

    const terrain = this.gameState.map_data.terrain[y]?.[x];
    if (!terrain) return null;

    return {
      terrain_type: terrain,
      unit: this.gameState.units.find(u => u.x === x && u.y === y),
      building: this.gameState.buildings.find(b => b.x === x && b.y === y),
      resources: 0, // We'll need to add this to the map data if needed
      owner_id: null // We'll need to add this to the map data if needed
    };
  }

  getTerrainColor(terrainType) {
    switch (terrainType) {
      case 'plains':
        return '#90be6d';
      case 'forest':
        return '#40916c';
      case 'mountain':
        return '#6b705c';
      case 'water':
        return '#48cae4';
      default:
        return '#2d3748';
    }
  }

  drawCellContent(cell, x, y, size) {
    if (!cell) return;

    // Draw unit
    if (cell.unit) {
      // Draw unit shadow
      this.ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
      this.ctx.beginPath();
      this.ctx.ellipse(x + size/2, y + size * 0.8, size/3, size/6, 0, 0, Math.PI * 2);
      this.ctx.fill();

      // Draw unit body
      this.ctx.fillStyle = cell.unit.owner_id === this.playerId ? "#4299e1" : "#e53e3e";
      this.ctx.beginPath();
      this.ctx.arc(x + size/2, y + size/2, size/3, 0, Math.PI * 2);
      this.ctx.fill();

      // Add highlight
      this.ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
      this.ctx.beginPath();
      this.ctx.arc(x + size/2 - size/6, y + size/2 - size/6, size/6, 0, Math.PI * 2);
      this.ctx.fill();

      // Draw unit health
      if (cell.unit.health) {
        // Health bar background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fillRect(x + size/4, y + size * 0.8, size/2, 4);

        // Health bar
        const healthPercent = cell.unit.health / 100;
        this.ctx.fillStyle = healthPercent > 0.6 ? '#22c55e' : healthPercent > 0.3 ? '#eab308' : '#ef4444';
        this.ctx.fillRect(x + size/4, y + size * 0.8, size/2 * healthPercent, 4);
      }
    }

    // Draw building
    if (cell.building) {
      // Draw building shadow
      this.ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
      this.ctx.fillRect(x + size/4 + 2, y + size/4 + 2, size/2, size/2);

      // Draw building body
      this.ctx.fillStyle = cell.building.owner_id === this.playerId ? "#48bb78" : "#c53030";
      this.ctx.fillRect(x + size/4, y + size/4, size/2, size/2);

      // Add building details
      this.ctx.strokeStyle = cell.building.owner_id === this.playerId ? "#22c55e" : "#b91c1c";
      this.ctx.lineWidth = 2;
      this.ctx.strokeRect(x + size/4, y + size/4, size/2, size/2);

      // Draw building health if applicable
      if (cell.building.health) {
        // Health bar background
        this.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        this.ctx.fillRect(x + size/4, y + size * 0.8, size/2, 4);

        // Health bar
        const healthPercent = cell.building.health / 100;
        this.ctx.fillStyle = healthPercent > 0.6 ? '#22c55e' : healthPercent > 0.3 ? '#eab308' : '#ef4444';
        this.ctx.fillRect(x + size/4, y + size * 0.8, size/2 * healthPercent, 4);
      }
    }

    // Draw resources
    if (cell.resources > 0) {
      // Draw resource icon (gold coin)
      this.ctx.fillStyle = '#fbbf24';
      this.ctx.beginPath();
      this.ctx.arc(x + size/2, y + size - size/4, size/6, 0, Math.PI * 2);
      this.ctx.fill();
      
      // Add shine to coin
      this.ctx.fillStyle = '#fcd34d';
      this.ctx.beginPath();
      this.ctx.arc(x + size/2 - size/12, y + size - size/4 - size/12, size/12, 0, Math.PI * 2);
      this.ctx.fill();

      // Draw resource amount
      this.ctx.fillStyle = '#000';
      this.ctx.font = `${size/3}px Arial`;
      this.ctx.textAlign = 'center';
      this.ctx.textBaseline = 'middle';
      this.ctx.fillText(cell.resources, x + size/2, y + size - size/4);
    }
  }

  handleClick(event) {
    const rect = this.canvas.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Calculate grid dimensions
    const gridSize = this.gameState.map_size;
    const cellSize = Math.min(
      (rect.width - (gridSize + 1) * this.padding) / gridSize,
      (rect.height - (gridSize + 1) * this.padding) / gridSize
    );

    // Center the grid
    const startX = (rect.width - (gridSize * (cellSize + this.padding) - this.padding)) / 2;
    const startY = (rect.height - (gridSize * (cellSize + this.padding) - this.padding)) / 2;

    // Calculate grid coordinates
    const gridX = Math.floor((x - startX) / (cellSize + this.padding));
    const gridY = Math.floor((y - startY) / (cellSize + this.padding));

    if (gridX >= 0 && gridX < gridSize && gridY >= 0 && gridY < gridSize) {
      this.selectedCell = { x: gridX, y: gridY };
      this.onCellClick(gridX, gridY);
      this.render();
    }
  }

  clearSelection() {
    this.selectedCell = null;
    this.render();
  }
}
