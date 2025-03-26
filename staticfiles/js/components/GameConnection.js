/**
 * Turn-Based Strategy Game
 * WebSocket connection management
 */

export class GameConnection {
  constructor(gameId) {
    this.gameId = gameId;
    this.socket = null;
    this.callbacks = {
      onGameState: null,
      onGameUpdate: null,
      onChatMessage: null,
      onConnect: null,
      onDisconnect: null,
    };

    this.connect();
  }

  connect() {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Use port 8001 explicitly for WebSocket connections
    const host = window.location.hostname + ":8001";
    const wsUrl = `${wsProtocol}//${host}/ws/game/${this.gameId}/`;

    console.log("Connecting to WebSocket at:", wsUrl);
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = (e) => {
      console.log("WebSocket connection established");
      if (this.callbacks.onConnect) this.callbacks.onConnect();

      // Request initial game state
      this.requestGameState();
    };

    this.socket.onmessage = (e) => {
      const data = JSON.parse(e.data);

      if (data.type === "game_state" && this.callbacks.onGameState) {
        this.callbacks.onGameState(data.game_state);
      } else if (data.type === "game_update" && this.callbacks.onGameUpdate) {
        this.callbacks.onGameUpdate(data.update_type, data.data);
      } else if (data.type === "chat_message" && this.callbacks.onChatMessage) {
        this.callbacks.onChatMessage(data.username, data.message);
      }
    };

    this.socket.onclose = (e) => {
      console.log("WebSocket connection closed");
      if (this.callbacks.onDisconnect) this.callbacks.onDisconnect();

      // Try to reconnect after a delay
      setTimeout(() => this.connect(), 3000);
    };

    this.socket.onerror = (e) => {
      console.error("WebSocket error:", e);
    };
  }

  requestGameState() {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          type: "request_game_state",
        })
      );
    }
  }

  sendChatMessage(message) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          type: "chat_message",
          message: message,
        })
      );
    }
  }

  setCallback(type, callback) {
    if (this.callbacks.hasOwnProperty(type)) {
      this.callbacks[type] = callback;
    }
  }
}
