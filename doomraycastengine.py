import pygame
import math
import sys

# Initialize Pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 640, 480
HALF_HEIGHT = HEIGHT // 2
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2.5D Doom-Lookalike")
clock = pygame.time.Clock()
FPS = 60

# Field of view and raycasting settings
FOV = math.pi / 3        # 60 degrees field of view
HALF_FOV = FOV / 2
NUM_RAYS = WIDTH         # one ray per screen column
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 800          # maximum distance to check

# Map definition (a simple grid where '1' represents a wall)
world_map = [
    "111111111111",
    "1          1",
    "1   11     1",
    "1   11     1",
    "1          1",
    "1     11   1",
    "1     11   1",
    "1          1",
    "111111111111"
]
MAP_WIDTH = len(world_map[0])
MAP_HEIGHT = len(world_map)
TILE = 64  # size of each map block in pixels

# Player settings: starting position and viewing angle
player_x = TILE * 1.5
player_y = TILE * 1.5
player_angle = 0
move_speed = 5
rot_speed = 0.05

def cast_rays():
    """Casts rays from the player's position and draws vertical wall slices."""
    start_angle = player_angle - HALF_FOV
    for ray in range(NUM_RAYS):
        # Calculate current ray angle
        angle = start_angle + ray * DELTA_ANGLE
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        # Ray marching loop
        for depth in range(1, MAX_DEPTH):
            # Calculate target position along the ray
            target_x = player_x + depth * cos_a
            target_y = player_y + depth * sin_a

            # Determine which map square we're in
            map_x = int(target_x // TILE)
            map_y = int(target_y // TILE)

            # If outside the bounds, stop this ray
            if map_x < 0 or map_x >= MAP_WIDTH or map_y < 0 or map_y >= MAP_HEIGHT:
                break

            # If a wall is hit, render a vertical slice
            if world_map[map_y][map_x] == '1':
                # Correct for the fish-eye effect
                depth_corrected = depth * math.cos(player_angle - angle)
                # Calculate wall slice height (you can tweak the constant for scale)
                wall_height = min(HEIGHT, (TILE * 277) / (depth_corrected + 0.0001))
                # Adjust brightness based on distance (simple shading effect)
                color_intensity = 255 / (1 + depth_corrected * depth_corrected * 0.0001)
                color = (color_intensity, color_intensity, color_intensity)
                # Draw the vertical slice (one pixel wide)
                pygame.draw.rect(screen, color, (ray, HALF_HEIGHT - wall_height // 2, 1, wall_height))
                break

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # Player controls
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        player_angle -= rot_speed
    if keys[pygame.K_RIGHT]:
        player_angle += rot_speed
    if keys[pygame.K_UP]:
        player_x += move_speed * math.cos(player_angle)
        player_y += move_speed * math.sin(player_angle)
    if keys[pygame.K_DOWN]:
        player_x -= move_speed * math.cos(player_angle)
        player_y -= move_speed * math.sin(player_angle)

    # Clear screen and cast rays
    screen.fill((0, 0, 0))
    cast_rays()

    # Update the display and maintain frame rate
    pygame.display.flip()
    clock.tick(FPS)
