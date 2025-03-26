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
    document.getElementById("current-turn").textContent =
      this.gameState.current_turn;
    document.getElementById("current-player").textContent =
      this.gameState.current_player_username || "None";

    // Update player resources if player
    if (this.playerId) {
      const currentPlayer = this.gameState.players.find(
        (p) => p.id === this.playerId
      );
      if (currentPlayer) {
        document.getElementById("player-resources").textContent =
          currentPlayer.resources;
      }
    }

    // Render game board
    if (!this.gameBoard) {
      this.gameBoard = new GameBoard(this.gameState, this.playerId, (x, y) =>
        this.handleCellClick(x, y)
      );
    } else {
      this.gameBoard.gameState = this.gameState;
    }
    this.gameBoard.initializeBoard0();

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
    document.getElementById("end-turn-btn").disabled = !isMyTurn;

    const actionInfo = document.getElementById("action-info");
    const cancelActionBtn = document.getElementById("cancel-action-btn");
    const buildOptions = document.getElementById("build-options");
    const trainOptions = document.getElementById("train-options");

    if (this.currentAction) {
      actionInfo.classList.remove("d-none");
      actionInfo.textContent = `Current action: ${this.currentAction.type}`;
      cancelActionBtn.classList.remove("d-none");

      // Show/hide appropriate options
      if (this.currentAction.type === "build") {
        buildOptions.classList.remove("d-none");
      } else {
        buildOptions.classList.add("d-none");
      }
    } else {
      actionInfo.classList.add("d-none");
      cancelActionBtn.classList.add("d-none");

      if (isMyTurn) {
        buildOptions.classList.remove("d-none");
      } else {
        buildOptions.classList.add("d-none");
      }
      trainOptions.classList.add("d-none");
    }
  }

  handleCellClick(x, y) {
    if (!this.playerId || this.gameState.current_player_id !== this.playerId)
      return;

    if (this.currentAction) {
      if (
        this.currentAction.type === "build" &&
        this.isValidBuildPosition(x, y)
      ) {
        this.addAction({
          type: "build",
          building_type: this.currentAction.building_type,
          x: x,
          y: y,
        });
        this.cancelAction();
      }
      return;
    }

    // Check if there's a unit or building at clicked position
    const cell = this.boardElement.querySelector(
      `game-cell[data-x="${x}"][data-y="${y}"]`
    );
    const entity = cell?.firstElementChild;

    if (entity) {
      const entityType = entity.dataset.type;
      const entityId = parseInt(entity.dataset.id);
      const playerId = parseInt(entity.dataset.playerId);

      if (playerId === this.playerId) {
        // Select own unit/building
        const selectedEntity = this.selectEntity(entityType, entityId);
        if (selectedEntity) {
          if (entityType === "unit") {
            this.currentAction = {
              type: "select_unit",
              unit_id: entityId,
            };
          } else if (
            entityType === "building" &&
            selectedEntity.building_type === "barracks"
          ) {
            document.getElementById("train-options").classList.remove("d-none");
            document
              .getElementById("train-options")
              .setAttribute("data-barracks-id", entityId);
          }
        }
      } else if (this.currentAction?.type === "select_unit") {
        // Attack enemy unit/building
        this.addAction({
          type: "attack",
          unit_id: this.currentAction.unit_id,
          target_x: x,
          target_y: y,
        });
        this.cancelAction();
      }
    } else if (this.currentAction?.type === "select_unit") {
      // Move unit to empty cell
      this.addAction({
        type: "move_unit",
        unit_id: this.currentAction.unit_id,
        x: x,
        y: y,
      });
      this.cancelAction();
    }
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
    document
      .querySelectorAll(".valid-move, .valid-attack, .valid-build")
      .forEach((el) => {
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
    const message = document.getElementById("chat-input").value.trim();
    if (!message) return;

    this.connection.sendChatMessage(message);
    document.getElementById("chat-input").value = "";
  }

  addChatMessage(username, message) {
    const isSystem = username === "System";
    const chatMessage = document.createElement("div");
    chatMessage.className = `chat-message ${
      isSystem ? "chat-message-system" : "chat-message-user"
    }`;
    chatMessage.innerHTML = `<strong>${username}:</strong> ${message}`;

    const chatContainer = document.getElementById("chat-container");
    chatContainer.appendChild(chatMessage);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
}
