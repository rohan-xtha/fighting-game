from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import random
import time

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'your-secret-key'  # In production, use environment variables

# Allow all origins for development
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='eventlet',
                   logger=True,
                   engineio_logger=True)

# For production
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

@app.route('/')
def index():
    return app.send_static_file('index.html')

# Store active players and matchmaking queue
players_online = set()
matchmaking_queue = []
active_matches = {}
player_data = {}

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")
    if request.sid in players_online:
        players_online.remove(request.sid)
        if request.sid in player_data:
            del player_data[request.sid]
    
    # Remove from matchmaking queue
    if request.sid in matchmaking_queue:
        matchmaking_queue.remove(request.sid)
    
    # Handle disconnection during a match
    for match_id, players in list(active_matches.items()):
        if request.sid in players:
            other_player = players[0] if players[1] == request.sid else players[1]
            emit('opponent_disconnected', room=other_player)
            del active_matches[match_id]
            break

@socketio.on('player_online')
def handle_player_online(data):
    player_id = request.sid
    players_online.add(player_id)
    player_data[player_id] = {
        'username': data.get('username', 'Player'),
        'status': 'online'
    }
    emit('player_count', {'count': len(players_online)}, broadcast=True)

@socketio.on('join_matchmaking')
def handle_join_matchmaking():
    player_id = request.sid
    
    if player_id in matchmaking_queue:
        return
    
    matchmaking_queue.append(player_id)
    player_data[player_id]['status'] = 'searching'
    
    # Try to find a match
    if len(matchmaking_queue) >= 2:
        player1 = matchmaking_queue.pop(0)
        player2 = matchmaking_queue.pop(0)
        
        match_id = f"match_{int(time.time())}_{random.randint(1000, 9999)}"
        active_matches[match_id] = [player1, player2]
        
        # Notify both players
        emit('match_found', {'match_id': match_id, 'opponent': player_data[player2]['username']}, room=player1)
        emit('match_found', {'match_id': match_id, 'opponent': player_data[player1]['username']}, room=player2)
        
        player_data[player1]['status'] = 'in_game'
        player_data[player2]['status'] = 'in_game'
    else:
        emit('searching_for_opponent', {'position': len(matchmaking_queue)})

@socketio.on('leave_matchmaking')
def handle_leave_matchmaking():
    player_id = request.sid
    if player_id in matchmaking_queue:
        matchmaking_queue.remove(player_id)
        player_data[player_id]['status'] = 'online'
        emit('left_matchmaking')

@socketio.on('player_ready')
def handle_player_ready(data):
    match_id = data.get('match_id')
    if match_id in active_matches:
        players = active_matches[match_id]
        if request.sid in players:
            player_index = players.index(request.sid)
            emit('opponent_ready', {'player_number': player_index + 1}, room=players[1 - player_index])

@socketio.on('player_input')
def handle_player_input(data):
    # Forward input to the other player
    match_id = data.get('match_id')
    if match_id in active_matches:
        players = active_matches[match_id]
        other_player = players[1] if players[0] == request.sid else players[0]
        emit('opponent_input', {'input': data['input']}, room=other_player)

@socketio.on('game_over')
def handle_game_over(data):
    match_id = data.get('match_id')
    if match_id in active_matches:
        players = active_matches[match_id]
        other_player = players[1] if players[0] == request.sid else players[0]
        emit('opponent_disconnected', room=other_player)
        del active_matches[match_id]

if __name__ == '__main__':
    print("Starting game server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
