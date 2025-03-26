/**
 * Turn-Based Strategy Game
 * Game UI manager
 */

import { GameConnection } from "./GameConnection.js";
import { GameBoard } from "./GameBoard.js";
import { getCookie, getCSRFToken } from "../utils/helpers.js";

export class GameUI {
  constructor(gameId, playerId) {
    this.gameId = gameId;
    this.playerId = playerId;
    this.gameState = null;
    this.currentAction = null;
    this.pendingActions = [];
    this.gameBoard = null;

    this.connection = new GameConnection(gameId);
    this.setupConnectionCallbacks();

    this.setupEventHandlers();
  }

  setupConnectionCallbacks() {
    this.connection.setCallback("onGameState", (gameState) => {
      this.gameState = gameState;
      this.renderGameState();
    });

    this.connection.setCallback("onGameUpdate", (updateType, data) => {
      // Request updated game state
      this.connection.requestGameState();
    });

    this.connection.setCallback("onChatMessage", (username, message) => {
      this.addChatMessage(username, message);
    });

    this.connection.setCallback("onConnect", () => {
      const connectionStatus = document.getElementById("connection-status");
      connectionStatus.textContent = "Connected";
      connectionStatus.classList.remove("text-danger");
      connectionStatus.classList.add("text-success");
    });

    this.connection.setCallback("onDisconnect", () => {
      const connectionStatus = document.getElementById("connection-status");
      connectionStatus.textContent = "Disconnected";
      connectionStatus.classList.remove("text-success");
      connectionStatus.classList.add("text-danger");
    });
  }

  setupEventHandlers() {
    // End turn button
    document.getElementById("end-turn-btn").addEventListener("click", () => {
      this.submitTurn();
    });

    // Cancel action button
    document
      .getElementById("cancel-action-btn")
      .addEventListener("click", () => {
        this.cancelAction();
      });

    // Build buttons
    document.addEventListener("click", (e) => {
      if (e.target.classList.contains("build-btn")) {
        const buildingType = e.target.getAttribute("data-building-type");
        this.startBuildAction(buildingType);
      }
    });

    // Train buttons
    document.addEventListener("click", (e) => {
      if (e.target.classList.contains("train-btn")) {
        const unitType = e.target.getAttribute("data-unit-type");
        this.startTrainAction(unitType);
      }
    });

    // Chat send button
    document.getElementById("send-chat-btn").addEventListener("click", () => {
      this.sendChatMessage();
    });

    // Chat input enter key
    document.getElementById("chat-input").addEventListener("keypress", (e) => {
      if (e.which === 13) {
        this.sendChatMessage();
      }
    });
  }

  renderGameState() {
    if (!this.gameState) return;

    // Update turn and current player info
    const currentTurn = document.getElementById("current-turn");
    const currentPlayer = document.getElementById("current-player");
    if (currentTurn) currentTurn.textContent = this.gameState.current_turn;
    if (currentPlayer) currentPlayer.textContent = this.gameState.current_player_username || "None";

    // Update player resources if player
    if (this.playerId) {
      const currentPlayer = this.gameState.players.find(
        (p) => p.id === this.playerId
      );
      if (currentPlayer) {
        const playerResources = document.getElementById("player-resources");
        if (playerResources) {
          playerResources.textContent = currentPlayer.resources;
        }
      }
    }

    // Render game board
    if (!this.gameBoard) {
      this.gameBoard = new GameBoard(this.gameState, this.playerId, (x, y) =>
        this.handleCellClick(x, y)
      );
      this.gameBoard.initializeBoard();
    } else {
      this.gameBoard.gameState = this.gameState;
      this.gameBoard.initializeBoard();
    }

    // Render player list
    this.renderPlayerList();

    // Update action panel
    this.updateActionPanel();
  }

