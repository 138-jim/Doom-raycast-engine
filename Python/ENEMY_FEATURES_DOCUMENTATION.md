# Enemy Variety and States Implementation

This document details the exact locations where the new enemy variety and state features were implemented in the Doom raycasting engine.

## Overview of Features Added

### 1. Enemy Variety - Different Types
- **Scout**: Fast, low health, quick attacks (Green sprites)
- **Tank**: Slow, high health, heavy damage (Gray sprites) 
- **Ranged**: Medium speed, long attack range (Purple sprites)

### 2. Enemy States - Behavioral System
- **Patrol**: Default state, follows patrol routes around spawn point
- **Alert**: Spotted player, moving to attack
- **Search**: Lost sight of player, searching last known position
- **Attack**: In range and attacking player

## Code Locations and Changes

### 1. Constants and Enums (Lines 15-94)

**File**: `doom.py`
**Lines**: 15-25, 69-94

Added enemy type and state enums:
```python
class EnemyType(Enum):
    SCOUT = "scout"
    TANK = "tank" 
    RANGED = "ranged"

class EnemyState(Enum):
    PATROL = "patrol"
    ALERT = "alert"
    SEARCH = "search"
    ATTACK = "attack"
```

Added type-specific constants:
- Scout stats (lines 70-74)
- Tank stats (lines 76-80)  
- Ranged stats (lines 82-86)
- State behavior settings (lines 88-94)

### 2. Enemy Class Complete Rewrite (Lines 629-983)

**File**: `doom.py`
**Lines**: 629-983

The entire Enemy class was rewritten to support:

#### Constructor (Lines 630-667)
- Takes optional `enemy_type` parameter
- Generates random type if not specified
- Sets up state system and patrol routes
- Calls `_set_type_stats()` and `_generate_patrol_route()`

#### Type Stats Method (Lines 669-690)
```python
def _set_type_stats(self):
    """Set stats based on enemy type"""
```
Sets speed, HP, damage, attack range, and cooldown based on enemy type.

#### Patrol Route Generation (Lines 692-717)
```python
def _generate_patrol_route(self):
    """Generate a random patrol route around spawn point"""
```
Creates 2-4 random patrol points within PATROL_RADIUS of spawn location.

#### Main Update Method (Lines 719-760)
```python
def update(self, player, other_enemies=None):
```
Now coordinates state system, line of sight, pathfinding, and movement.

#### Line of Sight System (Lines 762-785)
```python
def _can_see_player(self, player):
    """Check if enemy can see the player using line of sight"""
```
Raycasting-based visibility check with range limits.

#### State Management (Lines 787-847)
```python
def _update_state(self, player, player_in_sight, other_enemies):
    """Update enemy state based on conditions"""
```
Handles all state transitions and timers.

#### Group Coordination (Lines 849-867)
```python
def _alert_nearby_enemies(self, other_enemies, player):
    """Alert nearby enemies when this enemy spots the player"""
```
When one enemy spots the player, nearby enemies become alert.

#### Smart Pathfinding (Lines 869-911)
```python
def _update_pathfinding(self, player):
    """Update pathfinding based on current state"""
```
Different pathfinding behavior per state:
- Patrol: Move between patrol points
- Alert/Attack: Path to player
- Search: Path to last known player position

#### State-Based Movement (Lines 913-953)
```python
def _move(self):
    """Move enemy along current path"""
```
Applies speed multipliers based on state (faster when alert, slower when searching).

#### Enhanced Damage Response (Lines 973-983)
When hit, enemies become more alert and may change states.

### 3. Sprite System Updates (Lines 996-1095)

**File**: `doom.py`
**Lines**: 996-1095

#### Updated Sprite Creation (Lines 996-1095)
```python
def create_enemy_sprite(enemy_type=EnemyType.SCOUT):
```
Different colors per enemy type:
- Scout: Green (lines 1004-1006)
- Tank: Gray (lines 1007-1009)
- Ranged: Purple (lines 1010-1012)

### 4. Enemy Manager Updates (Lines 1200-1337)

**File**: `doom.py`
**Lines**: 1200-1337

#### Updated Enemy Processing (Line 1209)
```python
attacking = enemy.update(player, self.enemies)
```
Now passes all enemies for group coordination.

#### Dynamic Damage System (Line 1213)
```python
player_died = player.take_damage(enemy.damage)
```
Uses enemy-specific damage values instead of global constant.

