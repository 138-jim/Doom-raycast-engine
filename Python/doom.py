import pygame
import numpy as np
import math
import random
import time
import os
from pygame import Surface, surfarray
from pygame.pixelarray import PixelArray
from pygame.locals import *
from pygame import mixer
import heapq
from collections import deque
from enum import Enum

# Try to import numba, but provide fallback if not available
try:
    from numba import njit, jit, prange
    NUMBA_AVAILABLE = True
    print("Numba is available! Using JIT acceleration.")
except ImportError:
    print("Numba not found. Using fallback implementations.")
    NUMBA_AVAILABLE = False
    # Define dummy decorators that do nothing
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def jit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    
    def prange(*args):
        return range(*args)

# Constants and Configuration
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FOV = 60  # Field of view in degrees
HALF_FOV = FOV / 2
MAX_DEPTH = 20  # Maximum rendering distance
TILE_SIZE = 64
PLAYER_SIZE = 10
RAY_COUNT = 200  # Number of rays to cast (resolution)
WALL_HEIGHT = 50
WALL_STRIP_WIDTH = math.ceil(SCREEN_WIDTH / RAY_COUNT)  # Ensure no gaps between strips

# Weapon settings
WEAPON_IDLE_POS = 0

# Weapon configurations for different weapon types
WEAPON_CONFIGS = {
    'pistol': {
        'name': 'PISTOL',
        'max_ammo': 12,
        'damage': 1,
        'fire_cooldown': 20,
        'reload_time': 150,
        'recoil': 10,
        'recoil_recovery': 0.08,
        'spread': 0,  # No spread
        'pellets': 1,  # Single bullet
        'auto': False  # Semi-automatic
    },
    'shotgun': {
        'name': 'SHOTGUN',
        'max_ammo': 8,
        'damage': 1,
        'fire_cooldown': 40,
        'reload_time': 200,
        'recoil': 25,
        'recoil_recovery': 0.06,
        'spread': 0.15,  # Wide spread angle
        'pellets': 5,  # 5 pellets per shot
        'auto': False
    },
    'rifle': {
        'name': 'RIFLE',
        'max_ammo': 30,
        'damage': 1,
        'fire_cooldown': 8,
        'reload_time': 180,
        'recoil': 6,
        'recoil_recovery': 0.12,
        'spread': 0.05,  # Slight spread
        'pellets': 1,
        'auto': True  # Fully automatic
    }
}

# Legacy constants for backwards compatibility
WEAPON_RECOIL = 10
WEAPON_RECOIL_RECOVERY_SPEED = 0.08
WEAPON_FIRE_COOLDOWN = 20  # frames
WEAPON_MAX_AMMO = 12
WEAPON_RELOAD_TIME = 150  # frames

# Enemy settings
ENEMY_SIZE = 20
ENEMY_SPEED = 0.08
ENEMY_HP = 3
ENEMY_DAMAGE = 10
ENEMY_ATTACK_RANGE = 1.5
ENEMY_ATTACK_COOLDOWN = 60  # frames
MAX_ENEMIES = 5
ENEMY_SPAWN_COOLDOWN = 100  # frames
PATH_UPDATE_FREQUENCY = 10  # Update path every N frames
MAX_PATH_LENGTH = 100       # Maximum nodes in path to prevent excessive computation

# Performance settings
WALL_HEIGHT_LIMIT = SCREEN_HEIGHT * 2.5  # Maximum wall height to prevent excessive rendering
LOD_ENABLED = True                       # Level of Detail for close walls/sprites
MAX_SPRITE_SIZE = SCREEN_HEIGHT * 1.2    # Maximum size for enemy sprites
MINIMUM_WALL_DISTANCE = 0.1              # Prevent division by zero and extreme wall heights
RENDER_DISTANCE_CLOSE = 1.0              # Distance threshold for close rendering
RENDER_DISTANCE_MID = 3.0                # Distance threshold for medium rendering

# Player health settings
PLAYER_MAX_HEALTH = 100

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)

# Pre-calculate values for optimization
FOV_RAD = math.radians(FOV)
HALF_FOV_RAD = math.radians(HALF_FOV)
ANGLE_STEP = FOV_RAD / RAY_COUNT

