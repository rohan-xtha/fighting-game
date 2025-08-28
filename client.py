import socket
import json
import pygame
import sys
import threading
import time
from game import Fighter, SCREEN_WIDTH, SCREEN_HEIGHT, GRAVITY, SCROLL_THRESH, TILE_SIZE, ROWS, COLS, TILE_TYPES, screen, scroll, bg_scroll, bg, screen_scroll, game_active, player1, player2, draw_bg, draw_health_bars, draw_controls, draw_game, check_winner, reset_game, slow_mo_timer, MAX_SLOW_MO_FRAMES, WIN_WIDTH, WIN_HEIGHT, GROUND_HEIGHT

class NetworkClient:
    def __init__(self, host='localhost', port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.host = host
        self.port = port
        self.connected = False
        self.player_id = None
        self.game_state = {}
        self.lock = threading.Lock()
    
    def connect(self):
        try:
            self.client.connect((self.host, self.port))
            self.connected = True
            
            # Start receiving thread
            receive_thread = threading.Thread(target=self.receive_data, daemon=True)
            receive_thread.start()
            
            # Wait for initial game state
            start_time = time.time()
            while not hasattr(self, 'player_id') and time.time() - start_time < 5:
                time.sleep(0.1)
                
            return self.connected
            
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            return False
    
    def receive_data(self):
        while self.connected:
            try:
                data = self.client.recv(8192).decode()
                if not data:
                    self.connected = False
                    break
                    
                messages = data.split('\n')
                for msg in messages:
                    if not msg.strip():
                        continue
                    try:
                        message = json.loads(msg)
                        self.handle_message(message)
                    except json.JSONDecodeError:
                        print(f"Invalid JSON: {msg}")
                        
            except (ConnectionResetError, ConnectionAbortedError):
                print("Connection to server lost")
                self.connected = False
                break
            except Exception as e:
                print(f"Error receiving data: {e}")
                self.connected = False
                break
    
    def handle_message(self, message):
        if message['type'] == 'init':
            self.player_id = message['player_id']
            with self.lock:
                self.game_state = message['game_state']
            print(f"Connected as {self.player_id}")
            
        elif message['type'] == 'game_state':
            with self.lock:
                self.game_state = message['game_state']
                
        elif message['type'] == 'game_start':
            print("Game started!")
            
        elif message['type'] == 'player_disconnected':
            print(f"{message['player_id']} has disconnected")
            # Handle player disconnection
            
    def send_data(self, data):
        if self.connected:
            try:
                self.client.send((json.dumps(data) + '\n').encode())
            except:
                print("Failed to send data to server")
                self.connected = False

def main():
    pygame.init()
    
    # Initialize network client
    import argparse
    parser = argparse.ArgumentParser(description='Game Client')
    parser.add_argument('--host', type=str, default='localhost', help='Server IP to connect to')
    parser.add_argument('--port', type=int, default=5555, help='Server port')
    args = parser.parse_args()
    
    client = NetworkClient(host=args.host, port=args.port)
    if not client.connect():
        print("Failed to connect to server. Starting in offline mode.")
        import game
        game.main()
        return
    
    # Wait until we receive initial game state
    start_time = time.time()
    while not hasattr(client, 'player_id') and time.time() - start_time < 5:
        time.sleep(0.1)
    
    if not hasattr(client, 'player_id'):
        print("Failed to receive initial game state. Starting in offline mode.")
        import game
        game.main()
        return
    
    # Game variables
    clock = pygame.time.Clock()
    FPS = 60
    
    # Create players
    player1 = None
    player2 = None
    
    # Game loop
    run = True
    while run:
        clock.tick(FPS)
        
        # Get game state
        with client.lock:
            game_state = client.game_state.copy()
        
        # Update players from game state
        if 'players' in game_state:
            if player1 is None or player2 is None:
                # Initialize players
                player1 = Fighter(200, 0, 'player1')
                player2 = Fighter(800, 0, 'player2')
            
            # Update player1
            p1_state = game_state['players'].get('player1', {})
            player1.rect.x = p1_state.get('x', 200)
            player1.rect.y = p1_state.get('y', 0)
            player1.health = p1_state.get('health', 100)
            player1.facing_right = p1_state.get('facing_right', True)
            player1.is_attacking = p1_state.get('is_attacking', False)
            player1.animation_frame = p1_state.get('animation_frame', 0)
            
            # Update player2
            p2_state = game_state['players'].get('player2', {})
            player2.rect.x = p2_state.get('x', 800)
            player2.rect.y = p2_state.get('y', 0)
            player2.health = p2_state.get('health', 100)
            player2.facing_right = p2_state.get('facing_right', False)
            player2.is_attacking = p2_state.get('is_attacking', False)
            player2.animation_frame = p2_state.get('animation_frame', 0)
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    run = False
                # Add other key events as needed
        
        # Get keyboard state
        keys = pygame.key.get_pressed()
        
        # Prepare player input
        player_input = {}
        if client.player_id == 'player1':
            # Player 1 controls (WASD + F, G)
            if keys[pygame.K_a]:
                player_input['move'] = -5
            elif keys[pygame.K_d]:
                player_input['move'] = 5
            
            if keys[pygame.K_f]:
                player_input['action'] = 'punch'
            elif keys[pygame.K_g]:
                player_input['action'] = 'kick'
            else:
                player_input['action'] = 'idle'
                
        elif client.player_id == 'player2':
            # Player 2 controls (Arrow keys + L, K)
            if keys[pygame.K_LEFT]:
                player_input['move'] = -5
            elif keys[pygame.K_RIGHT]:
                player_input['move'] = 5
            
            if keys[pygame.K_l]:
                player_input['action'] = 'punch'
            elif keys[pygame.K_k]:
                player_input['action'] = 'kick'
            else:
                player_input['action'] = 'idle'
        
        # Send input to server
        if client.connected and player_input:
            client.send_data(player_input)
        
        # Draw game
        screen.fill((0, 0, 0))
        
        # Draw background
        draw_bg()
        
        # Draw players
        if player1 and player2:
            # Determine drawing order based on y-position (player with higher y is in front)
            if player1.rect.bottom < player2.rect.bottom:
                player1.draw(screen, scroll)
                player2.draw(screen, scroll)
            else:
                player2.draw(screen, scroll)
                player1.draw(screen, scroll)
            
            # Draw health bars and controls
            draw_health_bars()
            draw_controls()
        
        # Draw connection status
        font = pygame.font.SysFont('Arial', 20)
        status_text = f"Connected as {client.player_id}" if client.connected else "Disconnected"
        status_color = (0, 255, 0) if client.connected else (255, 0, 0)
        status_surface = font.render(status_text, True, status_color)
        screen.blit(status_surface, (10, 10))
        
        pygame.display.update()
        
        # Cap the frame rate
        clock.tick(FPS)
    
    # Clean up
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
