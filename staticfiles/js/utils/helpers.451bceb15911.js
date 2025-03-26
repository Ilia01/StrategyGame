/**
 * Turn-Based Strategy Game
 * Utility helper functions
 */

/**
 * Calculate Manhattan distance between two points
 */
export function calculateDistance(x1, y1, x2, y2) {
  return Math.abs(x1 - x2) + Math.abs(y1 - y2);
}

/**
 * Get movement cost for a terrain type
 */
export function getTerrainMovementCost(terrain) {
  switch (terrain) {
    case "plains":
      return 1;
    case "forest":
      return 2;
    case "mountain":
      return 3;
    case "water":
      return Infinity; // Cannot move through water
    default:
      return 1;
  }
}

/**
 * Get icon for a unit type
 */
export function getUnitTypeIcon(unitType) {
  switch (unitType) {
    case "infantry":
      return "👤";
    case "archer":
      return "🏹";
    case "cavalry":
      return "🐎";
    case "siege":
      return "⚔️";
    default:
      return "?";
  }
}

/**
 * Get icon for a building type
 */
export function getBuildingTypeIcon(buildingType) {
  switch (buildingType) {
    case "base":
      return "🏰";
    case "barracks":
      return "🏛️";
    case "farm":
      return "🌾";
    case "mine":
      return "⛏️";
    default:
      return "?";
  }
}

/**
 * Get color for a player number
 */
export function getPlayerColor(playerNumber) {
  const colors = ["#ff0000", "#0000ff", "#00ff00", "#ffff00"];
  return colors[(playerNumber - 1) % colors.length];
}

/**
 * Get CSRF token from cookies
 */
export function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split("; ");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

/**
 * Get CSRF token from cookies
 */
export function getCSRFToken() {
  return getCookie("csrftoken");
}
