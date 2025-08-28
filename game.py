import pygame
import sys
import socket
import json
import threading
import time

# Constants
WIDTH, HEIGHT = 1000, 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAVITY = 0.8
JUMP_STRENGTH = -15
PLAYER_SPEED = 5

# Slow motion settings
SLOW_MO_FACTOR = 0.5  # 50% speed
MAX_SLOW_MO_FRAMES = 20  # Duration of slow motion in frames
slow_mo_timer = 0

# Create the game window
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shadow Fighters")
clock = pygame.time.Clock()

# Load and scale background image
background = pygame.image.load('background.jpg').convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

def load_animation_frames(base_path, action, frame_count, size=(80, 120)):
    """Load animation frames for a specific action"""
    frames = []
    for i in range(1, frame_count + 1):
        try:
            frame = pygame.image.load(f"{base_path}/{action}{i}.png").convert_alpha()
            frames.append(pygame.transform.scale(frame, size))
        except:
            # Create a colored rectangle as fallback
            surf = pygame.Surface(size, pygame.SRCALPHA)
            color = (255, 0, 0) if action == "punch" else (0, 0, 255) if action == "kick" else (200, 200, 200)
            pygame.draw.rect(surf, color, (0, 0, size[0], size[1]))
            frames.append(surf)
    return frames

