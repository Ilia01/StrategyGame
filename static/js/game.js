/**
 * Turn-Based Strategy Game
 * Main game initialization and setup
 */

import { GameUI } from "./components/GameUI.js";
import { UNIT_COSTS, BUILDING_COSTS } from "./utils/constants.js";
import { getCookie } from "./utils/helpers.js";

// UI Setup functions
function setupBuildButtons() {
  const buildOptionsContainer = document.getElementById("build-options");
  if (!buildOptionsContainer) return;

  buildOptionsContainer.innerHTML = `
    ${Object.entries(BUILDING_COSTS)
      .map(
        ([buildingType, cost]) => `
      <button class="btn btn-sm btn-outline-secondary build-btn m-1" data-building-type="${buildingType}">
        Build ${buildingType} <span class="badge bg-info">${cost}</span>
      </button>
    `
      )
      .join("")}
  `;
}

function setupTrainButtons() {
  const trainOptionsContainer = document.getElementById("train-options");
  if (!trainOptionsContainer) return;

  trainOptionsContainer.innerHTML = `
    ${Object.entries(UNIT_COSTS)
      .map(
        ([unitType, cost]) => `
      <button class="btn btn-sm btn-outline-secondary train-btn m-1" data-unit-type="${unitType}">
        Train ${unitType} <span class="badge bg-info">${cost}</span>
      </button>
    `
      )
      .join("")}
  `;
}

// Game initialization
function initializeGameUI(gameUI) {
  gameUI.connection.setCallback("onGameState", (gameState) => {
    gameUI.gameState = gameState;
    gameUI.renderGameState();
  });

  gameUI.connection.setCallback("onChatMessage", (username, message) => {
    gameUI.addChatMessage(username, message);
  });

  gameUI.setupEventHandlers();
  setupBuildButtons();
  setupTrainButtons();
}

export function initializeGame(gameId, playerId) {
  const gameUI = new GameUI(gameId, playerId);
  initializeGameUI(gameUI);
  gameUI.connection.connect();
}

export function initializeIndex() {
  $("#create-game-form").submit(handleCreateGame);
  $(".join-game-btn").click(handleJoinGame);
}

function handleCreateGame(e) {
  e.preventDefault();
  const formData = {
    name: $("#game-name").val(),
    map_size: $("#map-size").val(),
    max_players: $("#max-players").val(),
  };

  $.ajax({
    url: "/api/create_game/", // Updated path
    type: "POST",
    data: JSON.stringify(formData),
    contentType: "application/json",
    headers: { "X-CSRFToken": getCookie("csrftoken") },
    success: (response) =>
      (window.location.href = `/game/${response.game_id}/`),
    error: (xhr) =>
      alert(
        "Error creating game: " + xhr.responseJSON?.error || "Unknown error"
      ),
  });
}

function handleJoinGame() {
  const gameId = $(this).data("game-id");
  $.ajax({
    url: `/api/join_game/${gameId}/`, // Updated path
    type: "POST",
    headers: { "X-CSRFToken": getCookie("csrftoken") },
    success: () => (window.location.href = `/game/${gameId}/`),
    error: (xhr) =>
      alert(
        "Error joining game: " + xhr.responseJSON?.error || "Unknown error"
      ),
  });
}

document.addEventListener("DOMContentLoaded", function () {
  const gameId = document.body.getAttribute("data-game-id");
  const playerId = document.body.getAttribute("data-player-id");

  if (gameId && playerId) {
    initializeGame(gameId, playerId);
  }
  setupBuildButtons();
  setupTrainButtons();
});
