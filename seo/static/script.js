const boardSize = 19;
const gameBoard = document.getElementById('game-board');
const gameStatus = document.getElementById('game-status');
const resetButton = document.getElementById('reset-button');

const socket = io();

let playerColor = null;
let myTurn = false;

function drawBoard(board) {
    gameBoard.innerHTML = '';
    for (let i = 0; i < boardSize; i++) {
        for (let j = 0; j < boardSize; j++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.row = i;
            cell.dataset.col = j;
            cell.addEventListener('click', handleCellClick);
            
            if(board[i][j]) {
                const stone = document.createElement('div');
                stone.classList.add('stone', board[i][j]);
                cell.appendChild(stone);
            }
            gameBoard.appendChild(cell);
        }
    }
}

function handleCellClick(event) {
    if (!myTurn) return;
    const row = parseInt(event.target.dataset.row);
    const col = parseInt(event.target.dataset.col);
    socket.emit('place_stone', { row, col });
}

resetButton.addEventListener('click', () => {
    socket.emit('reset_game');
});

socket.on('connect', () => {
    console.log('Connected to server');
    socket.emit('join', {});
});

socket.on('player_assignment', (data) => {
    playerColor = data.player;
    document.getElementById('player-info').textContent = `You are ${playerColor}`;
});

socket.on('start_game', (data) => {
    drawBoard(data.board);
    myTurn = (playerColor === data.turn);
    gameStatus.textContent = data.turn === playerColor ? "Your turn" : `${data.turn}'s turn`;
});

socket.on('update', (data) => {
    drawBoard(data.board);
    myTurn = (playerColor === data.turn);
    gameStatus.textContent = data.turn === playerColor ? "Your turn" : `${data.turn}'s turn`;
});

socket.on('game_over', (data) => {
    myTurn = false;
    gameStatus.textContent = `${data.winner.charAt(0).toUpperCase() + data.winner.slice(1)} Wins!`;
    alert(`${data.winner} wins!`);
});

socket.on('status', (data) => {
    gameStatus.textContent = data.msg;
});

socket.on('player_left', (data) => {
    alert(`${data.color} has left the game.`);
    gameStatus.textContent = 'Waiting for another player...';
});

// Initial setup
drawBoard(Array(boardSize).fill(null).map(() => Array(boardSize).fill(null)));
gameStatus.textContent = 'Connecting to server...';