# Create a simple map (0 = empty, 1 = wall)
MAP = [
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 1],
[1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
[1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
[1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1],
[1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
[1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
[1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1],
[1, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)

# Create the A* pathfinding implementation
class PathNode:
    def __init__(self, x, y, parent=None):
        self.x = x
        self.y = y
        self.parent = parent
        self.g = 0  # Cost from start to this node
        self.h = 0  # Heuristic (estimated cost to goal)
        self.f = 0  # Total cost (g + h)
    
    def __lt__(self, other):
        # Comparison for priority queue
        return self.f < other.f
    
    def __eq__(self, other):
        # Check if two nodes are the same position
        return self.x == other.x and self.y == other.y

# Implement A* pathfinding algorithm
def a_star_pathfinding(start_x, start_y, goal_x, goal_y, max_iterations=1000):
    # Convert to grid coordinates
    start_grid_x, start_grid_y = int(start_x / TILE_SIZE), int(start_y / TILE_SIZE)
    goal_grid_x, goal_grid_y = int(goal_x / TILE_SIZE), int(goal_y / TILE_SIZE)
    
    # Check if start or goal is in a wall
    if MAP[start_grid_y][start_grid_x] != 0 or MAP[goal_grid_y][goal_grid_x] != 0:
        return []  # No valid path possible
    
    # Define movement directions (including diagonals)
    directions = [
        (0, -1),   # up
        (1, -1),   # up-right
        (1, 0),    # right
        (1, 1),    # down-right
        (0, 1),    # down
        (-1, 1),   # down-left
        (-1, 0),   # left
        (-1, -1),  # up-left
    ]
    
    # Initialize open and closed lists
    open_list = []
    closed_set = set()
    
    # Create start and end nodes
    start_node = PathNode(start_grid_x, start_grid_y)
    goal_node = PathNode(goal_grid_x, goal_grid_y)
    
    # Calculate heuristic for start node
    start_node.h = abs(start_node.x - goal_node.x) + abs(start_node.y - goal_node.y)
    start_node.f = start_node.h
    
    # Add start node to open list
    heapq.heappush(open_list, start_node)
    
    iterations = 0
    
    # Main loop
    while open_list and iterations < max_iterations:
        iterations += 1
        
        # Get node with lowest f score from open list
        current_node = heapq.heappop(open_list)
        
        # Check if reached goal
        if current_node.x == goal_node.x and current_node.y == goal_node.y:
            # Reconstruct path
            path = []
            while current_node:
                # Convert back to world coordinates (center of tile)
                path.append((current_node.x * TILE_SIZE + TILE_SIZE/2, 
                             current_node.y * TILE_SIZE + TILE_SIZE/2))
                current_node = current_node.parent
            return path[::-1]  # Return reversed path (start to goal)
        
        # Add current node to closed set
        closed_set.add((current_node.x, current_node.y))
        
        # Check all adjacent nodes
        for dx, dy in directions:
            # Calculate new position
            new_x, new_y = current_node.x + dx, current_node.y + dy
            
            # Check if valid position (within map bounds and not a wall)
            if (0 <= new_x < MAP_WIDTH and 0 <= new_y < MAP_HEIGHT and 
                MAP[new_y][new_x] == 0 and (new_x, new_y) not in closed_set):
                
                # Create neighbor node
                neighbor = PathNode(new_x, new_y, current_node)
                
                # Calculate g score (cost from start to this node)
                # Diagonal movement costs more
                if dx != 0 and dy != 0:
                    # Check if diagonal path is blocked by walls (to prevent cutting corners)
                    if MAP[current_node.y][new_x] != 0 or MAP[new_y][current_node.x] != 0:
                        continue
                    neighbor.g = current_node.g + 1.414  # √2 for diagonal movement
                else:
                    neighbor.g = current_node.g + 1
                
                # Calculate h score (heuristic - estimated cost to goal)
                # Using Manhattan distance (abs(x1-x2) + abs(y1-y2))
                neighbor.h = abs(neighbor.x - goal_node.x) + abs(neighbor.y - goal_node.y)
                
                # Calculate f score (total cost)
                neighbor.f = neighbor.g + neighbor.h
                
                # Check if node is already in open list with better score
                better_node_exists = False
                for idx, open_node in enumerate(open_list):
                    if open_node == neighbor and open_node.g <= neighbor.g:
                        better_node_exists = True
                        break
                
                if not better_node_exists:
                    heapq.heappush(open_list, neighbor)
    
    # No path found
    return []

# Fast bulk texture rendering for walls
def render_textured_column(color_array, texture_column, tex_step, tex_start_pos, height, shade):
    """Fill a color array with texture data in one operation"""
    # Early exit for invalid heights
    if height <= 0:
        return
        
    # Start texture position
    tex_position = tex_start_pos
    
    # Get the mask for texture index wrap-around
    tile_mask = TILE_SIZE - 1
    
    # For very tall walls (close distances), use LOD to skip pixels
    # This improves performance significantly when close to walls
    if height > SCREEN_HEIGHT:
        # Calculate how many pixels to skip (adaptive LOD)
        skip_factor = max(1, height // SCREEN_HEIGHT)
        
        # Only process every nth pixel and duplicate
        for y in range(0, height, skip_factor):
            # Get texture Y coordinate efficiently
            tex_y = int(tex_position) & tile_mask
            tex_position += tex_step * skip_factor
            
            # Get texture color and apply shade
            color = texture_column[tex_y]
            
            # Calculate shaded color once
            r = int(color[0] * shade)
            g = int(color[1] * shade)
            b = int(color[2] * shade)
            
            # Fill multiple pixels at once (duplicating the same color)
            for i in range(min(skip_factor, height - y)):
                if y + i < height:  # Safety check
                    color_array[y + i][0] = r
                    color_array[y + i][1] = g
                    color_array[y + i][2] = b
    else:
        # Normal rendering for regular height walls
        for y in range(height):
            # Get texture Y coordinate efficiently
            tex_y = int(tex_position) & tile_mask
            tex_position += tex_step
            
            # Get texture color and apply shade
            color = texture_column[tex_y]
            
            # Set pixel directly in array - avoid function calls
            color_array[y][0] = int(color[0] * shade)
            color_array[y][1] = int(color[1] * shade)
            color_array[y][2] = int(color[2] * shade)
    
    return color_array

# Load and prepare textures with height precalculation
def load_textures():
    # Create basic texture patterns for walls
    # Brick texture - create higher contrast, more solid looking bricks
    brick = pygame.Surface((TILE_SIZE, TILE_SIZE))
    brick.fill((140, 50, 30))  # Darker, richer red for base
    
    # Create more defined brick pattern
    for y in range(0, TILE_SIZE, 8):
        for x in range(0, TILE_SIZE, 16):
            offset = 8 if y % 16 == 0 else 0
            # Make the mortar thinner and more defined
            pygame.draw.rect(brick, (190, 100, 60), (x + offset+1, y+1, 7, 3))
            
            # Add subtle brick texture/variations
            if random.random() > 0.7:
                shade = random.randint(-20, 20)
                brick_color = (min(255, max(0, 190+shade)), 
                               min(255, max(0, 100+shade//2)), 
                               min(255, max(0, 60+shade//3)))
                pygame.draw.rect(brick, brick_color, (x + offset+2, y+2, 5, 1))
    
    # Stone texture - more defined and varied
    stone = pygame.Surface((TILE_SIZE, TILE_SIZE))
    stone.fill((70, 70, 70))  # Darker base for contrast
    
    # Draw stones with better definition and variation
    for y in range(0, TILE_SIZE, 8):
        for x in range(0, TILE_SIZE, 8):
            shade = random.randint(70, 120)
            # Add subtle variation to each stone block
            stone_color = (shade, shade, shade+random.randint(-10, 10))
            pygame.draw.rect(stone, stone_color, (x, y, 7, 7))
            
            # Add highlights/shadows to create more depth
            edge_shade = max(30, shade-40)
            pygame.draw.line(stone, (edge_shade, edge_shade, edge_shade), 
                           (x, y+7), (x+7, y+7))
            pygame.draw.line(stone, (edge_shade, edge_shade, edge_shade), 
                           (x+7, y), (x+7, y+7))
            
            # Add subtle crack or texture detail to some blocks
            if random.random() > 0.8:
                detail_shade = min(200, shade+30)
                pygame.draw.line(stone, (detail_shade, detail_shade, detail_shade), 
                               (x+1, y+1), (x+3, y+3))
    
    # Create texture list without complex array handling
    textures = [brick, stone]
    
    return textures

# Create a gun class to handle weapon logic
class Gun:
    def __init__(self, weapon_type='pistol'):
        self.weapon_type = weapon_type
        self.config = WEAPON_CONFIGS[weapon_type]

        self.recoil = 0
        self.firing = False
        self.cooldown = 0
        self.flash_duration = 0
        self.ammo = self.config['max_ammo']
        self.reloading = False
        self.reload_timer = 0
        self.hit_data = []  # Store hit information for spread weapons

        # Load weapon graphics
        self.weapon_image = self.create_weapon_image()
        self.muzzle_flash = self.create_muzzle_flash()

        # Load sound effects
        mixer.init()
        self.sound_fire = mixer.Sound(os.path.join("sounds", "gun_fire.wav"))
        self.sound_empty = mixer.Sound(os.path.join("sounds", "gun_empty.wav"))
        self.sound_reload = mixer.Sound(os.path.join("sounds", "gun_reload.wav"))

        # Set volume
        self.sound_fire.set_volume(0.3)
        self.sound_empty.set_volume(0.3)
        self.sound_reload.set_volume(0.3)
    
    def create_weapon_image(self):
        # Create weapon image based on type
        gun_surface = Surface((150, 120), pygame.SRCALPHA)

        if self.weapon_type == 'pistol':
            # Pistol - compact handgun
            pygame.draw.rect(gun_surface, (50, 50, 50), (60, 20, 40, 10))  # Barrel
            pygame.draw.rect(gun_surface, (70, 70, 70), (40, 30, 70, 40))  # Body
            pygame.draw.rect(gun_surface, (60, 60, 60), (50, 70, 50, 30))  # Lower body
            pygame.draw.rect(gun_surface, (80, 50, 30), (60, 70, 30, 50))  # Handle
            pygame.draw.rect(gun_surface, (100, 100, 100), (45, 35, 60, 10))  # Details
            pygame.draw.rect(gun_surface, (30, 30, 30), (95, 25, 10, 5))  # Sight

        elif self.weapon_type == 'shotgun':
            # Shotgun - wider barrel, pump action
            pygame.draw.rect(gun_surface, (40, 40, 40), (50, 15, 60, 18))  # Wide barrel
            pygame.draw.rect(gun_surface, (35, 35, 35), (70, 33, 20, 8))  # Pump
            pygame.draw.rect(gun_surface, (60, 60, 60), (30, 35, 80, 45))  # Body
            pygame.draw.rect(gun_surface, (50, 50, 50), (40, 80, 60, 25))  # Lower receiver
            pygame.draw.rect(gun_surface, (70, 45, 25), (55, 80, 30, 40))  # Wooden stock
            pygame.draw.rect(gun_surface, (90, 90, 90), (35, 40, 70, 12))  # Top rail
            pygame.draw.rect(gun_surface, (25, 25, 25), (105, 20, 8, 8))  # Front sight

        elif self.weapon_type == 'rifle':
            # Rifle - long barrel, tactical look
            pygame.draw.rect(gun_surface, (45, 45, 45), (50, 18, 70, 12))  # Long barrel
            pygame.draw.rect(gun_surface, (55, 55, 55), (25, 30, 90, 35))  # Body
            pygame.draw.rect(gun_surface, (50, 50, 50), (35, 65, 70, 30))  # Lower receiver
            pygame.draw.rect(gun_surface, (65, 40, 30), (50, 75, 40, 45))  # Stock
            pygame.draw.rect(gun_surface, (80, 80, 80), (30, 35, 80, 8))  # Top rail
            pygame.draw.rect(gun_surface, (100, 100, 100), (60, 33, 30, 4))  # Scope mount
            pygame.draw.rect(gun_surface, (30, 30, 30), (115, 22, 6, 6))  # Front sight
            pygame.draw.rect(gun_surface, (40, 40, 40), (80, 60, 25, 8))  # Magazine

        return gun_surface
    
    def create_muzzle_flash(self):
        # Create a muzzle flash effect
        flash_surface = Surface((60, 40), pygame.SRCALPHA)
        
        # Yellow-orange circular flash
        pygame.draw.circle(flash_surface, (255, 220, 130, 200), (20, 20), 20)
        pygame.draw.circle(flash_surface, (255, 160, 50, 170), (30, 20), 15)
        
        # Random spark lines
        for _ in range(5):
            start_x = 30
            start_y = 20
            end_x = start_x + random.randint(10, 30)
            end_y = start_y + random.randint(-15, 15)
            pygame.draw.line(flash_surface, (255, 255, 200), 
                           (start_x, start_y), (end_x, end_y), 2)
        
        return flash_surface
    
    def fire(self):
        if self.cooldown == 0 and not self.reloading:
            if self.ammo > 0:
                # Trigger recoil using weapon config
                self.recoil = self.config['recoil']
                self.firing = True
                self.cooldown = self.config['fire_cooldown']
                self.flash_duration = 4

                # Reduce ammo
                self.ammo -= 1

                # Generate spread pattern for multiple pellets (shotgun)
                self.hit_data = []
                for i in range(self.config['pellets']):
                    # Calculate spread offset for this pellet
                    if self.config['spread'] > 0:
                        spread_angle = random.uniform(-self.config['spread'], self.config['spread'])
                    else:
                        spread_angle = 0
                    self.hit_data.append({
                        'angle_offset': spread_angle,
                        'damage': self.config['damage']
                    })

                # Play sound
                self.sound_fire.play()

                return True
            else:
                # Empty gun click
                self.sound_empty.play()
                self.cooldown = self.config['fire_cooldown'] // 2  # Shorter cooldown for empty

                return False
        return False
    
    def reload(self):
        if not self.reloading and self.ammo < self.config['max_ammo']:
            self.reloading = True
            self.reload_timer = self.config['reload_time']
            self.sound_reload.play()

    def update(self):
        # Handle recoil recovery using weapon config
        if self.recoil > 0:
            self.recoil -= self.config['recoil_recovery']
            if self.recoil < 0:
                self.recoil = 0

        # Handle cooldown
        if self.cooldown > 0:
            self.cooldown -= 1
            if self.cooldown == 0:
                self.firing = False
                self.hit_data = []  # Clear hit data when firing ends

        # Handle muzzle flash
        if self.flash_duration > 0:
            self.flash_duration -= 1

        # Handle reloading
        if self.reloading:
            self.reload_timer -= 1
            if self.reload_timer <= 0:
                self.ammo = self.config['max_ammo']
                self.reloading = False
    
    def draw(self, screen):
        # Calculate position with recoil
        weapon_width = self.weapon_image.get_width()
        weapon_height = self.weapon_image.get_height()
        weapon_x = SCREEN_WIDTH // 2 - weapon_width // 2
        weapon_y = SCREEN_HEIGHT - weapon_height + int(self.recoil)

        # Draw weapon
        screen.blit(self.weapon_image, (weapon_x, weapon_y))

        # Draw muzzle flash when firing
        if self.flash_duration > 0:
            flash_x = weapon_x + 100
            flash_y = weapon_y + 25
            screen.blit(self.muzzle_flash, (flash_x, flash_y))

        # Draw weapon name and ammo counter
        font = pygame.font.SysFont(None, 30)
        weapon_name_text = font.render(self.config['name'], True, (255, 255, 100))
        screen.blit(weapon_name_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 90))

        ammo_text = font.render(f"AMMO: {self.ammo}/{self.config['max_ammo']}", True, (255, 255, 255))
        screen.blit(ammo_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 60))

        # Show reloading text
        if self.reloading:
            reload_text = font.render("RELOADING...", True, (255, 200, 50))
            screen.blit(reload_text, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30))

        # Show weapon switch hint
        hint_font = pygame.font.SysFont(None, 20)
        hint_text = hint_font.render("1: PISTOL  2: SHOTGUN  3: RIFLE", True, (150, 150, 150))
        screen.blit(hint_text, (10, SCREEN_HEIGHT - 25))

# Player class
class Player:
    def __init__(self, x, y, angle=0):
        self.x = x * TILE_SIZE + TILE_SIZE / 2
        self.y = y * TILE_SIZE + TILE_SIZE / 2
        self.angle = angle
        self.movement_speed = 5
        self.rotation_speed = 3
        self.mouse_sensitivity = 0.2  # Lower values for less sensitive mouse movement
        self.health = PLAYER_MAX_HEALTH
        self.hit_effect = 0  # For red flash when hit
        self.score = 0

    def take_damage(self, damage):
        self.health -= damage
        self.hit_effect = 10  # Duration of red effect
        return self.health <= 0  # Return True if player is dead

    def update(self, keys, mouse_dx=0):
        # Mouse rotation - mouse_dx is the horizontal mouse movement since last frame
        self.angle += mouse_dx * self.mouse_sensitivity
        
        # Keep the arrow key rotation as a backup control method
        if keys[pygame.K_LEFT]:
            self.angle -= self.rotation_speed
        if keys[pygame.K_RIGHT]:
            self.angle += self.rotation_speed
        
        # Normalize angle to 0-360 degrees
        self.angle %= 360
        
        # Convert angle to radians for movement calculation
        rad_angle = math.radians(self.angle)
        
        # Forward and backward movement
        dx, dy = 0, 0
        if keys[pygame.K_w]:  # Forward
            dx = math.cos(rad_angle) * self.movement_speed
            dy = math.sin(rad_angle) * self.movement_speed
        if keys[pygame.K_s]:  # Backward
            dx = -math.cos(rad_angle) * self.movement_speed
            dy = -math.sin(rad_angle) * self.movement_speed
        
        # Strafing left and right
        if keys[pygame.K_a]:  # Left strafe
            dx = math.cos(rad_angle - math.pi/2) * self.movement_speed
            dy = math.sin(rad_angle - math.pi/2) * self.movement_speed
        if keys[pygame.K_d]:  # Right strafe
            dx = math.cos(rad_angle + math.pi/2) * self.movement_speed
            dy = math.sin(rad_angle + math.pi/2) * self.movement_speed
        
        # Check collision before moving
        new_x = self.x + dx
        new_y = self.y + dy
        
        # Check if the new position is inside a wall
        map_x = int(new_x / TILE_SIZE)
        map_y = int(new_y / TILE_SIZE)
        
        # Make sure we're within map bounds
        if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
            # If the new position is not in a wall, move there
            if MAP[map_y][map_x] == 0:
                self.x = new_x
                self.y = new_y
        
        # Update hit effect
        if self.hit_effect > 0:
            self.hit_effect -= 1


    def draw(self, screen):
        # Draw player on 2D minimap
        pygame.draw.circle(screen, RED, (int(self.x / TILE_SIZE * 10), 
                                        int(self.y / TILE_SIZE * 10)), 3)
        
        # Draw direction line
        line_length = 10
        end_x = self.x / TILE_SIZE * 10 + math.cos(math.radians(self.angle)) * line_length
        end_y = self.y / TILE_SIZE * 10 + math.sin(math.radians(self.angle)) * line_length
        pygame.draw.line(screen, RED, 
                         (int(self.x / TILE_SIZE * 10), int(self.y / TILE_SIZE * 10)),
                         (int(end_x), int(end_y)), 1)

# Modify the Enemy class to use pathfinding
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.hp = ENEMY_HP
        self.attack_cooldown = 0
        self.hit_effect = 0  # Visual indicator when hit
        self.sprites = create_enemy_sprite()  # Create sprites with different angles
        self.current_sprite_idx = 0  # Default to front-facing
        
        # Pathfinding attributes
        self.path = []
        self.path_update_counter = 0
        self.current_path_index = 0
        self.angle = 0  # Direction enemy is facing
        
    def update(self, player):
        # Calculate direction to player
        dx = player.x - self.x
        dy = player.y - self.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Calculate angle to player for sprite selection
        self.angle = math.degrees(math.atan2(dy, dx))
        
        # Don't move if hit recently
        if self.hit_effect > 0:
            self.hit_effect -= 1
            return False  # Not attacking
        
        # Update pathfinding
        self.path_update_counter += 1
        if self.path_update_counter >= PATH_UPDATE_FREQUENCY or not self.path:
            self.path = a_star_pathfinding(self.x, self.y, player.x, player.y)
            self.path_update_counter = 0
            self.current_path_index = 0
            
            # Limit path length to prevent excessive computation
            if len(self.path) > MAX_PATH_LENGTH:
                self.path = self.path[:MAX_PATH_LENGTH]
        
        # Move along path if available
        if self.path and self.current_path_index < len(self.path) and distance > TILE_SIZE * 0.8:
            target_x, target_y = self.path[self.current_path_index]
            
            # Calculate direction to next path node
            path_dx = target_x - self.x
            path_dy = target_y - self.y
            path_distance = math.sqrt(path_dx*path_dx + path_dy*path_dy)
            
            # If close enough to current waypoint, move to next
            if path_distance < TILE_SIZE / 2:
                self.current_path_index += 1
            else:
                # Normalize direction
                if path_distance > 0:
                    path_dx /= path_distance
                    path_dy /= path_distance
                
                # Move towards next path node
                new_x = self.x + path_dx * ENEMY_SPEED * TILE_SIZE
                new_y = self.y + path_dy * ENEMY_SPEED * TILE_SIZE
                
                # Map coordinates
                map_x = int(new_x / TILE_SIZE)
                map_y = int(new_y / TILE_SIZE)
                
                # Check if position is valid
                if (0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT and 
                    MAP[map_y][map_x] == 0):
                    self.x = new_x
                    self.y = new_y
        
        # Select appropriate sprite based on angle to player
        # Normalize angle to 0-360 degrees
        normalized_angle = (self.angle + 360) % 360
        
        # Front facing: -45 to 45 degrees
        if -45 <= normalized_angle <= 45 or normalized_angle >= 315:
            self.current_sprite_idx = 0  # Front sprite
        # Right side: 45 to 135 degrees
        elif 45 < normalized_angle < 135:
            self.current_sprite_idx = 1  # Side sprite
        # Back: 135 to 225 degrees
        elif 135 <= normalized_angle <= 225:
            self.current_sprite_idx = 2  # Back sprite
        # Left side: 225 to 315 degrees
        else:
            self.current_sprite_idx = 1  # Side sprite (mirrored later)
        
        # Handle attack cooldown
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        
        # Check if in attack range
        attacking = False
        if distance < TILE_SIZE * ENEMY_ATTACK_RANGE and self.attack_cooldown == 0:
            attacking = True
            self.attack_cooldown = ENEMY_ATTACK_COOLDOWN
            
        return attacking
    
    def take_damage(self, damage=1):
        self.hp -= damage
        self.hit_effect = 5  # Visual effect duration
        return self.hp <= 0  # Return True if dead
    
    def get_current_sprite(self):
        # Get current sprite based on viewing angle
        base_sprite = self.sprites[self.current_sprite_idx]
        
        # Special case: if looking at left side, flip the side sprite horizontally
        if self.current_sprite_idx == 1 and 225 <= (self.angle + 360) % 360 <= 315:
            return pygame.transform.flip(base_sprite, True, False)
        
        return base_sprite
    
# Create a multi-frame enemy sprite generator
def create_enemy_sprite():
    # Base size for the enemy sprite
    sprite_size = TILE_SIZE
    
    # Create different facing sprites for multiple viewing angles
    sprites = []
    
    # Create front-facing sprite (same as before)
    front_sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    
    # Body (dark red)
    body_color = (150, 30, 30)
    pygame.draw.rect(front_sprite, body_color, (sprite_size//4, sprite_size//3, sprite_size//2, sprite_size//2))
    
    # Head (lighter red)
    head_color = (180, 40, 40)
    head_size = sprite_size//4
    pygame.draw.circle(front_sprite, head_color, (sprite_size//2, sprite_size//4), head_size)
    
    # Arms (dark red)
    pygame.draw.rect(front_sprite, body_color, (sprite_size//8, sprite_size//3, sprite_size//6, sprite_size//3))
    pygame.draw.rect(front_sprite, body_color, (sprite_size*5//8, sprite_size//3, sprite_size//6, sprite_size//3))
    
    # Legs (dark red)
    pygame.draw.rect(front_sprite, body_color, (sprite_size//3, sprite_size*5//6, sprite_size//6, sprite_size//6))
    pygame.draw.rect(front_sprite, body_color, (sprite_size//2, sprite_size*5//6, sprite_size//6, sprite_size//6))
    
    # Eyes (white with black pupils)
    eye_offset = sprite_size//16
    eye_size = sprite_size//12
    pygame.draw.circle(front_sprite, (255, 255, 255), (sprite_size//2 - eye_offset, sprite_size//4), eye_size)
    pygame.draw.circle(front_sprite, (255, 255, 255), (sprite_size//2 + eye_offset, sprite_size//4), eye_size)
    
    # Pupils (black)
    pupil_size = eye_size//2
    pygame.draw.circle(front_sprite, (0, 0, 0), (sprite_size//2 - eye_offset, sprite_size//4), pupil_size)
    pygame.draw.circle(front_sprite, (0, 0, 0), (sprite_size//2 + eye_offset, sprite_size//4), pupil_size)
    
    # Add front sprite
    sprites.append(front_sprite)
    
    # Create side facing sprite (looks thinner when viewed from side)
    side_sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    
    # Body (dark red but narrower)
    pygame.draw.rect(side_sprite, body_color, (sprite_size*3//8, sprite_size//3, sprite_size//4, sprite_size//2))
    
    # Head (lighter red)
    pygame.draw.circle(side_sprite, head_color, (sprite_size//2, sprite_size//4), head_size)
    
    # Arms (one arm visible from side)
    pygame.draw.rect(side_sprite, body_color, (sprite_size*3//8, sprite_size//3, sprite_size//4, sprite_size//3))
    
    # Legs (one slightly in front of the other)
    pygame.draw.rect(side_sprite, body_color, (sprite_size*3//8, sprite_size*5//6, sprite_size//6, sprite_size//6))
    pygame.draw.rect(side_sprite, body_color, (sprite_size//2, sprite_size*5//6, sprite_size//6, sprite_size//6))
    
    # Eye (only one visible from side)
    pygame.draw.circle(side_sprite, (255, 255, 255), (sprite_size*5//8, sprite_size//4), eye_size)
    pygame.draw.circle(side_sprite, (0, 0, 0), (sprite_size*5//8, sprite_size//4), pupil_size)
    
    # Add side sprite
    sprites.append(side_sprite)
    
    # Create back facing sprite (similar to front but with back of head)
    back_sprite = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
    
    # Body (same as front)
    pygame.draw.rect(back_sprite, body_color, (sprite_size//4, sprite_size//3, sprite_size//2, sprite_size//2))
    
    # Head (darker to indicate back of head)
    darker_head = (head_color[0]//2, head_color[1]//2, head_color[2]//2)
    pygame.draw.circle(back_sprite, darker_head, (sprite_size//2, sprite_size//4), head_size)
    
    # Arms (dark red)
    pygame.draw.rect(back_sprite, body_color, (sprite_size//8, sprite_size//3, sprite_size//6, sprite_size//3))
    pygame.draw.rect(back_sprite, body_color, (sprite_size*5//8, sprite_size//3, sprite_size//6, sprite_size//3))
    
    # Legs (dark red)
    pygame.draw.rect(back_sprite, body_color, (sprite_size//3, sprite_size*5//6, sprite_size//6, sprite_size//6))
    pygame.draw.rect(back_sprite, body_color, (sprite_size//2, sprite_size*5//6, sprite_size//6, sprite_size//6))
    
    # No eyes visible from back
    
    # Add back sprite
    sprites.append(back_sprite)
    
    return sprites

def render_enemies(screen, player, enemies, z_buffer):
    # Convert player's angle to radians for calculations
    player_angle_rad = math.radians(player.angle)
    
    # Sort enemies by distance (render far to near)
    enemies_with_dist = []
    for enemy in enemies:
        # Calculate vector from player to enemy
        sprite_x = enemy.x - player.x
        sprite_y = enemy.y - player.y
        
        # Calculate distance to sprite
        sprite_dist = math.sqrt(sprite_x * sprite_x + sprite_y * sprite_y)
        enemies_with_dist.append((enemy, sprite_dist))
    
    # Sort by distance (far to near)
    enemies_with_dist.sort(key=lambda x: x[1], reverse=True)
    
    # Render each enemy
    for enemy, sprite_dist in enemies_with_dist:
        # Skip if the sprite is too far
        if sprite_dist > MAX_DEPTH * TILE_SIZE:
            continue
        
        # Calculate sprite angle relative to player's view
        sprite_angle = math.atan2(enemy.y - player.y, enemy.x - player.x) - player_angle_rad
        
        # Normalize angle to -π to π
        while sprite_angle > math.pi:
            sprite_angle -= 2 * math.pi
        while sprite_angle < -math.pi:
            sprite_angle += 2 * math.pi
        
        # Check if sprite is in field of view
        if abs(sprite_angle) > HALF_FOV_RAD * 1.5:  # Extra margin for wide sprites
            continue
        
        # Calculate sprite screen position
        # Map from angle to screen coordinate
        sprite_screen_x = (0.5 + sprite_angle / FOV_RAD) * SCREEN_WIDTH
        
        # Calculate sprite size based on distance
        sprite_size = min(SCREEN_HEIGHT, int(SCREEN_HEIGHT / (sprite_dist / TILE_SIZE)))
        
        # Calculate sprite vertical position
        sprite_top = max(0, SCREEN_HEIGHT // 2 - sprite_size // 2)
        sprite_bottom = min(SCREEN_HEIGHT, SCREEN_HEIGHT // 2 + sprite_size // 2)
        
        # Calculate horizontal span of sprite
        sprite_width = sprite_size
        sprite_left = int(sprite_screen_x - sprite_width / 2)
        sprite_right = sprite_left + sprite_width
        
        # Clamp to screen
        sprite_left = max(0, sprite_left)
        sprite_right = min(SCREEN_WIDTH, sprite_right)
        
        # Get the appropriate sprite based on viewing angle
        enemy_sprite = enemy.get_current_sprite()
        
        # Create a sprite surface scaled to the correct size
        scaled_sprite = pygame.transform.scale(enemy_sprite, (sprite_size, sprite_size))
        
        # If the enemy is hit, apply red tint effect
        if enemy.hit_effect > 0:
            # Create a red overlay
            red_overlay = Surface(scaled_sprite.get_size(), pygame.SRCALPHA)
            red_overlay.fill((255, 0, 0, 100))
            scaled_sprite.blit(red_overlay, (0, 0))
        
        # Draw sprite only where it's visible in front of walls
        for x in range(sprite_left, sprite_right):
            # Find the ray that corresponds to this x position
            ray_idx = int(x / WALL_STRIP_WIDTH)
            
            # Ensure ray_idx is within bounds
            if 0 <= ray_idx < len(z_buffer):
                # Only draw if sprite is closer than the wall at this ray
                if sprite_dist / TILE_SIZE < z_buffer[ray_idx]:
                    # Calculate the x position on the sprite texture
                    tex_x = int((x - sprite_left) / sprite_width * TILE_SIZE)
                    
                    # Calculate vertical strip to draw
                    strip_width = math.ceil(WALL_STRIP_WIDTH)
                    strip_height = sprite_bottom - sprite_top
                    
                    # Create a surface for the sprite strip
                    sprite_strip = Surface((strip_width, strip_height), pygame.SRCALPHA)
                    
                    # Cut out the vertical strip from the scaled sprite
                    for y in range(strip_height):
                        # Check if we're within the sprite boundaries
                        if tex_x < scaled_sprite.get_width() and y < scaled_sprite.get_height():
                            color = scaled_sprite.get_at((tex_x, y))
                            if color[3] > 0:  # Only if not fully transparent
                                sprite_strip.set_at((0, y), color)
                    
                    # Blit the sprite strip to the screen
                    screen.blit(sprite_strip, (x, sprite_top))

# Enemy manager class
class EnemyManager:
    def __init__(self):
        self.enemies = []
        self.spawn_cooldown = ENEMY_SPAWN_COOLDOWN
        self.show_paths = False  # Toggle for showing paths on minimap
        self.spawn_attempts = 0  # Track consecutive spawn failures
        
    def update(self, player, gun):
        # Process existing enemies
        for enemy in self.enemies[:]:  # Use a copy to safely remove during iteration
            # Update enemy and check if attacking
            attacking = enemy.update(player)
            
            # If enemy is attacking player
            if attacking:
                player_died = player.take_damage(ENEMY_DAMAGE)
                if player_died:
                    print("Player died!")
                    # Handle player death if needed
            
            # Check if player is shooting this enemy
            if gun.firing and gun.hit_data:
                # Calculate enemy position relative to player
                dx = enemy.x - player.x
                dy = enemy.y - player.y
                distance = math.sqrt(dx*dx + dy*dy)

                # Check if player is looking at enemy (angle check)
                enemy_angle = math.degrees(math.atan2(dy, dx))
                # Normalize angles for comparison
                enemy_angle = (enemy_angle + 360) % 360

                # Check each pellet/bullet in the spread pattern
                hit_distance_threshold = TILE_SIZE * 8
                enemy_hit = False

                for hit in gun.hit_data:
                    # Apply angle offset for this pellet
                    pellet_angle = (math.degrees(player.angle) + math.degrees(hit['angle_offset']) + 360) % 360

                    # Calculate angle difference with proper wrapping
                    angle_diff = min(abs(enemy_angle - pellet_angle),
                                   abs(enemy_angle - pellet_angle + 360),
                                   abs(enemy_angle - pellet_angle - 360))

                    # Make the hit detection forgiving based on distance
                    hit_angle_threshold = HALF_FOV * 1.2

                    # Check if enemy is in front of player and within this pellet's angle
                    if distance < hit_distance_threshold and angle_diff < hit_angle_threshold:
                        enemy_killed = enemy.take_damage()
                        enemy_hit = True
                        if enemy_killed:
                            self.enemies.remove(enemy)
                            player.score += 100

                            # Provide feedback text
                            print(f"Enemy killed! Total enemies: {len(self.enemies)}")
                            break  # Enemy is dead, no need to check more pellets

                # Visual feedback if enemy was hit but not killed
                if enemy_hit and enemy in self.enemies:
                    pass  # Enemy was hit (damage applied in take_damage)
        
        # Spawn new enemies if needed
        self.spawn_cooldown -= 1
        if self.spawn_cooldown <= 0 and len(self.enemies) < MAX_ENEMIES:
            # Try to spawn an enemy
            if self.spawn_enemy(player):
                # Reset cooldown and attempts counter on successful spawn
                self.spawn_cooldown = ENEMY_SPAWN_COOLDOWN
                self.spawn_attempts = 0
                print(f"Enemy spawned! Total enemies: {len(self.enemies)}")
            else:
                # Increment failed attempts counter
                self.spawn_attempts += 1
                
                # If we've had multiple failures, try again sooner but not immediately
                if self.spawn_attempts > 3:
                    self.spawn_cooldown = ENEMY_SPAWN_COOLDOWN // 3
                    # Reset attempts to prevent continuous rapid attempts
                    if self.spawn_attempts > 5:
                        self.spawn_attempts = 0
                else:
                    # Regular cooldown for first few attempts
                    self.spawn_cooldown = ENEMY_SPAWN_COOLDOWN
    
    def spawn_enemy(self, player):
        # Maximum attempts to find a valid spawn position
        max_attempts = 30
        attempts = 0
        
        while attempts < max_attempts:
            attempts += 1
            
            # Random map position
            x = random.randint(1, MAP_WIDTH-2)
            y = random.randint(1, MAP_HEIGHT-2)
            
            # Check if position is valid (not in a wall)
            if MAP[y][x] == 0:
                # Check if another enemy is already at this position
                position_occupied = False
                for enemy in self.enemies:
                    enemy_tile_x = int(enemy.x / TILE_SIZE)
                    enemy_tile_y = int(enemy.y / TILE_SIZE)
                    if enemy_tile_x == x and enemy_tile_y == y:
                        position_occupied = True
                        break
                
                if position_occupied:
                    continue
                
                # Check distance from player
                dx = x * TILE_SIZE - player.x
                dy = y * TILE_SIZE - player.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Only spawn if far enough from player
                if distance > TILE_SIZE * 3:
                    # Check reachability: can this enemy reach the player from here?
                    spawn_pos_x = x * TILE_SIZE + TILE_SIZE / 2  # Center of tile
                    spawn_pos_y = y * TILE_SIZE + TILE_SIZE / 2
                    
                    # Use our A* pathfinding to check if a path exists
                    path = a_star_pathfinding(spawn_pos_x, spawn_pos_y, player.x, player.y)
                    
                    # If a path exists, this is a valid spawn position
                    if path and len(path) > 1:  # Ensure path has at least 2 points
                        # Create a new enemy at this position
                        new_enemy = Enemy(spawn_pos_x, spawn_pos_y)
                        # Give it the initial path to the player
                        new_enemy.path = path
                        self.enemies.append(new_enemy)
                        return True
        
        # If we've reached max attempts without finding a valid position
        print(f"Failed to spawn enemy after {max_attempts} attempts")
        return False
    
    def draw_minimap(self, screen, minimap_scale):
        # Draw enemies on minimap
        for enemy in self.enemies:
            x = int(enemy.x / TILE_SIZE * minimap_scale)
            y = int(enemy.y / TILE_SIZE * minimap_scale)
            color = (255, 0, 0) if enemy.hit_effect > 0 else (200, 50, 50)
            
            # Draw enemy dot
            pygame.draw.circle(screen, color, (x, y), 2)
            
            # Draw enemy facing direction
            dir_x = x + math.cos(math.radians(enemy.angle)) * 5
            dir_y = y + math.sin(math.radians(enemy.angle)) * 5
            pygame.draw.line(screen, (255, 200, 50), (x, y), (int(dir_x), int(dir_y)), 1)
            
            # Optionally draw paths
            if self.show_paths and hasattr(enemy, 'path') and enemy.path:
                # Draw path nodes
                for i in range(len(enemy.path)-1):
                    start_x = int(enemy.path[i][0] / TILE_SIZE * minimap_scale)
                    start_y = int(enemy.path[i][1] / TILE_SIZE * minimap_scale)
                    end_x = int(enemy.path[i+1][0] / TILE_SIZE * minimap_scale)
                    end_y = int(enemy.path[i+1][1] / TILE_SIZE * minimap_scale)
                    pygame.draw.line(screen, (0, 255, 255, 128), (start_x, start_y), (end_x, end_y), 1)
                
                # Highlight current target node
                if hasattr(enemy, 'current_path_index') and enemy.current_path_index < len(enemy.path):
                    node_x = int(enemy.path[enemy.current_path_index][0] / TILE_SIZE * minimap_scale)
                    node_y = int(enemy.path[enemy.current_path_index][1] / TILE_SIZE * minimap_scale)
                    pygame.draw.circle(screen, (0, 255, 0), (node_x, node_y), 2)

# Update the draw_minimap function to include a toggle for showing paths
def draw_minimap(screen, player, enemy_manager=None):
    # Increase minimap size for larger maps
    minimap_size = 150  # Larger minimap size
    minimap_scale = minimap_size / max(MAP_WIDTH, MAP_HEIGHT)
    
    # Create a separate surface for the minimap with transparency
    minimap_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
    minimap_surface.fill((0, 0, 0, 180))  # Semi-transparent black background
    
    # Draw grid lines (optional - helps with orientation)
    grid_color = (40, 40, 40, 100)  # Very subtle grid
    for x in range(0, MAP_WIDTH + 1, 4):  # Draw every 4th line for less clutter
        pygame.draw.line(minimap_surface, grid_color, 
                       (x * minimap_scale, 0), 
                       (x * minimap_scale, minimap_size))
    for y in range(0, MAP_HEIGHT + 1, 4):
        pygame.draw.line(minimap_surface, grid_color, 
                       (0, y * minimap_scale), 
                       (minimap_size, y * minimap_scale))
    
    # Draw the walls
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if MAP[y][x] > 0:
                # Use different colors for different wall types
                wall_color = WHITE
                if MAP[y][x] == 1:
                    wall_color = (200, 200, 200)  # Light gray
                elif MAP[y][x] == 2:
                    wall_color = (150, 100, 100)  # Brick red
                
                # Draw filled rectangles for walls
                pygame.draw.rect(minimap_surface, wall_color,
                               (x * minimap_scale, 
                                y * minimap_scale, 
                                minimap_scale, minimap_scale), 0)
    
    # Draw rays for visualization
    # Calculate player's map position
    player_map_x = player.x / TILE_SIZE
    player_map_y = player.y / TILE_SIZE
    
    # Player position on minimap
    player_x = int(player.x / TILE_SIZE * minimap_scale)
    player_y = int(player.y / TILE_SIZE * minimap_scale)
    
    # Calculate start angle for rays
    start_angle = player.angle - HALF_FOV
    
    # Draw a subset of rays (every 10th ray to reduce clutter)
    ray_step = 10
    for ray_index in range(0, RAY_COUNT, ray_step):
        # Calculate ray angle
        ray_angle = start_angle + (ray_index / RAY_COUNT) * FOV
        ray_angle_rad = math.radians(ray_angle)
        
        # Ray direction vector
        ray_dir_x = math.cos(ray_angle_rad)
        ray_dir_y = math.sin(ray_angle_rad)
        
        # Initialize map position for DDA
        map_x = int(player_map_x)
        map_y = int(player_map_y)
        
        # Calculate DDA parameters
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else float('inf')
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else float('inf')
        
        step_x = 1 if ray_dir_x >= 0 else -1
        step_y = 1 if ray_dir_y >= 0 else -1
        
        if ray_dir_x < 0:
            side_dist_x = (player_map_x - map_x) * delta_dist_x
        else:
            side_dist_x = (map_x + 1.0 - player_map_x) * delta_dist_x
            
        if ray_dir_y < 0:
            side_dist_y = (player_map_y - map_y) * delta_dist_y
        else:
            side_dist_y = (map_y + 1.0 - player_map_y) * delta_dist_y
        
        # Perform DDA to find ray intersection with wall
        hit = False
        side = 0
        
        # Limit DDA iterations to prevent infinite loops
        max_dda_steps = max(MAP_WIDTH, MAP_HEIGHT) * 2
        dda_steps = 0
        
        while not hit and dda_steps < max_dda_steps:
            dda_steps += 1
            
            # Jump to next square
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
                 
            # Check if ray is out of bounds
            if not (0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT):
                break
                
            # Check if ray hit a wall
            if MAP[map_y][map_x] > 0:
                hit = True
        
        # Calculate ray endpoint
        if hit:
            # Calculate perpendicular wall distance
            if side == 0:
                perp_wall_dist = (map_x - player_map_x + (1 - step_x) / 2) / ray_dir_x
            else:
                perp_wall_dist = (map_y - player_map_y + (1 - step_y) / 2) / ray_dir_y
                
            # Calculate ray endpoint in world coordinates
            ray_end_x = player.x + ray_dir_x * perp_wall_dist * TILE_SIZE
            ray_end_y = player.y + ray_dir_y * perp_wall_dist * TILE_SIZE
        else:
            # If no hit, draw ray to edge of minimap
            ray_length = max(MAP_WIDTH, MAP_HEIGHT) * TILE_SIZE
            ray_end_x = player.x + ray_dir_x * ray_length
            ray_end_y = player.y + ray_dir_y * ray_length
        
        # Convert ray endpoint to minimap coordinates
        minimap_end_x = int(ray_end_x / TILE_SIZE * minimap_scale)
        minimap_end_y = int(ray_end_y / TILE_SIZE * minimap_scale)
        
        # Draw ray line with alpha transparency
        ray_color = (0, 200, 0, 70)  # Light green with transparency
        pygame.draw.line(minimap_surface, ray_color, 
                       (player_x, player_y), (minimap_end_x, minimap_end_y), 1)
    
    # Draw enemies if manager is provided
    if enemy_manager is not None:
        for enemy in enemy_manager.enemies:
            x = int(enemy.x / TILE_SIZE * minimap_scale)
            y = int(enemy.y / TILE_SIZE * minimap_scale)
            color = (255, 0, 0) if enemy.hit_effect > 0 else (200, 50, 50)
            
            # Increase enemy dot size slightly
            pygame.draw.circle(minimap_surface, color, (x, y), 2)
            
            # Draw enemy facing direction
            dir_x = x + math.cos(math.radians(enemy.angle)) * 5
            dir_y = y + math.sin(math.radians(enemy.angle)) * 5
            pygame.draw.line(minimap_surface, (255, 200, 50), (x, y), (int(dir_x), int(dir_y)), 1)
            
            # Optionally draw paths
            if hasattr(enemy_manager, 'show_paths') and enemy_manager.show_paths and hasattr(enemy, 'path') and enemy.path:
                # Draw path nodes
                for i in range(len(enemy.path)-1):
                    start_x = int(enemy.path[i][0] / TILE_SIZE * minimap_scale)
                    start_y = int(enemy.path[i][1] / TILE_SIZE * minimap_scale)
                    end_x = int(enemy.path[i+1][0] / TILE_SIZE * minimap_scale)
                    end_y = int(enemy.path[i+1][1] / TILE_SIZE * minimap_scale)
                    pygame.draw.line(minimap_surface, (0, 255, 255, 128), (start_x, start_y), (end_x, end_y), 1)
                
                # Highlight current target node
                if hasattr(enemy, 'current_path_index') and enemy.current_path_index < len(enemy.path):
                    node_x = int(enemy.path[enemy.current_path_index][0] / TILE_SIZE * minimap_scale)
                    node_y = int(enemy.path[enemy.current_path_index][1] / TILE_SIZE * minimap_scale)
                    pygame.draw.circle(minimap_surface, (0, 255, 0), (node_x, node_y), 2)
    
    # Draw player position and direction
    player_x = int(player.x / TILE_SIZE * minimap_scale)
    player_y = int(player.y / TILE_SIZE * minimap_scale)
    
    # Player position as a circle
    pygame.draw.circle(minimap_surface, RED, (player_x, player_y), 3)
    
    # Player direction as a line
    dir_len = 8
    dir_x = player_x + math.cos(math.radians(player.angle)) * dir_len
    dir_y = player_y + math.sin(math.radians(player.angle)) * dir_len
    pygame.draw.line(minimap_surface, RED, (player_x, player_y), (int(dir_x), int(dir_y)), 2)
    
    # Draw FOV cone (optional - helps with orientation)
    left_angle = math.radians(player.angle - HALF_FOV)
    right_angle = math.radians(player.angle + HALF_FOV)
    fov_len = 15
    left_x = player_x + math.cos(left_angle) * fov_len
    left_y = player_y + math.sin(left_angle) * fov_len
    right_x = player_x + math.cos(right_angle) * fov_len
    right_y = player_y + math.sin(right_angle) * fov_len
    
    # Draw FOV as semi-transparent triangle
    fov_points = [(player_x, player_y), (int(left_x), int(left_y)), (int(right_x), int(right_y))]
    fov_surface = pygame.Surface((minimap_size, minimap_size), pygame.SRCALPHA)
    pygame.draw.polygon(fov_surface, (255, 255, 0, 30), fov_points)  # Very transparent yellow
    minimap_surface.blit(fov_surface, (0, 0))
    
    # Add a border around the minimap
    pygame.draw.rect(minimap_surface, (150, 150, 150), (0, 0, minimap_size, minimap_size), 1)
    
    # Add a minimap title
    small_font = pygame.font.SysFont(None, 14)
    title_text = small_font.render("MINIMAP", True, (200, 200, 200))
    minimap_surface.blit(title_text, (minimap_size//2 - title_text.get_width()//2, 2))
    
    # Blit the minimap surface to the screen in the top-left corner with a small margin
    screen.blit(minimap_surface, (10, 10))


# Modify the cast_rays function to add enemy rendering
# Complete cast_rays function with enemy rendering
def cast_rays(screen, player, textures, gun=None, enemy_manager=None):
    # Create sky and floor surfaces once
    sky_surface = Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 2))
    floor_surface = Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 2))
    
    # Pre-calculate the sky gradient
    for y in range(SCREEN_HEIGHT // 2):
        color = (100, 100, 255 - y // 2)
        pygame.draw.line(sky_surface, color, (0, y), (SCREEN_WIDTH, y))
    
    # Pre-calculate the floor gradient
    for y in range(SCREEN_HEIGHT // 2):
        color = (40 + y // 5, 40 + y // 5, 40 + y // 5)
        pygame.draw.line(floor_surface, color, (0, y), (SCREEN_WIDTH, y))
    
    # Blit the sky and floor to the screen
    screen.blit(sky_surface, (0, 0))
    screen.blit(floor_surface, (0, SCREEN_HEIGHT // 2))
    
    # Create a surface for the wall columns
    # This allows us to draw columns more efficiently than individual pixels
    wall_surface = Surface((RAY_COUNT, SCREEN_HEIGHT))
    wall_surface.fill((0, 0, 0))  # Fill with black to start
    wall_pixel_array = PixelArray(wall_surface)
    
    # Precalculate player's position and view data
    player_map_x = player.x / TILE_SIZE
    player_map_y = player.y / TILE_SIZE
    start_angle = player.angle - HALF_FOV
    
    # Precalculate constants for the inner loop
    screen_half_height = SCREEN_HEIGHT // 2
    tile_size_minus_one = TILE_SIZE - 1
    
    # Store distance to walls for each ray for sprite rendering
    z_buffer = [float('inf')] * RAY_COUNT
    
    # Cast rays in batches
    for ray in range(RAY_COUNT):
        # Calculate ray angle
        ray_angle = start_angle + (ray / RAY_COUNT) * FOV
        ray_angle_rad = math.radians(ray_angle)
        
        # Ray direction vector
        ray_dir_x = math.cos(ray_angle_rad)
        ray_dir_y = math.sin(ray_angle_rad)
        
        # DDA Algorithm with integer optimizations where possible
        map_x = int(player_map_x)
        map_y = int(player_map_y)
        
        # Optimize division - calculate once
        if ray_dir_x != 0:
            delta_dist_x = abs(1 / ray_dir_x)
        else:
            delta_dist_x = float('inf')
            
        if ray_dir_y != 0:
            delta_dist_y = abs(1 / ray_dir_y)
        else:
            delta_dist_y = float('inf')
        
        # Direction to step in - can be integer
        step_x = 1 if ray_dir_x >= 0 else -1
        step_y = 1 if ray_dir_y >= 0 else -1
        
        # Length of ray from current position to next x or y side
        if ray_dir_x < 0:
            side_dist_x = (player_map_x - map_x) * delta_dist_x
        else:
            side_dist_x = (map_x + 1.0 - player_map_x) * delta_dist_x
        
        if ray_dir_y < 0:
            side_dist_y = (player_map_y - map_y) * delta_dist_y
        else:
            side_dist_y = (map_y + 1.0 - player_map_y) * delta_dist_y
        
        # Perform optimized DDA
        hit = False
        side = 0  # 0 for x-side, 1 for y-side
        
        # Simplified boundary check
        map_bounds_ok = True
        
        while not hit and map_bounds_ok:
            # Jump to next map square
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            
            # Fast bounds check
            map_bounds_ok = (0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT)
            
            # Check if ray hit a wall
            if map_bounds_ok and MAP[map_y][map_x] > 0:
                hit = True
        
        if hit:
            # Calculate distance - avoid division where possible
            if side == 0:
                perp_wall_dist = (map_x - player_map_x + (1 - step_x) / 2) / ray_dir_x
            else:
                perp_wall_dist = (map_y - player_map_y + (1 - step_y) / 2) / ray_dir_y
            
            # Store the distance for sprite rendering (z-buffer)
            z_buffer[ray] = perp_wall_dist
            
            # Calculate line height - avoid floating-point division inside loop
            line_height = int(SCREEN_HEIGHT / perp_wall_dist) if perp_wall_dist > 0 else SCREEN_HEIGHT
            
            # Prevent the line from being too tall - use max/min to avoid conditionals
            line_height = min(line_height, SCREEN_HEIGHT * 3)
            
            # Calculate draw boundaries
            draw_start = max(0, -line_height // 2 + screen_half_height)
            draw_end = min(SCREEN_HEIGHT - 1, line_height // 2 + screen_half_height)
            
            # Texture calculations
            wall_texture_idx = MAP[map_y][map_x] - 1
            # Make sure the wall_texture_idx is valid before accessing textures
            if wall_texture_idx < 0 or wall_texture_idx >= len(textures):
                wall_texture_idx = 0  # Use the first texture as a fallback
            
            # Calculate wall X coordinate more efficiently
            if side == 0:
                wall_x = player_map_y + perp_wall_dist * ray_dir_y
            else:
                wall_x = player_map_x + perp_wall_dist * ray_dir_x
            wall_x -= int(wall_x)  # Faster than math.floor
            
            # X coordinate on the texture
            tex_x = int(wall_x * TILE_SIZE)
            if (side == 0 and ray_dir_x > 0) or (side == 1 and ray_dir_y < 0):
                tex_x = TILE_SIZE - tex_x - 1
            
            # Calculate shade based on distance and side
            # Apply y-side darkening
            base_shade = 0.8 if side == 1 else 1.0
            
            # Distance fog effect - map to precomputed shade levels
            distance_factor = min(1.0, perp_wall_dist / MAX_DEPTH)
            shade_factor = base_shade * (1.0 - distance_factor * 0.6)  # Scale down brightness with distance
            
            # Get texture
            texture = textures[wall_texture_idx]
            
            # Draw vertical wall strip
            strip_height = draw_end - draw_start
            if strip_height > 0:
                # Calculate width of the strip - round up to ensure no gaps
                strip_width = math.ceil(WALL_STRIP_WIDTH)
                
                # Create a surface for this wall strip with exact dimensions
                column_surface = Surface((strip_width, strip_height))
                
                # Calculate texture step only once per column
                tex_step = TILE_SIZE / line_height
                tex_pos = (draw_start - screen_half_height + line_height // 2) * tex_step
                
                # Build the texture column with the exact height needed
                tex_position = tex_pos
                for y in range(strip_height):
                    tex_y = int(tex_position) & tile_size_minus_one
                    tex_position += tex_step
                    
                    # Get color from texture using get_at instead of direct indexing
                    color = texture.get_at((tex_x, tex_y))
                    r = int(color[0] * shade_factor)
                    g = int(color[1] * shade_factor)
                    b = int(color[2] * shade_factor)
                    
                    # Fill the entire width of the strip with this color
                    pygame.draw.line(column_surface, (r, g, b), 
                                    (0, y), (strip_width-1, y))
                
                # Blit the column to the screen - ensure exact positioning
                screen.blit(column_surface, (int(ray * WALL_STRIP_WIDTH), draw_start))
        else:
            # If no wall was hit, set z_buffer to maximum depth
            z_buffer[ray] = MAX_DEPTH
    
    # Render enemies after walls (sprite rendering)
    if enemy_manager is not None:
        # Convert player's angle to radians for calculations
        player_angle_rad = math.radians(player.angle)
        
        # Sort enemies by distance (render far to near)
        enemies_with_dist = []
        for enemy in enemy_manager.enemies:
            # Calculate vector from player to enemy
            sprite_x = enemy.x - player.x
            sprite_y = enemy.y - player.y
            
            # Calculate distance to sprite
            sprite_dist = math.sqrt(sprite_x * sprite_x + sprite_y * sprite_y)
            enemies_with_dist.append((enemy, sprite_dist))
        
        # Sort by distance (far to near)
        enemies_with_dist.sort(key=lambda x: x[1], reverse=True)
        
        # Render each enemy
        for enemy, sprite_dist in enemies_with_dist:
            # Skip if the sprite is too far
            if sprite_dist > MAX_DEPTH * TILE_SIZE:
                continue
            
            # Calculate sprite angle relative to player's view
            sprite_angle = math.atan2(enemy.y - player.y, enemy.x - player.x) - player_angle_rad
            
            # Normalize angle to -π to π
            while sprite_angle > math.pi:
                sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi:
                sprite_angle += 2 * math.pi
            
            # Check if sprite is in field of view
            if abs(sprite_angle) > HALF_FOV_RAD * 1.5:  # Extra margin for wide sprites
                continue
            
            # Calculate sprite screen position
            # Map from angle to screen coordinate
            sprite_screen_x = (0.5 + sprite_angle / FOV_RAD) * SCREEN_WIDTH
            
            # Calculate sprite size based on distance
            sprite_size = min(SCREEN_HEIGHT, int(SCREEN_HEIGHT / (sprite_dist / TILE_SIZE)))
            
            # Calculate sprite vertical position
            sprite_top = max(0, SCREEN_HEIGHT // 2 - sprite_size // 2)
            sprite_bottom = min(SCREEN_HEIGHT, SCREEN_HEIGHT // 2 + sprite_size // 2)
            
            # Calculate horizontal span of sprite
            sprite_width = sprite_size
            sprite_left = int(sprite_screen_x - sprite_width / 2)
            sprite_right = sprite_left + sprite_width
            
            # Clamp to screen
            sprite_left = max(0, sprite_left)
            sprite_right = min(SCREEN_WIDTH, sprite_right)
            
            # Get the appropriate sprite based on viewing angle
            enemy_sprite = enemy.get_current_sprite()
            
            # Create a sprite surface scaled to the correct size
            scaled_sprite = pygame.transform.scale(enemy_sprite, (sprite_size, sprite_size))
            
            # If the enemy is hit, apply red tint effect
            if enemy.hit_effect > 0:
                # Create a red overlay
                red_overlay = Surface(scaled_sprite.get_size(), pygame.SRCALPHA)
                red_overlay.fill((255, 0, 0, 100))
                scaled_sprite.blit(red_overlay, (0, 0))
            
            # Draw sprite only where it's visible in front of walls
            for x in range(sprite_left, sprite_right):
                # Find the ray that corresponds to this x position
                ray_idx = int(x / WALL_STRIP_WIDTH)
                
                # Ensure ray_idx is within bounds
                if 0 <= ray_idx < len(z_buffer):
                    # Only draw if sprite is closer than the wall at this ray
                    if sprite_dist / TILE_SIZE < z_buffer[ray_idx]:
                        # Calculate the x position on the sprite texture
                        tex_x = int((x - sprite_left) / sprite_width * TILE_SIZE)
                        
                        # Calculate vertical strip to draw
                        strip_width = math.ceil(WALL_STRIP_WIDTH)
                        strip_height = sprite_bottom - sprite_top
                        
                        # Create a surface for the sprite strip
                        sprite_strip = Surface((strip_width, strip_height), pygame.SRCALPHA)
                        
                        # Cut out the vertical strip from the scaled sprite
                        for y in range(strip_height):
                            # Check if we're within the sprite boundaries
                            if tex_x < scaled_sprite.get_width() and y < scaled_sprite.get_height():
                                color = scaled_sprite.get_at((tex_x, y))
                                if color[3] > 0:  # Only if not fully transparent
                                    sprite_strip.set_at((0, y), color)
                        
                        # Blit the sprite strip to the screen
                        screen.blit(sprite_strip, (x, sprite_top))
    
    # Draw minimap and rays - only needed for debugging
    draw_minimap(screen, player, enemy_manager)
    
    
    # Draw gun if provided
    if gun is not None:
        gun.draw(screen)
    else:
        # Original placeholder code (only used if gun is None)
        weapon_width = 150
        weapon_height = 120
        weapon_x = SCREEN_WIDTH // 2 - weapon_width // 2
        weapon_y = SCREEN_HEIGHT - weapon_height
        pygame.draw.rect(screen, (80, 80, 80), (weapon_x, weapon_y, weapon_width, weapon_height // 2))
        pygame.draw.rect(screen, (60, 60, 60), (weapon_x + 20, weapon_y - 20, weapon_width - 40, weapon_height // 3))
    
    # Add red overlay when hit
    if player.hit_effect > 0:
        overlay = Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        alpha = min(150, player.hit_effect * 15)
        overlay.fill((255, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
    
    # Draw health bar
    health_width = 200
    health_height = 20
    health_x = 10
    health_y = SCREEN_HEIGHT - health_height - 40
    
    # Background
    pygame.draw.rect(screen, (50, 50, 50), (health_x, health_y, health_width, health_height))
    
    # Health fill
    health_fill_width = int((player.health / PLAYER_MAX_HEALTH) * health_width)
    health_color = (0, 255, 0) if player.health > 50 else (255, 165, 0) if player.health > 25 else (255, 0, 0)
    pygame.draw.rect(screen, health_color, (health_x, health_y, health_fill_width, health_height))
    
    # Border
    pygame.draw.rect(screen, (200, 200, 200), (health_x, health_y, health_width, health_height), 2)
    
    # Health text
    font = pygame.font.SysFont(None, 30)
    health_text = font.render(f"HEALTH: {player.health}", True, (255, 255, 255))
    screen.blit(health_text, (health_x + 10, health_y + 2))
    
    # Draw score
    score_text = font.render(f"SCORE: {player.score}", True, (255, 255, 255))
    screen.blit(score_text, (SCREEN_WIDTH - 150, 50))

# Create a directory for sound files if it doesn't exist
def ensure_sound_directory():
    sound_dir = "sounds"
    if not os.path.exists(sound_dir):
        os.makedirs(sound_dir)
    
    # Create simple sound files if they don't exist
    create_sound_files(sound_dir)

# Create placeholder sound files if they don't exist
def create_sound_files(sound_dir):
    # Gun fire sound (short beep)
    gun_fire_path = os.path.join(sound_dir, "gun_fire.wav")
    if not os.path.exists(gun_fire_path):
        create_beep_sound(gun_fire_path, frequency=200, duration=100, volume=0.3)
    
    # Empty gun click
    gun_empty_path = os.path.join(sound_dir, "gun_empty.wav")
    if not os.path.exists(gun_empty_path):
        create_beep_sound(gun_empty_path, frequency=100, duration=50, volume=0.2)
    
    # Reload sound
    gun_reload_path = os.path.join(sound_dir, "gun_reload.wav")
    if not os.path.exists(gun_reload_path):
        create_beep_sound(gun_reload_path, frequency=150, duration=300, volume=0.3)

# Function to create a simple beep sound
def create_beep_sound(filename, frequency=440, duration=100, volume=0.5):
    try:
        import numpy as np
        from scipy.io import wavfile
        
        sample_rate = 44100
        t = np.linspace(0, duration/1000, int(sample_rate * duration/1000), False)
        
        # Generate a simple sine wave
        note = np.sin(frequency * t * 2 * np.pi)
        
        # Apply volume
        note = note * volume
        
        # Convert to 16-bit audio
        audio = np.int16(note * 32767)
        
        # Save as WAV file
        wavfile.write(filename, sample_rate, audio)
    except ImportError:
        # If scipy is not available, create an empty file
        with open(filename, 'wb') as f:
            f.write(b'')

# Game state enum to track the current state
class GameState(Enum):
    MAIN_MENU = 0
    PLAYING = 1
    OPTIONS = 2
    GAME_OVER = 3
    CREDITS = 4

# Button class for menu interactions
class Button:
    def __init__(self, text, x, y, width, height, color, hover_color, text_color, font_size=36):
        self.text = text
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font_size = font_size
        self.font = pygame.font.SysFont(None, font_size)
        self.is_hovered = False
        self.click_sound = None
        self.hover_sound = None
        self.sound_played = False
        
        # Try to load button sounds if they exist
        try:
            # Check if mixer is initialized
            if pygame.mixer.get_init():
                self.click_sound = pygame.mixer.Sound(os.path.join("sounds", "button_click.wav"))
                self.hover_sound = pygame.mixer.Sound(os.path.join("sounds", "button_hover.wav"))
                # Set volume lower for UI sounds
                if self.click_sound and self.hover_sound:
                    self.click_sound.set_volume(0.3)
                    self.hover_sound.set_volume(0.2)
        except:
            # If sounds can't be loaded, just continue without them
            pass
    
    def draw(self, screen):
        # Draw button with hover effect
        current_color = self.hover_color if self.is_hovered else self.color
        
        # Draw button body with a gradient effect
        for i in range(self.height):
            # Darker at the bottom, lighter at the top
            factor = 1.0 - (i / self.height) * 0.3
            gradient_color = (
                int(current_color[0] * factor),
                int(current_color[1] * factor),
                int(current_color[2] * factor)
            )
            pygame.draw.line(screen, gradient_color, 
                           (self.x, self.y + i), 
                           (self.x + self.width, self.y + i))
        
        # Draw button border
        border_color = (255, 255, 255) if self.is_hovered else (150, 150, 150)
        border_width = 2 if self.is_hovered else 1
        pygame.draw.rect(screen, border_color, 
                        (self.x, self.y, self.width, self.height), 
                        border_width)
        
        # Render text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width // 2, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

    def check_hover(self, mouse_pos):
        # Check if mouse is over button
        old_hover = self.is_hovered
        self.is_hovered = (self.x <= mouse_pos[0] <= self.x + self.width and 
                          self.y <= mouse_pos[1] <= self.y + self.height)
        
        # Play hover sound on first hover
        if not old_hover and self.is_hovered and self.hover_sound and not self.sound_played:
            self.hover_sound.play()
            self.sound_played = True
        elif not self.is_hovered:
            self.sound_played = False
            
        return self.is_hovered
    
    def check_click(self, mouse_pos, mouse_click):
        # Check if button was clicked
        if (self.x <= mouse_pos[0] <= self.x + self.width and 
            self.y <= mouse_pos[1] <= self.y + self.height and 
            mouse_click):
            if self.click_sound:
                self.click_sound.play()
            return True
        return False

# Main menu class
class MainMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Create title font
        self.title_font = pygame.font.SysFont(None, 80)
        self.subtitle_font = pygame.font.SysFont(None, 30)
        
        # Create buttons
        button_width = 250
        button_height = 60
        button_spacing = 30
        button_x = (screen_width - button_width) // 2
        button_start_y = screen_height // 2
        
        # Button colors
        button_color = (60, 60, 60)
        hover_color = (100, 100, 100)
        text_color = (255, 255, 255)
        
        self.start_button = Button("START GAME", button_x, button_start_y, 
                                 button_width, button_height, 
                                 button_color, hover_color, text_color)
        
        self.options_button = Button("OPTIONS", button_x, button_start_y + button_height + button_spacing, 
                                   button_width, button_height, 
                                   button_color, hover_color, text_color)
        
        self.quit_button = Button("QUIT", button_x, button_start_y + (button_height + button_spacing) * 2, 
                                button_width, button_height, 
                                button_color, hover_color, text_color)
        
        # Create background with pixel scaling for a retro effect
        self.background = self.create_background()
        
        # Background scroll effect
        self.bg_scroll = 0
        
        # Try to load menu music if it exists
        self.music_playing = False
        try:
            if pygame.mixer.get_init():
                pygame.mixer.music.load(os.path.join("sounds", "menu_music.wav"))
                pygame.mixer.music.set_volume(0.5)
                self.music_playing = True
        except:
            # If music can't be loaded, just continue without it
            pass

    def create_background(self):
        # Create a background pattern with a simple grid
        bg = pygame.Surface((self.screen_width // 4, self.screen_height // 4))
        bg.fill((20, 20, 30))
        
        # Draw a grid pattern
        for x in range(0, bg.get_width(), 8):
            pygame.draw.line(bg, (40, 40, 60), (x, 0), (x, bg.get_height()))
        
        for y in range(0, bg.get_height(), 8):
            pygame.draw.line(bg, (40, 40, 60), (0, y), (bg.get_width(), y))
        
        # Scale up for a pixelated retro look
        scaled_bg = pygame.transform.scale(bg, (self.screen_width, self.screen_height))
        return scaled_bg

    def draw(self, screen, dt):
        # Update scrolling background
        self.bg_scroll = (self.bg_scroll + 20 * dt) % self.screen_height
        
        # Draw background with scroll effect
        screen.blit(self.background, (0, int(self.bg_scroll)))
        screen.blit(self.background, (0, int(self.bg_scroll) - self.screen_height))
        
        # Draw semi-transparent overlay for better text readability
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Draw game title with glowing effect
        title_text = "FPS RAYCASTER"
        pulse = (math.sin(pygame.time.get_ticks() / 300) + 1) / 2  # 0 to 1 pulsing effect
        
        # Draw glow behind text
        glow_factor = 5 + pulse * 5
        glow_size = int(80 + glow_factor)
        glow_font = pygame.font.SysFont(None, glow_size)
        glow_surf = glow_font.render(title_text, True, (120, 20, 20))
        glow_rect = glow_surf.get_rect(center=(self.screen_width // 2, 150))
        
        # Apply blur to the glow (simplified)
        for i in range(3):
            blur_offset = i * 2
            screen.blit(glow_surf, (glow_rect.x - blur_offset, glow_rect.y), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(glow_surf, (glow_rect.x + blur_offset, glow_rect.y), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(glow_surf, (glow_rect.x, glow_rect.y - blur_offset), special_flags=pygame.BLEND_RGB_ADD)
            screen.blit(glow_surf, (glow_rect.x, glow_rect.y + blur_offset), special_flags=pygame.BLEND_RGB_ADD)
        
        # Draw main title
        title_surf = self.title_font.render(title_text, True, (220, 50, 50))
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 150))
        screen.blit(title_surf, title_rect)
        
        # Draw subtitle
        subtitle = "A Python Raycaster Engine"
        subtitle_surf = self.subtitle_font.render(subtitle, True, (200, 200, 200))
        subtitle_rect = subtitle_surf.get_rect(center=(self.screen_width // 2, 210))
        screen.blit(subtitle_surf, subtitle_rect)
        
        # Draw buttons
        self.start_button.draw(screen)
        self.options_button.draw(screen)
        self.quit_button.draw(screen)
        
        # Draw version info at the bottom
        version_text = "v32.2.0"
        version_font = pygame.font.SysFont(None, 20)
        version_surf = version_font.render(version_text, True, (150, 150, 150))
        screen.blit(version_surf, (10, self.screen_height - 30))

    def update(self, mouse_pos, mouse_clicked):
        # Check button interactions
        self.start_button.check_hover(mouse_pos)
        self.options_button.check_hover(mouse_pos)
        self.quit_button.check_hover(mouse_pos)
        
        # Return appropriate action if a button was clicked
        if self.start_button.check_click(mouse_pos, mouse_clicked):
            # Start the menu music if it's not already playing
            if self.music_playing and pygame.mixer.music.get_busy():
                pygame.mixer.music.fadeout(1000)
            return GameState.PLAYING
        
        elif self.options_button.check_click(mouse_pos, mouse_clicked):
            return GameState.OPTIONS
        
        elif self.quit_button.check_click(mouse_pos, mouse_clicked):
            return None  # None indicates quit
        
        # Return current state if no button was clicked
        return GameState.MAIN_MENU

# Options menu
class OptionsMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Create fonts
        self.title_font = pygame.font.SysFont(None, 60)
        self.option_font = pygame.font.SysFont(None, 30)
        
        # Button colors
        button_color = (60, 60, 60)
        hover_color = (100, 100, 100)
        text_color = (255, 255, 255)
        
        # Create buttons
        button_width = 250
        button_height = 50
        button_x = (screen_width - button_width) // 2
        
        # Volume sliders
        self.volume_levels = {"master": 0.7, "sfx": 0.5, "music": 0.5}
        slider_y = 150
        self.sliders = []
        
        for i, (name, level) in enumerate(self.volume_levels.items()):
            self.sliders.append({
                "name": name.capitalize(),
                "value": level,
                "x": button_x,
                "y": slider_y + i * 60,
                "width": button_width,
                "height": 20,
                "is_dragging": False
            })
        
        # Back button
        self.back_button = Button("BACK", button_x, screen_height - 150, 
                               button_width, button_height, 
                               button_color, hover_color, text_color)
    
    def draw(self, screen):
        # Draw dark background
        screen.fill((20, 20, 30))
        
        # Draw title
        title_surf = self.title_font.render("OPTIONS", True, (200, 200, 200))
        title_rect = title_surf.get_rect(center=(self.screen_width // 2, 60))
        screen.blit(title_surf, title_rect)
        
        # Draw sliders
        for slider in self.sliders:
            # Draw slider name
            name_surf = self.option_font.render(f"{slider['name']} Volume: {int(slider['value'] * 100)}%", 
                                             True, (200, 200, 200))
            screen.blit(name_surf, (slider["x"], slider["y"] - 30))
            
            # Draw slider track
            pygame.draw.rect(screen, (80, 80, 80), 
                          (slider["x"], slider["y"], slider["width"], slider["height"]))
            
            # Draw slider fill
            fill_width = int(slider["width"] * slider["value"])
            pygame.draw.rect(screen, (200, 70, 70), 
                          (slider["x"], slider["y"], fill_width, slider["height"]))
            
            # Draw slider handle
            handle_x = slider["x"] + fill_width - 5
            pygame.draw.rect(screen, (220, 220, 220), 
                          (handle_x, slider["y"] - 5, 10, slider["height"] + 10))
        
        # Draw back button
        self.back_button.draw(screen)

    def update(self, mouse_pos, mouse_clicked, mouse_held):
        # Check button interactions
        self.back_button.check_hover(mouse_pos)
        
        # Handle sliders
        for slider in self.sliders:
            slider_rect = pygame.Rect(slider["x"], slider["y"], slider["width"], slider["height"])
            if slider_rect.collidepoint(mouse_pos):
                if mouse_clicked:
                    slider["is_dragging"] = True
            
            if not mouse_held:
                slider["is_dragging"] = False
            
            if slider["is_dragging"]:
                # Calculate new value based on mouse position
                rel_x = max(0, min(mouse_pos[0] - slider["x"], slider["width"]))
                slider["value"] = rel_x / slider["width"]
                
                # Apply volume changes
                if slider["name"] == "Master":
                    # Adjust all volume together
                    if pygame.mixer.get_init():
                        pygame.mixer.music.set_volume(slider["value"] * self.volume_levels["music"])
                elif slider["name"] == "Sfx":
                    # Would need to adjust all sound effects
                    self.volume_levels["sfx"] = slider["value"]
                elif slider["name"] == "Music":
                    if pygame.mixer.get_init():
                        pygame.mixer.music.set_volume(slider["value"] * self.volume_levels["master"])
                    self.volume_levels["music"] = slider["value"]
        
        # Return appropriate action if the back button was clicked
        if self.back_button.check_click(mouse_pos, mouse_clicked):
            return GameState.MAIN_MENU
        
        # Return current state if no button was clicked
        return GameState.OPTIONS

# Create sounds for buttons if they don't exist
def create_menu_sounds():
    sound_dir = "sounds"
    if not os.path.exists(sound_dir):
        os.makedirs(sound_dir)
    
    # Create button sounds if they don't exist
    hover_sound_path = os.path.join(sound_dir, "button_hover.wav")
    click_sound_path = os.path.join(sound_dir, "button_click.wav")
    
    if not os.path.exists(hover_sound_path):
        create_beep_sound(hover_sound_path, frequency=300, duration=50, volume=0.2)
    
    if not os.path.exists(click_sound_path):
        create_beep_sound(click_sound_path, frequency=400, duration=80, volume=0.3)
    
    # Create simple menu music if it doesn't exist
    music_path = os.path.join(sound_dir, "menu_music.wav")
    if not os.path.exists(music_path):
        try:
            import numpy as np
            from scipy.io import wavfile
            
            # Create a very simple looping tone sequence
            sample_rate = 44100
            duration = 10  # 10 seconds of music
            
            # Generate a simple melody
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            audio = np.zeros_like(t)
            
            # Define some notes (frequencies in Hz)
            notes = [220, 247, 262, 294, 330, 349, 392, 440]
            
            # Create a simple sequence
            for i, note in enumerate(notes):
                start = i * duration / len(notes)
                end = (i + 0.8) * duration / len(notes)  # Slight gap between notes
                
                # Create time slice for this note
                mask = (t >= start) & (t < end)
                
                # Create a simple envelope
                envelope = np.ones_like(t[mask])
                attack = int(len(envelope) * 0.1)
                release = int(len(envelope) * 0.2)
                
                envelope[:attack] = np.linspace(0, 1, attack)
                envelope[-release:] = np.linspace(1, 0, release)
                
                # Add the note with envelope
                audio[mask] += 0.3 * envelope * np.sin(2 * np.pi * note * t[mask])
            
            # Apply overall fade in/out
            fade = 44100  # 1 second fade
            audio[:fade] *= np.linspace(0, 1, fade)
            audio[-fade:] *= np.linspace(1, 0, fade)
            
            # Convert to 16-bit audio
            audio = np.int16(audio * 32767 * 0.3)  # Lower volume
            
            # Save as WAV file
            wavfile.write(music_path, sample_rate, audio)
            
        except ImportError:
            # If scipy is not available, create an empty file
            with open(music_path, 'wb') as f:
                f.write(b'')

def main():
    # Initialize pygame with optimized flags
    pygame.init()
    
    # Use hardware acceleration if available
    flags = pygame.HWSURFACE | pygame.DOUBLEBUF
    if hasattr(pygame, 'SCALED'):
        flags |= pygame.SCALED  # Improve high-DPI display performance
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption("FPS Raycaster")
    
    # Create a display surface for double buffering
    display_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    # Set up the game clock with vsync flag
    clock = pygame.time.Clock()
    
    # Ensure sound directories and files exist
    ensure_sound_directory()
    create_menu_sounds()
    
    # Create menu instances
    main_menu = MainMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    options_menu = OptionsMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Set initial game state
    game_state = GameState.MAIN_MENU
    
    # Start menu music
    if pygame.mixer.get_init():
        pygame.mixer.music.play(-1)  # Loop forever
    
    # Game objects (will be initialized when starting the game)
    player = None
    gun = None
    textures = None
    enemy_manager = None

    # Weapon inventory - tracks ammo for each weapon type
    weapon_inventory = {
        'pistol': WEAPON_CONFIGS['pistol']['max_ammo'],
        'shotgun': WEAPON_CONFIGS['shotgun']['max_ammo'],
        'rifle': WEAPON_CONFIGS['rifle']['max_ammo']
    }
    current_weapon_type = 'pistol'

    # Mouse state
    mouse_visible = True
    mouse_clicked = False
    mouse_held = False
    
    # Performance tracking
    frame_times = []
    moving_avg_size = 60  # Last 60 frames for average
    
    # Framerate settings
    target_fps = 144  # Higher target for modern displays
    
    # Main game loop
    running = True
    fps_counter = 0
    fps_timer = pygame.time.get_ticks()
    fps_display = "FPS: --"
    last_time = time.time()
    
    print("Starting game loop...")
    while running:
        # Track frame time
        current_time = time.time()
        dt = current_time - last_time
        last_time = current_time
        
        # Skip extreme dt values to avoid physics glitches
        if dt < 0.0001 or dt > 0.1:
            dt = 1/60
            
        frame_times.append(dt)
        if len(frame_times) > moving_avg_size:
            frame_times.pop(0)
        
        # Reset mouse click each frame
        mouse_clicked = False
        
        # Get mouse position
        mouse_pos = pygame.mouse.get_pos()
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if game_state == GameState.PLAYING:
                        # Return to main menu if in game
                        game_state = GameState.MAIN_MENU
                        # Show mouse cursor
                        pygame.mouse.set_visible(True)
                        mouse_visible = True
                        # Restart menu music
                        if pygame.mixer.get_init():
                            pygame.mixer.music.load(os.path.join("sounds", "menu_music.wav"))
                            pygame.mixer.music.play(-1)
                    else:
                        # Quit if in menu
                        running = False
                elif event.key == pygame.K_r and game_state == GameState.PLAYING:
                    gun.reload()
                # Weapon switching with number keys
                elif event.key == pygame.K_1 and game_state == GameState.PLAYING:
                    if current_weapon_type != 'pistol':
                        weapon_inventory[current_weapon_type] = gun.ammo
                        current_weapon_type = 'pistol'
                        gun = Gun('pistol')
                        gun.ammo = weapon_inventory['pistol']
                elif event.key == pygame.K_2 and game_state == GameState.PLAYING:
                    if current_weapon_type != 'shotgun':
                        weapon_inventory[current_weapon_type] = gun.ammo
                        current_weapon_type = 'shotgun'
                        gun = Gun('shotgun')
                        gun.ammo = weapon_inventory['shotgun']
                elif event.key == pygame.K_3 and game_state == GameState.PLAYING:
                    if current_weapon_type != 'rifle':
                        weapon_inventory[current_weapon_type] = gun.ammo
                        current_weapon_type = 'rifle'
                        gun = Gun('rifle')
                        gun.ammo = weapon_inventory['rifle']
                # Restart game if game over and Enter is pressed
                elif event.key == pygame.K_RETURN and game_state == GameState.GAME_OVER:
                    game_state = GameState.PLAYING
                    # Reset game state
                    player = Player(1.5, 1.5, 0)
                    # Reset weapon inventory
                    weapon_inventory = {
                        'pistol': WEAPON_CONFIGS['pistol']['max_ammo'],
                        'shotgun': WEAPON_CONFIGS['shotgun']['max_ammo'],
                        'rifle': WEAPON_CONFIGS['rifle']['max_ammo']
                    }
                    current_weapon_type = 'pistol'
                    gun = Gun('pistol')
                    enemy_manager = EnemyManager()
                    # Hide mouse cursor again
                    pygame.mouse.set_visible(False)
                    mouse_visible = False
                # Toggle path display with P
                elif event.key == pygame.K_p and game_state == GameState.PLAYING:
                    enemy_manager.show_paths = not enemy_manager.show_paths
                # Toggle mouse visibility with Tab
                elif event.key == pygame.K_TAB and game_state == GameState.PLAYING:
                    mouse_visible = not mouse_visible
                    pygame.mouse.set_visible(mouse_visible)
                    pygame.event.set_grab(not mouse_visible)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_clicked = True
                mouse_held = True
                if game_state == GameState.PLAYING and event.button == 1:  # Left mouse button
                    gun.fire()
            elif event.type == pygame.MOUSEBUTTONUP:
                mouse_held = False
        
        # Clear display surface
        display_surface.fill((0, 0, 0))
        
        # Handle game state
        if game_state == GameState.MAIN_MENU:
            # Update and draw main menu
            next_state = main_menu.update(mouse_pos, mouse_clicked)
            main_menu.draw(display_surface, dt)
            
            # Handle state transition
            if next_state == GameState.PLAYING:
                # Initialize game objects
                print("Loading textures...")
                textures = load_textures()
                print("Textures loaded.")

                player = Player(1.5, 1.5, 0)
                # Reset weapon inventory
                weapon_inventory = {
                    'pistol': WEAPON_CONFIGS['pistol']['max_ammo'],
                    'shotgun': WEAPON_CONFIGS['shotgun']['max_ammo'],
                    'rifle': WEAPON_CONFIGS['rifle']['max_ammo']
                }
                current_weapon_type = 'pistol'
                gun = Gun('pistol')
                enemy_manager = EnemyManager()

                # Hide mouse cursor for gameplay
                pygame.mouse.set_visible(False)
                mouse_visible = False
                pygame.event.set_grab(True)

                game_state = GameState.PLAYING
            elif next_state == GameState.OPTIONS:
                game_state = GameState.OPTIONS
            elif next_state is None:
                running = False
        
        elif game_state == GameState.OPTIONS:
            # Update and draw options menu
            next_state = options_menu.update(mouse_pos, mouse_clicked, mouse_held)
            options_menu.draw(display_surface)
            
            # Handle state transition
            if next_state == GameState.MAIN_MENU:
                game_state = GameState.MAIN_MENU
        
        elif game_state == GameState.PLAYING:
            # Get keyboard state
            keys = pygame.key.get_pressed()
            
            # Calculate mouse movement for rotation
            mouse_dx = pygame.mouse.get_rel()[0]
            
            # Check for space bar for shooting (auto fire if weapon supports it)
            if keys[pygame.K_SPACE]:
                if gun.config['auto']:
                    gun.fire()  # Keep firing if held down

            # Check for mouse button hold for auto fire
            if mouse_held and gun.config['auto']:
                gun.fire()
            
            # Update player with mouse movement
            player.update(keys, mouse_dx)
            
            # Update gun
            gun.update()
            
            # Update enemies
            enemy_manager.update(player, gun)
            
            # Check if player is dead
            if player.health <= 0:
                game_state = GameState.GAME_OVER
                # Show mouse cursor on game over
                pygame.mouse.set_visible(True)
                mouse_visible = True
                pygame.event.set_grab(False)
            
            # Cast rays and render 3D view to the display surface
            cast_rays(display_surface, player, textures, gun, enemy_manager)
            
            # Update FPS counter every second
            fps_counter += 1
            if pygame.time.get_ticks() - fps_timer > 500:  # Update twice a second
                fps = fps_counter * 2  # Since we're measuring half a second
                fps_display = f"FPS: {fps}"
                
                # Also calculate average frame time
                avg_frame_time = sum(frame_times) / len(frame_times) if frame_times else 0
                avg_frame_time_ms = avg_frame_time * 1000
                fps_display += f" | {avg_frame_time_ms:.1f}ms"
                
                fps_counter = 0
                fps_timer = pygame.time.get_ticks()
            
            # Draw FPS counter
            fps_text = pygame.font.SysFont(None, 24).render(fps_display, True, (255, 255, 255))
            display_surface.blit(fps_text, (10, 10))
            
            # Controls info
            controls_text = pygame.font.SysFont(None, 24).render(
                "WASD: Move | Mouse: Look | LMB/Space: Shoot | R: Reload | Tab: Mouse Toggle | Esc: Menu", 
                True, (255, 255, 255))
            display_surface.blit(controls_text, (10, SCREEN_HEIGHT - 30))
        
        elif game_state == GameState.GAME_OVER:
            # Draw game over screen
            font_large = pygame.font.SysFont(None, 72)
            font_medium = pygame.font.SysFont(None, 48)
            
            # Add a dark overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))  # Semi-transparent black
            display_surface.blit(overlay, (0, 0))
            
            # Draw game over text with red glow effect
            glow_factor = (math.sin(pygame.time.get_ticks() / 200) + 1) / 2  # 0 to 1 pulsing
            for offset in range(10, 0, -2):
                glow_size = 72 + offset
                glow_alpha = 100 - offset * 10
                glow_font = pygame.font.SysFont(None, glow_size)
                glow_text = glow_font.render("GAME OVER", True, (150, 0, 0))
                glow_text.set_alpha(glow_alpha)
                glow_rect = glow_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
                display_surface.blit(glow_text, glow_rect)
                
            game_over_text = font_large.render("GAME OVER", True, (255, 0, 0))
            display_surface.blit(game_over_text, 
                              (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 100))
            
            score_text = font_medium.render(f"Final Score: {player.score}", True, (255, 255, 255))
            display_surface.blit(score_text, 
                              (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))
            
            restart_text = font_medium.render("Press ENTER to restart", True, (255, 255, 255))
            display_surface.blit(restart_text, 
                              (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 100))
            
            menu_text = font_medium.render("Press ESC for menu", True, (255, 255, 255))
            display_surface.blit(menu_text, 
                               (SCREEN_WIDTH//2 - menu_text.get_width()//2, SCREEN_HEIGHT//2 + 160))
        
        # Blit the display surface to the screen
        screen.blit(display_surface, (0, 0))
        
        # Update display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(target_fps)

    # Clean up - restore mouse state
    pygame.mouse.set_visible(True)
    pygame.event.set_grab(False)
    pygame.quit()

if __name__ == "__main__":
    main()
