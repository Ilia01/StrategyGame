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
    this.selectedEntity = null;
    this.container = document.getElementById("game-board");
    this.initializeBoard();
  }

  initializeBoard() {
    this.container.innerHTML = "";
    const { map_size, map_data } = this.gameState;

    for (let y = 0; y < map_size; y++) {
      const row = document.createElement("div");
      row.className = "board-row";

      for (let x = 0; x < map_size; x++) {
        const cell = this.createCell(x, y);
        row.appendChild(cell);
      }

      this.container.appendChild(row);
    }
  }

  createCell(x, y) {
    const cell = document.createElement("div");
    cell.className = "board-cell";
    cell.dataset.x = x;
    cell.dataset.y = y;

    // Apply fog of war
    if (!this.isVisible(x, y)) {
      cell.classList.add("fog-of-war");
      return cell;
    }

    // Set terrain
    const terrain = this.gameState.map_data.terrain[y][x];
    cell.classList.add(`terrain-${terrain}`);

    const entity = this.getEntityAt(x, y);
    if (entity) {
      const entityElement = this.createEntityElement(entity);
      cell.appendChild(entityElement);
    }

    cell.addEventListener("click", () => this.onCellClick(x, y));
    return cell;
  }

  isVisible(x, y) {
    if (!this.playerId) return true; // Spectator mode sees everything

    const viewRange = 3; // Visibility range
    const playerEntities = this.getAllPlayerEntities();

    return playerEntities.some((entity) => {
      const distance = Math.abs(entity.x - x) + Math.abs(entity.y - y);
      return distance <= viewRange;
    });
  }

  getAllPlayerEntities() {
    const entities = [];

    // Add units
    this.gameState.units
      .filter((unit) => unit.player_id === this.playerId)
      .forEach((unit) => entities.push(unit));

    // Add buildings
    this.gameState.buildings
      .filter((building) => building.player_id === this.playerId)
      .forEach((building) => entities.push(building));

    return entities;
  }

  showMovementRange(unit) {
    const range = unit.movement_range;

    this.container.querySelectorAll(".board-cell").forEach((cell) => {
      const x = parseInt(cell.dataset.x);
      const y = parseInt(cell.dataset.y);
      const distance = Math.abs(unit.x - x) + Math.abs(unit.y - y);

      if (distance <= range && this.isValidMove(unit, x, y)) {
        cell.classList.add("valid-move");
      }
    });
  }

  showAttackRange(unit) {
    const range = unit.attack_range;

    this.container.querySelectorAll(".board-cell").forEach((cell) => {
      const x = parseInt(cell.dataset.x);
      const y = parseInt(cell.dataset.y);
      const distance = Math.abs(unit.x - x) + Math.abs(unit.y - y);

      if (distance <= range && this.getEnemyAt(x, y)) {
        cell.classList.add("valid-attack");
      }
    });
  }

  isValidMove(unit, x, y) {
    const terrain = this.gameState.map_data.terrain[y][x];
    if (terrain === "water") return false;

    // Check if destination is occupied
    if (this.getEntityAt(x, y)) return false;

    return true;
  }

  getEntityAt(x, y) {
    const unit = this.gameState.units.find((u) => u.x === x && u.y === y);
    if (unit) return { ...unit, type: "unit" };

    const building = this.gameState.buildings.find(
      (b) => b.x === x && b.y === y
    );
    if (building) return { ...building, type: "building" };

    return null;
  }

  getEnemyAt(x, y) {
    const entity = this.getEntityAt(x, y);
    return entity && entity.player_id !== this.playerId ? entity : null;
  }

  clearHighlights() {
    this.container.querySelectorAll(".board-cell").forEach((cell) => {
      cell.classList.remove("valid-move", "valid-attack", "selected");
    });
  }

  selectEntity(entity) {
    this.selectedEntity = entity;
    this.clearHighlights();

    if (entity && entity.type === "unit") {
      const cell = this.container.querySelector(
        `[data-x="${entity.x}"][data-y="${entity.y}"]`
      );
      if (cell) cell.classList.add("selected");

      if (!entity.has_moved) this.showMovementRange(entity);
      if (!entity.has_attacked) this.showAttackRange(entity);
    }
  }
}
