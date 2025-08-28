import pygame
import sys
import math
import random
import json
from js import document, window, WebSocket, setInterval, clearInterval
from pyodide.ffi import create_proxy

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2
WAITING_FOR_PLAYER = 3
ONLINE_MATCHMAKING = 4
ONLINE_PLAYING = 5

# Online status
online_players = 0
challenged = False
socket = None
player_id = None
match_id = None
player_number = 1
last_sent_input = {}
last_received_input = {}
input_send_interval = None

# Initialize Pygame
pygame.init()

# Set up display
canvas = document.getElementById("game-canvas")
WIDTH, HEIGHT = 1000, 600
screen = pygame.Surface((WIDTH, HEIGHT))
pygame_screen = pygame.canvas

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Game variables
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5

# Load assets
def load_image(name, scale=1):
    try:
        image = pygame.image.load(f"assets/{name}")
        if scale != 1:
            new_width = int(image.get_width() * scale)
            new_height = int(image.get_height() * scale)
            return pygame.transform.scale(image, (new_width, new_height))
        return image
    except:
        # Create a colored rectangle as fallback
        surf = pygame.Surface((50, 100))
        surf.fill((random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        return surf

# Player class
class Fighter:
    def __init__(self, x, y, controls, name):
        self.rect = pygame.Rect(x, y, 50, 100)
        self.vel_y = 0
        self.jump = False
        self.health = 100
        self.controls = controls
        self.facing_right = True
        self.is_attacking = False
        self.attack_frame = 0
        self.attack_cooldown = 0
        self.name = name
        self.load_animations()
    
    def load_animations(self):
        # Simple colored rectangles for web version
        self.idle_img = pygame.Surface((50, 100))
        self.idle_img.fill((0, 128, 255) if self.name == "player1" else (255, 100, 100))
        
        self.punch_img = pygame.Surface((70, 100))
        self.punch_img.fill((0, 200, 255) if self.name == "player1" else (255, 150, 150))
        
        self.kick_img = pygame.Surface((60, 110))
        self.kick_img.fill((0, 170, 255) if self.name == "player1" else (255, 120, 120))
    
    def move(self, target):
        # Movement logic here (simplified for web)
        keys = pygame.key.get_pressed()
        
        # Left/Right movement
        if keys[self.controls['left']]:
            self.rect.x -= PLAYER_SPEED
            self.facing_right = False
        if keys[self.controls['right']]:
            self.rect.x += PLAYER_SPEED
            self.facing_right = True
            
        # Jump
        if keys[self.controls['up']] and not self.jump:
            self.vel_y = JUMP_STRENGTH
            self.jump = True
        
        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y
        
        # Ground collision
        if self.rect.bottom > HEIGHT - 50:
            self.rect.bottom = HEIGHT - 50
            self.vel_y = 0
            self.jump = False
            
        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > WIDTH:
            self.rect.right = WIDTH
    
    def attack(self, attack_type, target):
        if self.attack_cooldown == 0:
            self.is_attacking = True
            self.attack_frame = 0
            self.attack_type = attack_type
            
            # Check if attack hits
            attack_rect = pygame.Rect(
                self.rect.right if self.facing_right else self.rect.left - 60,
                self.rect.centery - 20,
                60, 40
            )
            
            if attack_rect.colliderect(target.rect):
                target.health -= 10 if attack_type == 'punch' else 15
                target.health = max(0, target.health)
                
            self.attack_cooldown = 20
    
    def update(self, target):
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        if self.is_attacking:
            self.attack_frame += 1
            if self.attack_frame > 10:  # Attack animation lasts 10 frames
                self.is_attacking = False
        
        self.move(target)
    
    def draw(self, surface, scroll):
        # Draw character
        if self.is_attacking:
            if self.attack_type == 'punch':
                img = self.punch_img
            else:
                img = self.kick_img
        else:
            img = self.idle_img
        
        # Flip image if facing left
        if not self.facing_right:
            img = pygame.transform.flip(img, True, False)
        
        surface.blit(img, (self.rect.x - scroll[0], self.rect.y - scroll[1]))
        
        # Draw health bar
        health_width = 100 * (self.health / 100)
        pygame.draw.rect(surface, (255, 0, 0), (self.rect.x - scroll[0], self.rect.y - 20 - scroll[1], 100, 10))
        pygame.draw.rect(surface, (0, 255, 0), (self.rect.x - scroll[0], self.rect.y - 20 - scroll[1], health_width, 10))

# Game state
game_state = MENU
vs_bot = True
player1 = None
player2 = None

def create_players():
    global player1, player2
    player1 = Fighter(200, HEIGHT - 200, 
                     {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w,
                      'punch': pygame.K_f, 'kick': pygame.K_g}, 'player1')
    
    if vs_bot:
        player2 = Fighter(800, HEIGHT - 200, 
                         {'left': None, 'right': None, 'up': None,
                          'punch': None, 'kick': None}, 'bot')
    else:
        player2 = Fighter(800, HEIGHT - 200, 
                         {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP,
                          'punch': pygame.K_k, 'kick': pygame.K_l}, 'player2')

def bot_ai():
    if not vs_bot or not player1 or not player2:
        return
    
    # Simple AI: Move towards player and attack when close
    dx = player1.rect.centerx - player2.rect.centerx
    dy = player1.rect.centery - player2.rect.centery
    distance = math.sqrt(dx*dx + dy*dy)
    
    # Face the player
    player2.facing_right = dx > 0
    
    # Move towards player
    if abs(dx) > 80:  # If far, move closer
        if dx > 0:
            player2.rect.x += 2
        else:
            player2.rect.x -= 2
    
    # Randomly jump
    if random.random() < 0.01:  # 1% chance per frame
        player2.jump = True
    
    # Randomly attack when close
    if distance < 100 and random.random() < 0.02:  # 2% chance per frame when close
        if random.choice([True, False]):
            player2.attack('punch', player1)
        else:
            player2.attack('kick', player1)

def connect_to_server():
    global socket, player_id
    
    # In a real browser environment, this would be the WebSocket URL
    # For Pyodide, we'll simulate the connection
    print("Connecting to game server...")
    player_id = f"player_{random.randint(1000, 9999)}"
    
    # Simulate receiving player count
    def update_player_count():
        global online_players
        online_players = random.randint(10, 100)
    
    # Update player count every 5 seconds
    setInterval(create_proxy(update_player_count), 5000)
    update_player_count()

def send_ws_message(message_type, data=None):
    if data is None:
        data = {}
    data['type'] = message_type
    data['player_id'] = player_id
    print(f"Sending: {data}")
    # In a real implementation, this would send data through WebSocket
    # socket.send(json.dumps(data))

def draw_menu():
    global online_players, challenged, game_state
    
    screen.fill((30, 30, 40))
    font = pygame.font.SysFont(None, 64)
    title = font.render("SHADOW FIGHTERS", True, (255, 255, 255))
    screen.blit(title, (WIDTH//2 - title.get_width()//2, 80))
    
    # Online players counter
    online_text = font.render(f"ONLINE: {online_players}", True, (100, 200, 255))
    screen.blit(online_text, (WIDTH//2 - online_text.get_width()//2, 150))
    
    font = pygame.font.SysFont(None, 36)
    
    # Game mode selection
    mode_title = font.render("SELECT GAME MODE:", True, (255, 255, 200))
    screen.blit(mode_title, (WIDTH//2 - mode_title.get_width()//2, 240))
    
    # VS BOT option
    vs_bot_color = (100, 255, 100) if vs_bot else (200, 200, 200)
    vs_bot_text = "[X] VS BOT" if vs_bot else "[ ] VS BOT"
    mode_text = font.render(vs_bot_text, True, vs_bot_color)
    screen.blit(mode_text, (WIDTH//2 - mode_text.get_width()//2, 290))
    
    # VS FRIEND option
    vs_friend_color = (100, 255, 100) if not vs_bot else (200, 200, 200)
    vs_friend_text = "[X] VS FRIEND" if not vs_bot else "[ ] VS FRIEND"
    friend_text = font.render(vs_friend_text, True, vs_friend_color)
    screen.blit(friend_text, (WIDTH//2 - friend_text.get_width()//2, 330))
    
    # Online options (only in VS FRIEND mode)
    if not vs_bot:
        # Challenge button
        challenge_color = (255, 200, 100) if not challenged else (100, 255, 100)
        challenge_text = "[C] CHALLENGE RANDOM PLAYER" if not challenged else "[C] SEARCHING FOR OPPONENT..."
        challenge_render = font.render(challenge_text, True, challenge_color)
        screen.blit(challenge_render, (WIDTH//2 - challenge_render.get_width()//2, 380))
        
        # Online status
        online_status = "ONLINE" if player_id else "OFFLINE"
        status_color = (100, 255, 100) if player_id else (255, 100, 100)
        status_text = font.render(f"Status: {online_status}", True, status_color)
        screen.blit(status_text, (WIDTH - 150, 20))
    
    # Instructions
    instructions = [
        "SPACE: Change mode",
        "ENTER: Start game",
        "ESC: Back to menu"
    ]
    
    for i, text in enumerate(instructions):
        inst_text = font.render(text, True, (180, 180, 180))
        screen.blit(inst_text, (WIDTH//2 - inst_text.get_width()//2, 450 + i * 30))
    
    pygame_screen.blit(pygame.transform.scale(screen, (canvas.width, canvas.height)), (0, 0))
    pygame.display.flip()

def draw_game_over(winner):
    screen.fill((30, 30, 40))
    font = pygame.font.SysFont(None, 64)
    if winner == 1:
        text = font.render("PLAYER 1 WINS!", True, (100, 255, 100))
    else:
        text = font.render("PLAYER 2 WINS!" if not vs_bot else "BOT WINS!", True, (255, 100, 100))
    
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 200))
    
    font = pygame.font.SysFont(None, 36)
    restart_text = font.render("Press R to restart", True, (200, 200, 200))
    menu_text = font.render("Press M for menu", True, (200, 200, 200))
    
    screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, 300))
    screen.blit(menu_text, (WIDTH//2 - menu_text.get_width()//2, 350))
    
    pygame_screen.blit(pygame.transform.scale(screen, (canvas.width, canvas.height)), (0, 0))
    pygame.display.flip()

# Game loop
def create_online_players():
    global player1, player2, player_number, input_send_interval
    
    player1 = Fighter(200, HEIGHT - 200, 
                     {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w,
                      'punch': pygame.K_f, 'kick': pygame.K_g}, 'You')
    
    player2 = Fighter(800, HEIGHT - 200, 
                     {'left': None, 'right': None, 'up': None,
                      'punch': None, 'kick': None}, 'Opponent')
    
    # Start sending input updates
    if input_send_interval:
        clearInterval(input_send_interval)
    
    def send_input_updates():
        keys = pygame.key.get_pressed()
        input_state = {
            'left': keys[pygame.K_a],
            'right': keys[pygame.K_d],
            'up': keys[pygame.K_w],
            'punch': keys[pygame.K_f],
            'kick': keys[pygame.K_g]
        }
        if input_state != last_sent_input.get('state'):
            send_ws_message('player_input', {
                'match_id': match_id,
                'input': input_state
            })
            last_sent_input['state'] = input_state
    
    input_send_interval = setInterval(create_proxy(send_input_updates), 50)  # 20 updates per second

def game_loop():
    global game_state, player1, player2, vs_bot, match_id, player_number
    clock = pygame.time.Clock()
    scroll = [0, 0]
    
    create_players()
    
    def update():
        # Update players
        player1.update(player2)
        player2.update(player1)
        
        # Update camera scroll
        scroll[0] += (player1.rect.x - scroll[0] - WIDTH//2) * 0.1
        scroll[1] += (player1.rect.y - scroll[1] - HEIGHT//2) * 0.1
        
        # Keep scroll within bounds
        scroll[0] = max(0, min(scroll[0], WIDTH - 100))
        scroll[1] = max(0, min(scroll[1], HEIGHT - 100))
        
        # Check for attacks
        keys = pygame.key.get_pressed()
        if keys[pygame.K_f]:
            player1.attack('punch', player2)
        if keys[pygame.K_g]:
            player1.attack('kick', player2)
        if keys[pygame.K_k]:
            player2.attack('punch', player1)
        if keys[pygame.K_l]:
            player2.attack('kick', player1)
    
    def draw():
        # Clear screen
        screen.fill((50, 50, 50))
        
        # Draw ground
        pygame.draw.rect(screen, (100, 100, 100), (0, HEIGHT - 50, WIDTH, 50))
        
        # Draw players
        if player1.rect.centery < player2.rect.centery:
            player1.draw(screen, scroll)
            player2.draw(screen, scroll)
        else:
            player2.draw(screen, scroll)
            player1.draw(screen, scroll)
        
        # Draw HUD
        font = pygame.font.SysFont(None, 36)
        p1_text = font.render(f"P1: {player1.health}", True, (255, 255, 255))
        p2_text = font.render(f"P2: {player2.health}", True, (255, 255, 255))
        screen.blit(p1_text, (20, 20))
        screen.blit(p2_text, (WIDTH - 100, 20))
        
        # Draw to canvas
        pygame_screen.blit(pygame.transform.scale(screen, (canvas.width, canvas.height)), (0, 0))
        pygame.display.flip()
    
    # Main game loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            
            if event.type == pygame.KEYDOWN:
                if game_state == MENU:
                    if event.key == pygame.K_RETURN:
                        if not vs_bot and challenged:
                            game_state = ONLINE_MATCHMAKING
                            send_ws_message('join_matchmaking')
                        else:
                            game_state = PLAYING
                            create_players()
                    elif event.key == pygame.K_SPACE:
                        vs_bot = not vs_bot
                        challenged = False  # Reset challenge when changing modes
                    # C to challenge (only in VS FRIEND mode)
                    elif event.key == pygame.K_c and not vs_bot:
                        challenged = not challenged
                        if challenged:
                            game_state = ONLINE_MATCHMAKING
                            send_ws_message('join_matchmaking')
                        else:
                            send_ws_message('leave_matchmaking')
                            game_state = MENU
                
                elif game_state == PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        if game_state == ONLINE_MATCHMAKING:
                            send_ws_message('leave_matchmaking')
                        game_state = MENU
                    
                    # Player 1 attacks
                    if event.key == pygame.K_f:
                        player1.attack('punch', player2)
                    if event.key == pygame.K_g:
                        player1.attack('kick', player2)
                    
                    # Player 2 attacks (if not bot)
                    if not vs_bot:
                        if event.key == pygame.K_k:
                            player2.attack('punch', player1)
                        if event.key == pygame.K_l:
                            player2.attack('kick', player1)
                
                elif game_state == GAME_OVER:
                    if event.key == pygame.K_r:  # Restart
                        game_state = PLAYING
                        create_players()
                    elif event.key == pygame.K_m:  # Back to menu
                        game_state = MENU
        
        if game_state == MENU:
            draw_menu()
        
        elif game_state == PLAYING:
            # Update game
            player1.update(player2)
            if vs_bot:
                bot_ai()
            player2.update(player1)
            
            # Update camera scroll
            scroll[0] += (player1.rect.x - scroll[0] - WIDTH//2) * 0.1
            scroll[1] += (player1.rect.y - scroll[1] - HEIGHT//2) * 0.1
            
            # Keep scroll within bounds
            scroll[0] = max(0, min(scroll[0], WIDTH - 100))
            scroll[1] = max(0, min(scroll[1], HEIGHT - 100))
            
            # Check for game over
            if player1.health <= 0:
                game_state = GAME_OVER
                winner = 2
            elif player2.health <= 0:
                game_state = GAME_OVER
                winner = 1
            
            # Draw game
            screen.fill((50, 50, 50))
            pygame.draw.rect(screen, (100, 100, 100), (0, HEIGHT - 50, WIDTH, 50))
            
            if player1.rect.centery < player2.rect.centery:
                player1.draw(screen, scroll)
                player2.draw(screen, scroll)
            else:
                player2.draw(screen, scroll)
                player1.draw(screen, scroll)
            
            # Draw HUD
            font = pygame.font.SysFont(None, 36)
            p1_text = font.render(f"P1: {player1.health}", True, (255, 255, 255))
            p2_text = font.render(f"BOT: {player2.health}" if vs_bot else f"P2: {player2.health}", True, (255, 255, 255))
            screen.blit(p1_text, (20, 20))
            screen.blit(p2_text, (WIDTH - 100, 20))
            
            pygame_screen.blit(pygame.transform.scale(screen, (canvas.width, canvas.height)), (0, 0))
            pygame.display.flip()
        
        elif game_state == ONLINE_MATCHMAKING:
            screen.fill((30, 30, 40))
            font = pygame.font.SysFont(None, 48)
            
            # Animated dots
            dots = "." * ((pygame.time.get_ticks() // 500) % 4)
            
            waiting_text = font.render(f"Searching for opponent{dots}", True, (255, 255, 255))
            players_text = font.render(f"Online players: {online_players}", True, (200, 200, 255))
            cancel_text = font.render("Press ESC to cancel", True, (200, 200, 200))
            
            screen.blit(waiting_text, (WIDTH//2 - waiting_text.get_width()//2, 200))
            screen.blit(players_text, (WIDTH//2 - players_text.get_width()//2, 270))
            screen.blit(cancel_text, (WIDTH//2 - cancel_text.get_width()//2, 350))
            
            # In a real implementation, this would be handled by WebSocket events
            if pygame.time.get_ticks() > 5000:  # Simulate finding a match after 5 seconds
                game_state = PLAYING
                vs_bot = False
                create_online_players()
            
            pygame_screen.blit(pygame.transform.scale(screen, (canvas.width, canvas.height)), (0, 0))
            pygame.display.flip()
            
        elif game_state == ONLINE_PLAYING:
            # Similar to regular playing state but with network synchronization
            player1.update(player2)
            
            # Send input to server
            current_time = pygame.time.get_ticks()
            if current_time - last_sent_input.get('time', 0) > 50:  # Send 20 times per second
                keys = pygame.key.get_pressed()
                input_state = {
                    'left': keys[pygame.K_LEFT],
                    'right': keys[pygame.K_RIGHT],
                    'up': keys[pygame.K_UP],
                    'punch': keys[pygame.K_k],
                    'kick': keys[pygame.K_l]
                }
                if input_state != last_sent_input.get('state'):
                    send_ws_message('player_input', {
                        'match_id': match_id,
                        'input': input_state
                    })
                    last_sent_input = {'time': current_time, 'state': input_state}
            
            # Apply received input
            if last_received_input:
                player2.rect.x += (5 if last_received_input.get('right', False) else 0)
                player2.rect.x -= (5 if last_received_input.get('left', False) else 0)
                if last_received_input.get('up', False) and not player2.jump:
                    player2.jump = True
                    player2.vel_y = JUMP_STRENGTH
                
                if last_received_input.get('punch', False):
                    player2.attack('punch', player1)
                elif last_received_input.get('kick', False):
                    player2.attack('kick', player1)
            
            # Update camera and draw
            scroll[0] += (player1.rect.x - scroll[0] - WIDTH//2) * 0.1
            scroll[1] += (player1.rect.y - scroll[1] - HEIGHT//2) * 0.1
            
            screen.fill((50, 50, 50))
            pygame.draw.rect(screen, (100, 100, 100), (0, HEIGHT - 50, WIDTH, 50))
            
            if player1.rect.centery < player2.rect.centery:
                player1.draw(screen, scroll)
                player2.draw(screen, scroll)
            else:
                player2.draw(screen, scroll)
                player1.draw(screen, scroll)
            
            # Draw HUD with ping
            font = pygame.font.SysFont(None, 36)
            p1_text = font.render(f"YOU: {player1.health}", True, (255, 255, 255))
            p2_text = font.render(f"OPPONENT: {player2.health}", True, (255, 255, 255))
            ping_text = font.render("PING: 42ms", True, (200, 200, 200))
            
            screen.blit(p1_text, (20, 20))
            screen.blit(p2_text, (WIDTH - 200, 20))
            screen.blit(ping_text, (WIDTH//2 - ping_text.get_width()//2, 20))
            
            pygame_screen.blit(pygame.transform.scale(screen, (canvas.width, canvas.height)), (0, 0))
            pygame.display.flip()
            
            # Check for game over
            if player1.health <= 0 or player2.health <= 0:
                game_state = GAME_OVER
                winner = 2 if player1.health <= 0 else 1
                send_ws_message('game_over', {'match_id': match_id})
            
        elif game_state == GAME_OVER:
            draw_game_over(winner)
        
        clock.tick(60)

# Initialize networking
connect_to_server()

# Start the game
game_loop()