  renderPlayerList() {
    const playerList = document.getElementById("player-list");
    playerList.innerHTML = "";

    this.gameState.players.forEach((player) => {
      const isCurrentPlayer = player.id === this.gameState.current_player_id;
      const playerItem = document.createElement("li");
      playerItem.className = `list-group-item ${
        isCurrentPlayer ? "active" : ""
      }`;
      playerItem.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
          <span>
            <span class="badge bg-${this.getPlayerBadgeColor(
              player.player_number
            )}">${player.player_number}</span>
            ${player.username}
          </span>
          <span>Resources: ${player.resources}</span>
        </div>
      `;
      playerList.appendChild(playerItem);
    });
  }

  getPlayerBadgeColor(playerNumber) {
    const colors = ["danger", "primary", "success", "warning"];
    return colors[(playerNumber - 1) % colors.length];
  }

  updateActionPanel() {
    if (!this.playerId) return;

    const isMyTurn = this.gameState.current_player_id === this.playerId;
    const endTurnBtn = document.getElementById("end-turn-btn");
    if (endTurnBtn) {
      endTurnBtn.disabled = !isMyTurn;
    }

    const actionInfo = document.getElementById("action-info");
    const cancelActionBtn = document.getElementById("cancel-action-btn");

    if (this.currentAction) {
      if (actionInfo) {
        actionInfo.classList.remove("d-none");
        actionInfo.textContent = `Current action: ${this.currentAction.type}`;
      }
      if (cancelActionBtn) {
        cancelActionBtn.classList.remove("d-none");
      }
    } else {
      if (actionInfo) {
        actionInfo.classList.add("d-none");
      }
      if (cancelActionBtn) {
        cancelActionBtn.classList.add("d-none");
      }
    }
  }

  handleCellClick(x, y) {
    if (!this.gameState || this.gameState.current_player_id !== this.playerId) return;

    const cell = this.gameState.map_data[y][x];
    if (!cell) return;

    switch (this.currentAction?.type) {
      case "move":
        this.handleMoveAction(x, y);
        break;
      case "attack":
        this.handleAttackAction(x, y);
        break;
      case "build":
        this.handleBuildAction(x, y);
        break;
      case "train":
        this.handleTrainAction(x, y);
        break;
      default:
        this.handleSelection(x, y);
    }
  }

  handleSelection(x, y) {
    const cell = this.gameState.map_data[y][x];
    if (!cell) return;

    // Update selection info
    const selectionInfo = document.getElementById("selection-info");
    if (selectionInfo) {
      if (cell.unit) {
        selectionInfo.textContent = `Unit: ${cell.unit.type} (HP: ${cell.unit.health})`;
      } else if (cell.building) {
        selectionInfo.textContent = `Building: ${cell.building.type}`;
      } else {
        selectionInfo.textContent = `Empty cell (Resources: ${cell.resources || 0})`;
      }
    }

    // If it's our unit, show available actions
    if (cell.unit && cell.unit.owner_id === this.playerId) {
      this.showUnitActions(cell.unit);
    } else {
      this.hideUnitActions();
    }
  }

  showUnitActions(unit) {
    const moveBtn = document.getElementById("move-unit");
    const attackBtn = document.getElementById("attack");
    const buildBtn = document.getElementById("build");
    const trainBtn = document.getElementById("train-unit");

    if (moveBtn) moveBtn.disabled = unit.has_moved;
    if (attackBtn) attackBtn.disabled = unit.has_attacked;
    if (buildBtn) buildBtn.disabled = true;
    if (trainBtn) trainBtn.disabled = true;
  }

  hideUnitActions() {
    const moveBtn = document.getElementById("move-unit");
    const attackBtn = document.getElementById("attack");
    const buildBtn = document.getElementById("build");
    const trainBtn = document.getElementById("train-unit");

    if (moveBtn) moveBtn.disabled = true;
    if (attackBtn) attackBtn.disabled = true;
    if (buildBtn) buildBtn.disabled = true;
    if (trainBtn) trainBtn.disabled = true;
  }

  handleMoveAction(x, y) {
    if (!this.selectedUnit) return;

    const cell = this.gameState.map_data[y][x];
    if (!cell || cell.unit || cell.building) return;

    // Check if move is valid
    const distance = Math.abs(this.selectedUnit.x - x) + Math.abs(this.selectedUnit.y - y);
    if (distance > this.selectedUnit.movement_range) return;

    // Send move action
    this.socket.send(
      JSON.stringify({
        type: "move",
        unit_id: this.selectedUnit.id,
        x: x,
        y: y,
      })
    );

    this.cancelAction();
  }

  handleAttackAction(x, y) {
    if (!this.selectedUnit) return;

    const cell = this.gameState.map_data[y][x];
    if (!cell || !cell.unit || cell.unit.owner_id === this.playerId) return;

    // Check if attack is valid
    const distance = Math.abs(this.selectedUnit.x - x) + Math.abs(this.selectedUnit.y - y);
    if (distance > this.selectedUnit.attack_range) return;

    // Send attack action
    this.socket.send(
      JSON.stringify({
        type: "attack",
        unit_id: this.selectedUnit.id,
        target_id: cell.unit.id,
      })
    );

    this.cancelAction();
  }

  handleBuildAction(x, y) {
    if (!this.selectedUnit) return;

    const cell = this.gameState.map_data[y][x];
    if (!cell || cell.unit || cell.building) return;

    // Check if build is valid
    const distance = Math.abs(this.selectedUnit.x - x) + Math.abs(this.selectedUnit.y - y);
    if (distance > 1) return;

    // Send build action
    this.socket.send(
      JSON.stringify({
        type: "build",
        unit_id: this.selectedUnit.id,
        x: x,
        y: y,
        building_type: this.currentAction.buildingType,
      })
    );

    this.cancelAction();
  }

  handleTrainAction(x, y) {
    if (!this.selectedUnit) return;

    const cell = this.gameState.map_data[y][x];
    if (!cell || cell.unit || cell.building) return;

    // Check if train is valid
    const distance = Math.abs(this.selectedUnit.x - x) + Math.abs(this.selectedUnit.y - y);
    if (distance > 1) return;

    // Send train action
    this.socket.send(
      JSON.stringify({
        type: "train",
        unit_id: this.selectedUnit.id,
        x: x,
        y: y,
        unit_type: this.currentAction.unitType,
      })
    );

    this.cancelAction();
  }

  startBuildAction(buildingType) {
    this.currentAction = {
      type: "build",
      building_type: buildingType,
    };

    // Show valid build positions
    this.gameBoard.highlightValidBuildPositions();
    this.updateActionPanel();
  }

  startTrainAction(unitType) {
    const barracksId = parseInt(
      document.getElementById("train-options").getAttribute("data-barracks-id")
    );

    this.addAction({
      type: "train_unit",
      unit_type: unitType,
      barracks_id: barracksId,
    });

    this.cancelAction();
  }

  addAction(action) {
    this.pendingActions.push(action);
    document.getElementById("end-turn-btn").disabled = false;
  }

  cancelAction() {
    this.currentAction = null;
    const validElements = document.querySelectorAll(".valid-move, .valid-attack, .valid-build");
    validElements.forEach((el) => {
      el.classList.remove("valid-move", "valid-attack", "valid-build");
    });
    this.updateActionPanel();
  }

  submitTurn() {
    if (this.pendingActions.length === 0) return;

    fetch(`/api/take_turn/${this.gameId}/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": this.getCSRFToken(),
      },
      body: JSON.stringify({
        actions: this.pendingActions,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((data) => {
            throw new Error(data.error || "Unknown error");
          });
        }
        return response.json();
      })
      .then((data) => {
        this.pendingActions = [];
        this.gameBoard.selectedEntity = null;
        this.cancelAction();
        this.connection.requestGameState();
      })
      .catch((error) => {
        alert("Error submitting turn: " + error.message);
      });
  }

  sendChatMessage() {
    const chatInput = document.getElementById("chat-input");
    const message = chatInput.value.trim();
    if (message) {
      this.connection.sendChatMessage(message);
      chatInput.value = "";
    }
  }

  addChatMessage(username, message) {
    const chatMessages = document.getElementById("chat-messages");
    const messageElement = document.createElement("div");
    messageElement.className = "chat-message mb-2";
    messageElement.innerHTML = `
      <span class="font-semibold text-blue-600 dark:text-blue-400">${username}:</span>
      <span class="ml-2 text-gray-700 dark:text-gray-300">${message}</span>
    `;
    chatMessages.appendChild(messageElement);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }
}
