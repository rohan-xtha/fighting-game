import pygame
import sys
import math
import random
from js import document, window

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

# Create players
player1 = Fighter(200, HEIGHT - 200, 
                 {'left': pygame.K_a, 'right': pygame.K_d, 'up': pygame.K_w,
                  'punch': pygame.K_f, 'kick': pygame.K_g}, 'player1')

player2 = Fighter(800, HEIGHT - 200, 
                 {'left': pygame.K_LEFT, 'right': pygame.K_RIGHT, 'up': pygame.K_UP,
                  'punch': pygame.K_k, 'kick': pygame.K_l}, 'player2')

# Game loop
def game_loop():
    clock = pygame.time.Clock()
    scroll = [0, 0]
    
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
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    return
        
        update()
        draw()
        clock.tick(60)

# Start the game
game_loop()
