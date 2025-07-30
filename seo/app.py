from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Game state
games = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = 'game_room' # Simplified to a single room for now
    join_room(room)
    if room not in games:
        games[room] = {
            'board': [[None for _ in range(19)] for _ in range(19)],
            'players': {request.sid: 'black'},
            'current_player': request.sid
        }
        emit('player_assignment', {'player': 'black', 'sid': request.sid}, room=request.sid)
        emit('status', {'msg': 'Waiting for another player...'}, room=room)
    else:
        if len(games[room]['players']) == 1 and request.sid not in games[room]['players']:
            games[room]['players'][request.sid] = 'white'
            emit('player_assignment', {'player': 'white', 'sid': request.sid}, room=request.sid)
            emit('start_game', {'board': games[room]['board'], 'turn': 'black'}, room=room)
        else:
            # Spectator or player rejoining
            emit('player_assignment', {'player': 'spectator'}, room=request.sid)
            emit('update', games[room]['board'], room=request.sid)


@socketio.on('place_stone')
def on_place_stone(data):
    room = 'game_room'
    game = games.get(room)
    if not game or request.sid not in game['players']:
        return

    player_color = game['players'][request.sid]
    if game['current_player'] == request.sid and game['board'][data['row']][data['col']] is None:
        row, col = data['row'], data['col']
        game['board'][row][col] = player_color

        if check_win(game['board'], row, col, player_color):
            emit('game_over', {'winner': player_color}, room=room)
            game['current_player'] = None # Game over
        else:
            # Switch turns
            for sid, color in game['players'].items():
                if sid != request.sid:
                    game['current_player'] = sid
                    break
        
        emit('update', {'board': game['board'], 'turn': game['players'].get(game['current_player'])}, room=room)

@socketio.on('reset_game')
def on_reset_game():
    room = 'game_room'
    if room in games:
        # Preserve players, reset board and turn
        player_sids = list(games[room]['players'].keys())
        games[room]['board'] = [[None for _ in range(19)] for _ in range(19)]
        games[room]['current_player'] = player_sids[0]
        emit('start_game', {'board': games[room]['board'], 'turn': 'black'}, room=room)


@socketio.on('disconnect')
def on_disconnect():
    room = 'game_room'
    if room in games and request.sid in games[room]['players']:
        player_color = games[room]['players'][request.sid]
        del games[room]['players'][request.sid]
        emit('player_left', {'color': player_color}, room=room)
        if len(games[room]['players']) < 2:
            # Reset if a player leaves
            if games[room]['players']:
                remaining_sid = list(games[room]['players'].keys())[0]
                emit('status', {'msg': 'The other player left. Waiting for a new opponent...'}, room=remaining_sid)
            games.pop(room, None)


def check_win(board, row, col, player):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        # Check in the positive direction
        for i in range(1, 5):
            r, c = row + dr * i, col + dc * i
            if 0 <= r < 19 and 0 <= c < 19 and board[r][c] == player:
                count += 1
            else:
                break
        # Check in the negative direction
        for i in range(1, 5):
            r, c = row - dr * i, col - dc * i
            if 0 <= r < 19 and 0 <= c < 19 and board[r][c] == player:
                count += 1
            else:
                break
        if count >= 5:
            return True
    return False

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
