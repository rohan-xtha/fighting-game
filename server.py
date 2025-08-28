import socket
import json
import threading
import time

class GameServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)  # Disable Nagle's algorithm
        self.server.bind((host, port))
        self.server.listen(2)  # Allow 2 players
        self.clients = []
        self.game_state = {
            'players': {
                'player1': {
                    'x': 200, 'y': 0, 'health': 100, 'action': 'idle',
                    'facing_right': True, 'is_attacking': False, 'animation_frame': 0
                },
                'player2': {
                    'x': 800, 'y': 0, 'health': 100, 'action': 'idle',
                    'facing_right': False, 'is_attacking': False, 'animation_frame': 0
                }
            },
            'game_started': False
        }
        self.lock = threading.Lock()
        self.player_count = 0
        print(f"Server started on {host}:{port}")

    def handle_client(self, conn, addr):
        print(f"New connection from {addr}")
        
        # Assign player ID (1 or 2)
        with self.lock:
            self.player_count += 1
            player_id = f'player{min(self.player_count, 2)}'  # Only allow 2 players
            if self.player_count > 2:
                conn.send(json.dumps({'error': 'Server is full'}).encode())
                conn.close()
                return
        
        try:
            # Send initial game state and player ID
            conn.send(json.dumps({
                'type': 'init',
                'player_id': player_id,
                'game_state': self.game_state
            }).encode())
            
            # If this is the second player, start the game
            if self.player_count == 2:
                self.broadcast({'type': 'game_start'})
                self.game_state['game_started'] = True
            
            while True:
                try:
                    data = conn.recv(4096).decode()
                    if not data:
                        break
                        
                    # Update game state based on player input
                    player_input = json.loads(data)
                    self.update_game_state(player_id, player_input)
                    
                except json.JSONDecodeError:
                    print(f"Invalid JSON from {addr}")
                    break
                except ConnectionResetError:
                    break
                    
        except Exception as e:
            print(f"Error with client {addr}: {e}")
        finally:
            print(f"Client {addr} disconnected")
            with self.lock:
                if player_id in ['player1', 'player2']:
                    self.player_count -= 1
                    self.game_state['players'][player_id]['health'] = 0
                    self.broadcast({
                        'type': 'player_disconnected',
                        'player_id': player_id
                    })
            conn.close()
    
    def update_game_state(self, player_id, player_input):
        with self.lock:
            if 'move' in player_input:
                self.game_state['players'][player_id]['x'] += player_input['move']
            if 'action' in player_input:
                self.game_state['players'][player_id]['action'] = player_input['action']
            if 'facing_right' in player_input:
                self.game_state['players'][player_id]['facing_right'] = player_input['facing_right']
            if 'animation_frame' in player_input:
                self.game_state['players'][player_id]['animation_frame'] = player_input['animation_frame']
            if 'health' in player_input:
                self.game_state['players'][player_id]['health'] = player_input['health']
            if 'is_attacking' in player_input:
                self.game_state['players'][player_id]['is_attacking'] = player_input['is_attacking']
            
            # Broadcast updated game state to all clients
            self.broadcast({
                'type': 'game_state',
                'game_state': self.game_state
            })
    
    def broadcast(self, data):
        """Send data to all connected clients"""
        message = json.dumps(data).encode()
        for client, _ in self.clients:
            try:
                client.send(message)
            except:
                continue
    
    def start(self):
        print("Waiting for connections...")
        try:
            while True:
                conn, addr = self.server.accept()
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(conn, addr),
                    daemon=True
                )
                self.clients.append((conn, addr))
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            for client, _ in self.clients:
                client.close()
            self.server.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Game Server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host IP to bind to')
    parser.add_argument('--port', type=int, default=5555, help='Port to listen on')
    args = parser.parse_args()
    
    server = GameServer(host=args.host, port=args.port)
    server.start()