#### Weighted Enemy Spawning (Lines 1315-1333)
```python
enemy_type_weights = {
    EnemyType.SCOUT: 40,   # 40% chance
    EnemyType.TANK: 30,    # 30% chance  
    EnemyType.RANGED: 30   # 30% chance
}
```
Random weighted selection of enemy types when spawning.

### 5. Enhanced Minimap Display (Lines 1339-1383)

**File**: `doom.py`
**Lines**: 1339-1383

#### State and Type Visualization (Lines 1345-1367)
Different colors show enemy states and types:
- White: When hit
- Red: Attacking
- Orange: Alert  
- Yellow: Searching
- Green: Scout (patrolling)
- Gray: Tank (patrolling)
- Magenta: Ranged (patrolling)

Tank enemies show as larger dots (3px vs 2px).

## Game Balance Changes

### Enemy Count
- Increased MAX_ENEMIES from 5 to 8 (line 64)

### Type Distribution
- 40% Scouts (fast harassment)
- 30% Tanks (damage sponges)
- 30% Ranged (long-range threat with 6.0 tile attack range)

## Key Behavioral Features

### 1. Improved Enemy Behavior (Updated)
- Enemies patrol between two random points on the map (not just around spawn)
- Immediately pursue player when spotted (no alert delay)
- Lose player after time and search last known position
- Return to patrol if search fails

### 2. Group Coordination
- When one enemy spots player, nearby enemies (within 4 tiles) become alert
- Shared threat information prevents easy exploitation

### 3. State-Based Speed (Updated)
- Attacking enemies move 30% faster (immediate pursuit)
- Alert enemies move 20% faster  
- Searching enemies move 20% slower
- Creates dynamic encounter pacing

### 4. Line of Sight System
- Enemies can't see through walls
- Limited sight range (6 tiles)
- Realistic enemy awareness

## Recent Updates

### Complete Patrol System Rebuild
- **Removed old individual patrol system** completely
- **Built new group-based patrol system** from scratch
- **PatrolGroup class** manages coordinated group movement (lines 27-137)
- **Formation-based movement** with tactical positioning
- **Circuit patrol routes** - groups follow 3-4 waypoint circuits

### Extended Ranged Enemy Range  
- Ranged (purple) enemies now have 6.0 tile attack range instead of 4.0 (line 97)
- Makes them more dangerous at long distance

### Improved Enemy Health
- Scout HP increased from 2 to 3 (line 83)
- Tank HP doubled from 6 to 12 (line 89) - now much tankier
- Makes tanks require multiple shots to kill

### DDA-Based Line of Sight Detection
- **Accurate DDA raycasting** - same algorithm as the game's wall rendering (lines 789-886)
- **Pixel-perfect detection** - matches exactly how the game renders walls
- **Proper wall collision** - uses identical map tile checking as main rendering
- **Optimized performance** - efficient grid traversal with step limiting
- **Consistent with game physics** - no more detection discrepancies

### Group-Based Patrol System (REBUILT)
- **PatrolGroup class** - Complete group management system (lines 27-137)
- **3 patrol groups** with up to 3 enemies each across the map (lines 106-111)
- **Formation movement** - Enemies maintain tactical formations while patrolling
- **Coordinated patrol routes** - Groups move together through 3-4 waypoints in circuits
- **Dynamic group management** - Automatic member assignment and formation adjustment

### Immediate Pursuit
- Enemies immediately go to ATTACK state when player is spotted (lines 813-822)
- No delay through ALERT state
- 30% speed boost during pursuit (lines 945-946)
- Group coordination also triggers immediate attack (line 873)

## Testing the Features

Run the game and observe:
1. Different colored enemy types on minimap and in 3D view
2. **Coordinated patrol groups** - 3-enemy squads moving in tactical formations
3. **Formation patrolling** - enemies maintain spread/triangle formations while moving
4. **Circuit routes** - groups patrol in circuits through 3-4 waypoints
5. **Pixel-perfect detection** - enemies spot you with the same accuracy as wall rendering
6. **Consistent line of sight** - no more spotting through walls that should block vision
7. Immediate red color change and faster pursuit when enemies spot you
8. **Tankier enemies** - tanks now take multiple shots to kill (12 HP vs 6 HP)
9. Extended range attacks from purple enemies (6 tile range)
10. Group alerting triggers immediate pursuit from nearby enemies
11. **Dynamic group management** - when enemies die, formations automatically adjust

The implementation provides **coordinated group AI** with tactical formations, **pixel-perfect DDA raycasting**, and **proper military-style patrol behavior**. Groups move as cohesive units with realistic tactical positioning.