class Fighter:
    def __init__(self, x, y, controls, image_file):
        # Load player image
        try:
            self.original_image = pygame.image.load(image_file).convert_alpha()
        except:
            # Create a placeholder if image fails to load
            self.original_image = pygame.Surface((80, 120), pygame.SRCALPHA)
            pygame.draw.rect(self.original_image, (200, 200, 200), (0, 0, 80, 120))
            
        self.image = pygame.transform.scale(self.original_image, (80, 120))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.jumping = False
        self.health = 100
        self.controls = controls
        self.facing_right = True if x < WIDTH // 2 else False
        self.attack_rect = pygame.Rect(0, 0, 60, 40)
        
        # Animation states
        self.current_action = "idle"
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.animation_cooldown = 0
        
        # Create animation frames
        self.animations = {
            "idle": self._create_animation_frames("idle", 2, (80, 120)),
            "punch": self._create_animation_frames("punch", 3, (100, 120)),
            "kick": self._create_animation_frames("kick", 3, (100, 140))
        }
        
        # Set initial image
        self.image = self.animations["idle"][0]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Attack properties
        self.is_attacking = False
        self.attack_frame_active = False

    def update_animation(self, other_player):
        """Update the current animation frame and handle attack logic"""
        global slow_mo_timer
        self.animation_cooldown += self.animation_speed
        
        # Update attack state based on current frame
        if self.current_action == "punch" and 1 <= int(self.animation_frame) < 2:
            self.attack_frame_active = True
            # Set attack hitbox
            self.attack_rect = pygame.Rect(
                self.rect.right if self.facing_right else self.rect.left - 60,
                self.rect.centery - 20,
                60, 40
            )
            # Check for hit
            if self.attack_rect.colliderect(other_player.rect) and not other_player.is_attacking:
                other_player.health = max(0, other_player.health - 2)  # Reduced from 5 to 2
                slow_mo_timer = MAX_SLOW_MO_FRAMES
        elif self.current_action == "kick" and 1 <= int(self.animation_frame) < 2:
            self.attack_frame_active = True
            # Set kick hitbox
            self.attack_rect = pygame.Rect(
                self.rect.right if self.facing_right else self.rect.left - 70,
                self.rect.centery - 20,
                70, 45
            )
            # Check for hit 
            if self.attack_rect.colliderect(other_player.rect) and not other_player.is_attacking:
                other_player.health = max(0, other_player.health - 3)  # Reduced from 8 to 3
                slow_mo_timer = MAX_SLOW_MO_FRAMES
        else:
            self.attack_frame_active = False
        
        # Update animation frame
        if self.animation_cooldown >= 1:
            self.animation_cooldown = 0
            self.animation_frame += 1
            
            # Check if animation is complete
            if self.current_action != "idle" and self.animation_frame >= len(self.animations[self.current_action]):
                self.current_action = "idle"
                self.animation_frame = 0
                self.is_attacking = False
    
    def move(self, other_player):
        global slow_mo_timer
        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()
        
        # Movement - only if not in the middle of an attack
        if self.current_action == "idle":
            if keys[self.controls['left']]:
                dx = -PLAYER_SPEED
                self.facing_right = False
            if keys[self.controls['right']]:
                dx = PLAYER_SPEED
                self.facing_right = True
                
        # Jumping
        if keys[self.controls['up']] and not self.jumping and self.current_action == "idle":
            self.vel_y = JUMP_STRENGTH
            self.jumping = True
            
        # Apply gravity
        self.vel_y += GRAVITY
        dy += self.vel_y
        
        # Handle attacks
        if self.current_action == "idle":
            if keys[self.controls['punch']]:
                self.current_action = "punch"
                self.animation_frame = 0
                self.is_attacking = True
            elif keys[self.controls['kick']]:
                self.current_action = "kick"
                self.animation_frame = 0
                self.is_attacking = True
        
        # Update position with collision detection
        if 0 <= self.rect.x + dx <= WIDTH - self.rect.width:
            self.rect.x += dx
            
        # Ground collision
        if self.rect.bottom + dy > HEIGHT - 50:
            self.rect.bottom = HEIGHT - 50
            self.vel_y = 0
            self.jumping = False
        else:
            self.rect.y += dy
            
        # Update animation
        self.update_animation(other_player)

    def _create_animation_frames(self, action, frame_count, size):
        """Create animation frames for a specific action"""
        frames = []
        player_folder = 'player1' if '1' in str(type(self)) else 'player2'
        
        try:
            # Try to load the actual sprite frames
            for i in range(1, frame_count + 1):
                frame_path = f"{player_folder}/{action}{i}.png"
                frame = pygame.image.load(frame_path).convert_alpha()
                frame = pygame.transform.scale(frame, size)
                frames.append(frame)
        except Exception as e:
            print(f"Error loading {action} frames: {e}")
            # Fallback to simple colored rectangles if loading fails
            for i in range(frame_count):
                frame = pygame.Surface(size, pygame.SRCALPHA)
                color = (255, 0, 0) if '1' in player_folder else (0, 0, 255)
                pygame.draw.rect(frame, color, (0, 0, size[0], size[1]))
                frames.append(frame)
                
        return frames
        
    def draw(self, surface):
        # Get the current animation frame
        frame_index = int(self.animation_frame) % len(self.animations[self.current_action])
        current_frame = self.animations[self.current_action][frame_index].copy()
        
        # Flip the frame if facing left
        if not self.facing_right:
            current_frame = pygame.transform.flip(current_frame, True, False)
            
        # Draw the current frame
        draw_rect = current_frame.get_rect(midbottom=self.rect.midbottom)
        surface.blit(current_frame, draw_rect)
        
        # Draw health bar
        health_bar_width = 80
        health_ratio = self.health / 100
        health_bar = pygame.Rect(self.rect.x, self.rect.y - 15, health_bar_width * health_ratio, 5)
        health_bar_outline = pygame.Rect(self.rect.x, self.rect.y - 15, health_bar_width, 5)
        pygame.draw.rect(surface, (255, 0, 0), health_bar)
        pygame.draw.rect(surface, (255, 255, 255), health_bar_outline, 1)
    
    # Health text is now handled by draw_health_bars()

def draw_ground():
    pygame.draw.rect(screen, (50, 50, 50), (0, HEIGHT - 50, WIDTH, 50))

