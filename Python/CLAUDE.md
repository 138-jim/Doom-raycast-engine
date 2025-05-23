# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Doom-style raycasting engine implemented in Python using Pygame. The engine creates a 3D-like environment from a 2D map using raycasting techniques. The project includes a fully-featured game with enemy AI using A* pathfinding, weapon mechanics, and game state management.

## Commands

### Running the Game

To run the game:

```bash
cd /root/Doom-raycast-engine/Python
python doom.py
```

### Dependencies Installation

Install the required dependencies:

```bash
pip install pygame numpy
pip install numba  # Optional, for performance improvements
```

## Code Architecture

### Main Components

1. **Raycasting Engine**
   - Implemented in `doom.py` and simplified version in `doomraycastengine.py`
   - Uses Digital Differential Analysis (DDA) algorithm for efficient wall detection
   - Applies textures with perspective correction and distance-based shading

2. **Enemy AI**
   - Uses A* pathfinding algorithm implemented in `astar.py`
   - Paths are recalculated periodically to adjust to player movement
   - Includes proper handling of diagonal movement and corner cutting

3. **Game State Management**
   - Main menu, gameplay, and game over states
   - Transitions between different game states

### Key Classes

1. **Player**: Manages player position, movement, and health
2. **Gun**: Handles weapon mechanics and rendering
3. **Enemy**: Individual enemy entities with pathfinding and behaviors
4. **EnemyManager**: Controls spawning and updating of all enemies
5. **PathNode**: Used in A* pathfinding algorithm
6. **MainMenu/OptionsMenu**: User interface management
7. **Button**: Interactive UI elements

### Performance Optimizations

- Optional Numba JIT compilation for critical functions
- Efficient texture mapping with bit masking
- Level of Detail (LOD) techniques for close walls

## Game Controls

- **W, A, S, D**: Move (forward, left, backward, right)
- **Mouse**: Look around
- **Left Mouse Button / Space**: Shoot
- **R**: Reload weapon
- **P**: Toggle enemy path display on minimap
- **Esc**: Return to menu (during gameplay) or quit (in menu)