import os
import pygame

def create_sprite_sheet(player_num, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Colors for the sprites
    colors = {
        'body': (200, 200, 200) if player_num == 1 else (200, 150, 150),
        'head': (255, 220, 180) if player_num == 1 else (180, 200, 220),
        'limbs': (150, 150, 150) if player_num == 1 else (150, 100, 100),
        'highlight': (230, 230, 230) if player_num == 1 else (230, 200, 200)
    }
    
    # Create idle animation frames
    for i in range(1, 3):
        surf = pygame.Surface((80, 120), pygame.SRCALPHA)
        
        # Body
        pygame.draw.ellipse(surf, colors['body'], (20, 40, 40, 80))
        
        # Head
        head_offset = 0 if i == 1 else 1
        pygame.draw.circle(surf, colors['head'], (40, 30 + head_offset), 20)
        
        # Limbs
        arm_offset = 0 if i == 1 else 2
        pygame.draw.line(surf, colors['limbs'], (40, 60), (20 + arm_offset, 90), 6)
        pygame.draw.line(surf, colors['limbs'], (40, 60), (60 - arm_offset, 90), 6)
        pygame.draw.line(surf, colors['limbs'], (40, 120), (20, 150), 8)
        pygame.draw.line(surf, colors['limbs'], (40, 120), (60, 150), 8)
        
        # Save
        pygame.image.save(surf, f"{output_dir}/idle{i}.png")
    
    # Create punch animation frames
    for i in range(1, 4):
        surf = pygame.Surface((100, 120), pygame.SRCALPHA)
        
        # Body
        pygame.draw.ellipse(surf, colors['body'], (30, 40, 40, 80))
        
        # Head
        pygame.draw.circle(surf, colors['head'], (50, 30), 20)
        
        # Limbs
        # Back arm (not punching)
        pygame.draw.line(surf, colors['limbs'], (50, 60), (30, 90), 6)
        
        # Punching arm
        punch_x = 50 + (i * 10)
        punch_y = 60 - (i * 2)
        pygame.draw.line(surf, colors['limbs'], (50, 60), (punch_x, punch_y), 6)
        pygame.draw.circle(surf, colors['head'], (punch_x + 5, punch_y), 8)
        
        # Legs
        pygame.draw.line(surf, colors['limbs'], (50, 120), (30, 150), 8)
        pygame.draw.line(surf, colors['limbs'], (50, 120), (70, 150), 8)
        
        # Save
        pygame.image.save(surf, f"{output_dir}/punch{i}.png")
    
    # Create kick animation frames
    for i in range(1, 4):
        surf = pygame.Surface((100, 140), pygame.SRCALPHA)
        
        # Body
        pygame.draw.ellipse(surf, colors['body'], (30, 40, 40, 80))
        
        # Head
        pygame.draw.circle(surf, colors['head'], (50, 30), 20)
        
        # Arms
        pygame.draw.line(surf, colors['limbs'], (50, 60), (30, 90), 6)
        pygame.draw.line(surf, colors['limbs'], (50, 60), (70, 90), 6)
        
        # Standing leg
        pygame.draw.line(surf, colors['limbs'], (50, 120), (40, 150), 8)
        
        # Kicking leg
        kick_x = 50 + (i * 8)
        kick_y = 120 - (i * 5)
        pygame.draw.line(surf, colors['limbs'], (50, 100), (kick_x, kick_y), 8)
        pygame.draw.circle(surf, colors['limbs'], (kick_x + 5, kick_y + 5), 8)
        
        # Save
        pygame.image.save(surf, f"{output_dir}/kick{i}.png")

if __name__ == "__main__":
    pygame.init()
    
    # Create sprites for both players
    create_sprite_sheet(1, "player1")
    create_sprite_sheet(2, "player2")
    
    print("Sprite sheets created successfully!")
