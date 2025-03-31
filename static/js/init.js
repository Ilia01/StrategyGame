import { Game } from './game.js';

// Initialize the game when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get the game container
    const container = document.getElementById('game-board');
    if (!container) {
        console.error('Game board container not found');
        return;
    }

    // Get the game ID from the URL or data attribute
    const gameId = container.dataset.gameId;
    if (!gameId) {
        console.error('Game ID not found');
        return;
    }

    // Initialize the game
    console.log('Initializing game with ID:', gameId);
    window.game = new Game(gameId, container);
}); 