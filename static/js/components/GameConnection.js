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
    this.isConnected = false;
    this.connect();
  }

  connect() {
    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Explicitly use port 8001 for WebSocket connections through Daphne
    const host = window.location.hostname + ":8001";
    const wsUrl = `${wsProtocol}//${host}/ws/game/${this.gameId}/`;

    console.log("Attempting WebSocket connection to:", wsUrl);
    
    try {
      this.socket = new WebSocket(wsUrl);

      this.socket.onopen = (e) => {
        console.log("WebSocket connection established successfully");
        this.isConnected = true;
        if (this.callbacks.onConnect) this.callbacks.onConnect();
        // Request initial game state
        this.requestGameState();
      };

      this.socket.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          console.log("Received WebSocket message:", data);

          if (data.type === "game_state" && this.callbacks.onGameState) {
            this.callbacks.onGameState(data.state);
          } else if (data.type === "game_update" && this.callbacks.onGameUpdate) {
            this.callbacks.onGameUpdate(data.update_type, data.data);
          } else if (data.type === "chat_message" && this.callbacks.onChatMessage) {
            this.callbacks.onChatMessage(data.username, data.message);
          } else if (data.type === "error") {
            console.error("WebSocket error message:", data.message);
          }
        } catch (error) {
          console.error("Error processing WebSocket message:", error);
        }
      };

      this.socket.onclose = (e) => {
        console.log("WebSocket connection closed. Code:", e.code, "Reason:", e.reason);
        this.isConnected = false;
        if (this.callbacks.onDisconnect) this.callbacks.onDisconnect();

        // Try to reconnect after a delay
        setTimeout(() => {
          if (!this.isConnected) this.connect();
        }, 3000);
      };

      this.socket.onerror = (e) => {
        console.error("WebSocket error occurred:", e);
        this.isConnected = false;
      };
    } catch (error) {
      console.error("Error creating WebSocket connection:", error);
    }
  }

  disconnect() {
    if (this.socket) {
      this.isConnected = false;
      this.socket.close();
      this.socket = null;
    }
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

  sendGameAction(actionType, actionData) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(
        JSON.stringify({
          type: "game_action",
          action_type: actionType,
          action_data: actionData,
        })
      );
    }
  }

  setCallback(type, callback) {
    this.callbacks[type] = callback;
  }
}
