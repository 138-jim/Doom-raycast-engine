# Python Doom-Style Raycaster

A Python-based raycasting engine inspired by classic first-person shooters like Doom and Wolfenstein 3D. This project implements a fully-featured game with raycasting techniques, enemy AI with A* pathfinding, weapon mechanics, and game state management.

![Game Screenshot Placeholder](placeholder_for_screenshot.png)

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
- Optional: numba (for performance optimizations)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/python-doom-raycaster.git
   cd python-doom-raycaster
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
- **Tab** - Toggle mouse capture
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
- Optional numba JIT compilation for critical functions

## Project Structure

```
python-doom-raycaster/
├── doom.py           # Main game file
├── astar.py          # A* pathfinding implementation
├── astar.pseudo      # Pseudocode documentation for pathfinding
├── sounds/           # Game sound effects
│   ├── gun_fire.wav
│   ├── gun_empty.wav
│   ├── gun_reload.wav
│   ├── button_click.wav
│   ├── button_hover.wav
│   └── menu_music.wav
└── README.md         # This file
```

## Core Classes

- **Player**: Manages player position, movement, and health
- **Gun**: Handles weapon mechanics and rendering
- **Enemy**: Individual enemy entities with pathfinding and behaviors
- **EnemyManager**: Controls spawning and updating of all enemies
- **PathNode**: Used in A* pathfinding algorithm
- **MainMenu/OptionsMenu**: User interface management
- **Button**: Interactive UI elements

## Extending the Game

### Adding New Weapons

Modify the `Gun` class to include new weapon types with different properties:

```python
class Gun:
    def __init__(self, gun_type="pistol"):
        self.gun_type = gun_type
        # Set properties based on gun type
        if gun_type == "pistol":
            self.ammo = 12
            self.damage = 1
        elif gun_type == "shotgun":
            self.ammo = 8
            self.damage = 3
        # ...
```

### Creating New Maps

The game map is defined as a 2D array where:
- `0` represents empty space
- `1` represents walls

You can create new maps by modifying the `MAP` variable in `doom.py`.

### Adding New Enemy Types

Extend the `Enemy` class or create subclasses with different behaviors and properties.

## Credits

- Raycasting engine inspired by [Lode's Raycasting Tutorial](https://lodev.org/cgtutor/raycasting.html)
- A* pathfinding algorithm based on standard implementations

## License

This project is open-source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.