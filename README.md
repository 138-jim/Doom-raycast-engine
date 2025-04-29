# Doom-Style Raycaster

A raycasting engine inspired by classic first-person shooters like Doom and Wolfenstein 3D. This project implements a fully-featured game with raycasting techniques, enemy AI with A* pathfinding, weapon mechanics, and game state management.

## Web Version

A JavaScript version of the game is now available for playing directly in your browser without any installation required.

### Running the Web Version

1. Open the `index.html` file in your web browser.
2. Click "START GAME" to begin playing.
3. First click on the game screen to enable mouse capture for looking around.

### Browser Compatibility

The web version works best in modern browsers:
- Chrome
- Firefox
- Edge
- Safari (latest versions)

## Python Version

The original Python implementation is also available in this repository.

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

## Python Requirements

- Python 3.6+
- pygame
- NumPy
- Optional: numba (for performance optimizations)

## Python Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/doom-raycast-engine.git
   cd doom-raycast-engine
   ```

2. Install the required dependencies:
   ```
   pip install pygame numpy
   ```

3. Optional: Install numba for JIT acceleration:
   ```
   pip install numba
   ```

4. Run the game:
   ```
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

### Raycasting Engine

The game uses a raycasting technique to create a 3D-like environment from a 2D map. The engine:

- Casts rays for each vertical screen column in the player's field of view
- Uses the Digital Differential Analysis (DDA) algorithm to efficiently find wall intersections
- Calculates wall heights based on perpendicular distance to prevent fisheye effect
- Applies textures with proper perspective correction
- Implements distance-based shading for depth perception

### Enemy AI

Enemies use the A* pathfinding algorithm to navigate to the player:

- Paths are recalculated periodically to adjust to player movement
- Pathfinding includes proper handling of diagonal movement and corner cutting
- Enemies select appropriate sprites based on viewing angle
- Includes attack mechanics when within range of the player

### Performance Optimizations

- Level of Detail (LOD) techniques for close walls
- Enemy spawning with path validation
- Efficient texture mapping with bit masking
- Optional numba JIT compilation for critical functions (Python version)
- Dynamic resolution scaling (Web version)

## Project Structure

```
doom-raycast-engine/
├── doom.py           # Main Python game file
├── doomraycastengine.py # Simplified Python raycaster
├── astar.py          # A* pathfinding implementation (Python)
├── astar.pseudo      # Pseudocode documentation for pathfinding
│
├── index.html        # Web version entry point
├── style.css         # Web styling
├── constants.js      # Game constants and settings
├── game.js           # Main game loop and state management
├── player.js         # Player logic
├── enemy.js          # Enemy AI and management
├── weapon.js         # Weapon mechanics
├── raycaster.js      # Core rendering engine
├── pathfinding.js    # A* implementation for JS
├── textures.js       # Texture management
│
├── sounds/           # Game sound effects
└── README.md         # This file
```

## Core Classes

### Python Version
- **Player**: Manages player position, movement, and health
- **Gun**: Handles weapon mechanics and rendering
- **Enemy**: Individual enemy entities with pathfinding and behaviors
- **EnemyManager**: Controls spawning and updating of all enemies
- **PathNode**: Used in A* pathfinding algorithm
- **MainMenu/OptionsMenu**: User interface management
- **Button**: Interactive UI elements

### Web Version
- **Game**: Main game loop and state management
- **Player**: Player movement and state
- **Weapon**: Weapon mechanics and rendering
- **Enemy/EnemyManager**: Enemy behavior and spawning
- **Raycaster**: 3D rendering engine
- **Pathfinding**: A* implementation
- **TextureManager**: Handles texture creation and access
- **AudioManager**: Sound effect and music management

## Extending the Game

### Adding New Weapons

Modify the `Gun`/`Weapon` class to include new weapon types with different properties.

### Creating New Maps

The game map is defined as a 2D array where:
- `0` represents empty space
- `1` or higher represents walls (different values can be different textures)

You can create new maps by modifying the `MAP` variable in `doom.py` or `constants.js`.

### Adding New Enemy Types

Extend the `Enemy` class or create subclasses with different behaviors and properties.

## Credits

- Raycasting engine inspired by [Lode's Raycasting Tutorial](https://lodev.org/cgtutor/raycasting.html)
- A* pathfinding algorithm based on standard implementations [Stanford's A*](https://theory.stanford.edu/~amitp/GameProgramming/AStarComparison.html)

## License

This project is open-source and available under the MIT License.