# Doom-Style Raycaster

A raycasting engine inspired by classic first-person shooters like Doom and Wolfenstein 3D. This project implements a fully-featured game with raycasting techniques, enemy AI with A* pathfinding, weapon mechanics, and game state management.

## Python Implementation

This is a complete Python implementation of a Doom-style raycasting engine with sophisticated AI, weapon systems, and game mechanics.

## Features

- Fast raycasting engine with textured walls and distance shading
- Intelligent enemy AI using A* pathfinding algorithm
- Weapon system with shooting, recoil, and reloading mechanics
- Dynamic enemy spawning and management
- Player health and damage system
- Interactive minimap for navigation
- Complete game state management (menus, gameplay, game over)
- Performance optimizations for smooth gameplay
- Sound effects and visual feedback systems

## Requirements

- Python 3.6+
- pygame
- NumPy
- Optional: numba (for JIT acceleration - significantly improves performance)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/doom-raycast-engine.git
   cd doom-raycast-engine
   ```

2. Install the required dependencies:
   ```bash
   pip install pygame numpy
   ```

3. Optional but recommended: Install numba for JIT acceleration:
   ```bash
   pip install numba
   ```

4. Run the game:
   ```bash
   cd Python
   python doom.py
   ```

## How to Play

### Controls

- **W, A, S, D** - Move (forward, left, backward, right)
- **Mouse** - Look around
- **Left Mouse Button / Space** - Shoot
- **R** - Reload weapon
- **P** - Toggle enemy path display on minimap
- **Esc** - Return to menu (during gameplay) or quit (in menu)

### Gameplay Tips

- Use the minimap to navigate through the level
- Watch your ammo count and reload when necessary
- Keep track of your health and avoid taking damage
- Enemies will actively hunt you using pathfinding
- Score increases as you defeat enemies

## Technical Implementation

### Code Architecture

The main game file (`Python/doom.py`) is a monolithic implementation (~3000+ lines) containing the complete game in a single file for simplicity. It includes:

- **Screen dimensions**: 800x600 pixels
- **Field of View**: 60 degrees
- **Ray count**: 200 (rendering resolution)
- **Tile size**: 64 pixels
- **Map size**: 32x32 tiles (defined as 2D list where 0=walkable, 1=wall)

The code automatically detects if numba is available and uses JIT compilation for performance-critical functions. If numba is not installed, it falls back to standard Python implementations.

### Raycasting Engine

The game uses a raycasting technique to create a 3D-like environment from a 2D map:

- Casts rays for each vertical screen column in the player's field of view (200 rays)
- Uses the Digital Differential Analysis (DDA) algorithm to efficiently find wall intersections
- Calculates wall heights based on perpendicular distance to prevent fisheye effect
- Minimum wall distance (0.1) prevents extreme values when very close to walls
- Applies textures with proper perspective correction using bit masking
- Implements distance-based shading for depth perception

### Enemy AI

Enemies use the A* pathfinding algorithm to intelligently navigate to the player:

- **8-directional movement**: Including diagonals with proper cost calculation
  - Diagonal movement cost: 1.414 (√2)
  - Orthogonal movement cost: 1.0
- **Corner-cutting prevention**: Checks adjacent walls when moving diagonally
- **Manhattan distance heuristic**: `|x1-x2| + |y1-y2|`
- **Path recalculation**: Updated every PATH_UPDATE_FREQUENCY frames (10) to track player movement
- **Max iterations limit**: 1000 iterations to prevent infinite loops
- **Sprite angle selection**: Enemies display different sprites based on viewing angle
- **Attack mechanics**: Attack when within ENEMY_ATTACK_RANGE (1.5 tiles) with cooldown system (60 frames)

### Performance Optimizations

- Level of Detail (LOD) techniques for close walls and sprites
- Maximum wall height limit (SCREEN_HEIGHT * 2.5) prevents excessive rendering
- Maximum sprite size limit (SCREEN_HEIGHT * 1.2)
- Enemy spawning with path validation to ensure reachable positions
- Efficient texture mapping with bit masking and numpy arrays
- Optional numba JIT compilation for critical math operations (significantly improves performance)
- Path updates limited to every PATH_UPDATE_FREQUENCY frames (10) to reduce computational overhead

## Project Structure

```
doom-raycast-engine/
├── Python/
│   ├── doom.py                    # Main game file (~3000+ lines)
│   ├── doomraycastengine.py       # Simplified raycaster demo (109 lines)
│   ├── astar.py                   # Standalone A* pathfinding implementation
│   ├── astar.pseudo               # Pseudocode documentation for pathfinding
│   ├── weapon_system.pseudo       # Weapon system documentation
│   ├── weapon_system_changes.diff # Weapon system change history
│   └── sounds/                    # Sound effects directory
│
├── sounds/                        # Game sound effects (.wav files)
│   ├── button_click.wav
│   ├── button_hover.wav
│   ├── gun_empty.wav
│   ├── gun_fire.wav
│   ├── gun_reload.wav
│   └── menu_music.wav
│
├── CLAUDE.md                      # Developer guidance for Claude Code
└── README.md                      # This file
```

## Core Classes (Python/doom.py)

- **PathNode**: Node class for A* pathfinding algorithm
- **Gun**: Weapon rendering, recoil, ammo management, and reload mechanics
- **Player**: Position, movement, rotation, health, and collision detection
- **Enemy**: Individual enemy entity with AI, pathfinding, sprite rendering, and attack mechanics
- **EnemyManager**: Spawns enemies, validates spawn positions, updates all enemies, and handles rendering
- **GameState**: Enum defining game states (MENU, PLAYING, GAME_OVER)
- **Button**: UI button components for menus
- **MainMenu**: Start screen and navigation
- **OptionsMenu**: Settings interface

## Extending the Game

### Adding New Weapons

Modify the `Gun` class in `Python/doom.py` to include new weapon types with different properties. See `weapon_system.pseudo` for detailed documentation on the weapon system.

### Creating New Maps

The game map is defined as a 2D array where:
- `0` represents empty/walkable space
- `1` represents walls

You can create new maps by modifying the `MAP` variable in `Python/doom.py`. The map must be rectangular and surrounded by walls (border of 1s) for proper collision detection.

### Adjusting Difficulty

Modify enemy constants in `Python/doom.py`:
- `ENEMY_HP`: Hits to kill (default: 3)
- `ENEMY_SPEED`: Movement speed (default: 0.08)
- `ENEMY_DAMAGE`: Damage per attack (default: 10)
- `MAX_ENEMIES`: Maximum simultaneous enemies (default: 5)
- `ENEMY_SPAWN_COOLDOWN`: Frames between spawns (default: 100)

### Weapon Tuning

Modify weapon constants in `Python/doom.py`:
- `WEAPON_MAX_AMMO`: Magazine capacity (default: 12)
- `WEAPON_RELOAD_TIME`: Reload duration in frames (default: 150)
- `WEAPON_FIRE_COOLDOWN`: Frames between shots (default: 20)
- `WEAPON_RECOIL`: Visual recoil amount (default: 10)

## Supporting Files

- **doomraycastengine.py**: A simplified 109-line raycaster demo with basic wall rendering and no game logic - useful for understanding the core raycasting concept
- **astar.py**: Standalone A* pathfinding implementation with detailed documentation
- **astar.pseudo**: Pseudocode documentation explaining the A* algorithm step-by-step
- **weapon_system.pseudo**: Detailed documentation of the weapon system mechanics
- **weapon_system_changes.diff**: Change history for weapon system modifications
- **CLAUDE.md**: Developer guidance specifically for Claude Code assistance on this project

## Development Notes

### Code Style
- The Python implementation is monolithic (single large file) for simplicity
- No external configuration files or build systems required
- Includes comprehensive error handling

### Testing Changes
Simply run `cd Python && python doom.py` after making changes. The game includes error handling and will print numba availability status on startup.

### Common Issues
- **Enemies spawn inside walls**: Check MAP boundaries and spawn validation logic in EnemyManager
- **Performance issues**: Install numba for significant performance improvement, or reduce RAY_COUNT
- **Path display toggle**: Press P key to visualize enemy pathfinding on the minimap (useful for debugging)

### Debugging Tools
- **Minimap**: Shows player position, enemies, and walls
- **Path visualization**: Toggle with P key to see enemy pathfinding routes
- **Console output**: Prints numba availability and initialization messages

## Credits

- Raycasting engine inspired by [Lode's Raycasting Tutorial](https://lodev.org/cgtutor/raycasting.html)
- A* pathfinding algorithm based on standard implementations [Stanford's A*](https://theory.stanford.edu/~amitp/GameProgramming/AStarComparison.html)

## License

This project is open-source and available under the MIT License.