def draw_controls():
    font = pygame.font.SysFont('Arial', 24, bold=True)
    controls1 = font.render("P1: WASD - Move | F - Punch | G - Kick", True, WHITE)
    controls2 = font.render("P2: Arrows - Move | K - Punch | L - Kick", True, WHITE)
    # Position controls at the bottom with more padding
    screen.blit(controls1, (20, HEIGHT - 40))
    screen.blit(controls2, (WIDTH - 400, HEIGHT - 40))

# Add these at the top with other variables
global p1_health_smooth, p2_health_smooth, p1_health_prev, p2_health_prev
if 'p1_health_smooth' not in globals():
    p1_health_smooth = 100.0
    p2_health_smooth = 100.0
    p1_health_prev = 100
    p2_health_prev = 100

def draw_health_bars():
    global p1_health_smooth, p2_health_smooth, p1_health_prev, p2_health_prev
    
    # Smooth health decrease effect
    smooth_speed = 0.2
    p1_health_smooth += (player1.health - p1_health_smooth) * smooth_speed
    p2_health_smooth += (player2.health - p2_health_smooth) * smooth_speed
    
    # Flash white when taking damage
    p1_flash = abs(player1.health - p1_health_prev) > 0.1
    p2_flash = abs(player2.health - p2_health_prev) > 0.1
    
    # Update previous health values
    p1_health_prev = player1.health
    p2_health_prev = player2.health
    
    # Draw health bar backgrounds with flash effect
    bg_color1 = (255, 200, 200) if p1_flash else (80, 0, 0)
    bg_color2 = (255, 200, 200) if p2_flash else (80, 0, 0)
    
    # P1 Health Bar
    pygame.draw.rect(screen, bg_color1, (50, 20, 400, 30))  # Background with flash
    
    # P1 Health gradient
    health_ratio1 = player1.health / 100.0
    for i in range(int(400 * health_ratio1)):
        # Gradient from green to yellow to red
        if health_ratio1 > 0.5:
            g = 255
            r = int(510 * (1 - health_ratio1))
        else:
            r = 255
            g = int(510 * health_ratio1)
        color = (r, g, 0)
        pygame.draw.rect(screen, color, (50 + i, 20, 1, 30))
    
    # P1 Smooth damage indicator (white)
    pygame.draw.rect(screen, (255, 255, 255, 100), 
                    (50 + 400 * (p1_health_smooth/100.0), 20, 
                     400 * ((100 - p1_health_smooth)/100.0), 30))
    
    # P2 Health Bar
    pygame.draw.rect(screen, bg_color2, (WIDTH - 450, 20, 400, 30))  # Background with flash
    
    # P2 Health gradient
    health_ratio2 = player2.health / 100.0
    for i in range(int(400 * health_ratio2)):
        # Gradient from green to yellow to red
        if health_ratio2 > 0.5:
            g = 255
            r = int(510 * (1 - health_ratio2))
        else:
            r = 255
            g = int(510 * health_ratio2)
        color = (r, g, 0)
        pygame.draw.rect(screen, color, (WIDTH - 450 + i, 20, 1, 30))
    
    # P2 Smooth damage indicator (white)
    pygame.draw.rect(screen, (255, 255, 255, 100), 
                    (WIDTH - 450 + 400 * (p2_health_smooth/100.0), 20, 
                     400 * ((100 - p2_health_smooth)/100.0), 30))
    
    # Draw health bar borders with glow effect
    border_color1 = (255, 255, 255, 200) if p1_flash else WHITE
    border_color2 = (255, 255, 255, 200) if p2_flash else WHITE
    
    # Glow effect
    for i in range(1, 4):
        glow_surf = pygame.Surface((400 + i*4, 30 + i*4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*border_color1[:3], 50//i), (0, 0, 400 + i*4, 30 + i*4), 2)
        screen.blit(glow_surf, (50 - i*2, 20 - i*2))
        
        glow_surf = pygame.Surface((400 + i*4, 30 + i*4), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*border_color2[:3], 50//i), (0, 0, 400 + i*4, 30 + i*4), 2)
        screen.blit(glow_surf, (WIDTH - 450 - i*2, 20 - i*2))
    
    # Draw borders
    pygame.draw.rect(screen, border_color1, (50, 20, 400, 30), 2)  # P1 border
    pygame.draw.rect(screen, border_color2, (WIDTH - 450, 20, 400, 30), 2)  # P2 border
    
    # Draw player labels with glow
    font = pygame.font.SysFont('Arial', 24, bold=True)
    
    # P1 Label with glow
    p1_text = font.render("P1", True, (255, 255, 255, 200))
    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        screen.blit(p1_text, (10 + dx, 20 + dy))
    screen.blit(p1_text, (10, 20))
    
    # P2 Label with glow
    p2_text = font.render("P2", True, (255, 255, 255, 200))
    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        screen.blit(p2_text, (WIDTH - 30 + dx, 20 + dy))
    screen.blit(p2_text, (WIDTH - 30, 20))

def check_winner():
    if player1.health <= 0:
        return "Player 2 Wins!"
    elif player2.health <= 0:
        return "Player 1 Wins!"
    return None

def reset_game():
    player1.rect.x = 200
    player1.rect.y = HEIGHT - 150
    player1.health = 100
    player2.rect.x = 700
    player2.rect.y = HEIGHT - 150
    player2.health = 100

def draw_game(winner, game_over):
    # Draw background
    screen.blit(background, (0, 0))
    
    # Draw ground
    draw_ground()
    
    # Draw players
    player1.draw(screen)
    player2.draw(screen)
    
    # Draw UI
    draw_health_bars()
    draw_controls()
    
    # Draw game over message
    if game_over:
        font = pygame.font.SysFont('Arial', 72, bold=True)
        text = font.render(winner, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(text, text_rect)
        
        font = pygame.font.SysFont('Arial', 36)
        restart_text = font.render("Press R to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 80))
        screen.blit(restart_text, restart_rect)
    
    pygame.display.flip()

# Create players
player1 = Fighter(200, HEIGHT - 170,  # Adjusted Y position for better ground alignment
                 {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w,
                  'punch': pygame.K_f, 'kick': pygame.K_g}, 'player1/idle1.png')
player2 = Fighter(WIDTH - 300, HEIGHT - 170,  # Adjusted Y position for better ground alignment
                 {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP,
                  'punch': pygame.K_k, 'kick': pygame.K_l}, 'player2/idle1.png')

# Network client
client = None
try:
    from client import NetworkClient
    client = NetworkClient(host='localhost', port=5555)
    if not client.connect():
        print("Failed to connect to server. Starting in offline mode.")
        client = None
except Exception as e:
    print(f"Error initializing network: {e}")
    client = None

def main():
    running = True
    game_over = False
    winner = None
    
    while running:
        clock.tick(FPS)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game_over and event.key == pygame.K_r:
                    reset_game()
                    game_over = False
                    winner = None
        
        if not game_over:
            # Update players
            if client and hasattr(client, 'game_state'):
                p1_state = client.game_state.get('players', {}).get('player1', {})
                p2_state = client.game_state.get('players', {}).get('player2', {})
                
                player1.rect.x = p1_state.get('x', 200)
                player1.rect.y = p1_state.get('y', 0)
                player1.health = p1_state.get('health', 100)
                player1.facing_right = p1_state.get('facing_right', True)
                player1.is_attacking = p1_state.get('is_attacking', False)
                
                player2.rect.x = p2_state.get('x', 800)
                player2.rect.y = p2_state.get('y', 0)
                player2.health = p2_state.get('health', 100)
                player2.facing_right = p2_state.get('facing_right', False)
                player2.is_attacking = p2_state.get('is_attacking', False)
            else:
                player1.move(player2)
                player2.move(player1)
            
            # Check for winner
            winner = check_winner()
            if winner:
                game_over = True
        
        # Draw everything
        draw_game(winner, game_over)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
