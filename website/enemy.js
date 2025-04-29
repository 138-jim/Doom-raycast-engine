// Enemy.js - Handles enemy AI, pathfinding, and rendering

class Enemy {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.hp = ENEMY_HP;
        this.attackCooldown = 0;
        this.hitEffect = 0; // Visual indicator when hit
        this.angle = 0; // Direction enemy is facing
        
        // Pathfinding attributes
        this.path = [];
        this.pathUpdateCounter = 0;
        this.currentPathIndex = 0;
    }
    
    // Update enemy state and movement
    update(player, pathfinding) {
        // Calculate direction to player
        const dx = player.x - this.x;
        const dy = player.y - this.y;
        const distance = Math.sqrt(dx*dx + dy*dy);
        
        // Calculate angle to player for sprite selection
        this.angle = Math.atan2(dy, dx) * 180 / Math.PI;
        
        // Don't move if hit recently (stunned)
        if (this.hitEffect > 0) {
            this.hitEffect -= 1;
            return false; // Not attacking
        }
        
        // Update pathfinding
        this.pathUpdateCounter += 1;
        if (this.pathUpdateCounter >= PATH_UPDATE_FREQUENCY || !this.path.length) {
            // Use A* to find path to player
            this.path = pathfinding.findPath(
                this.x, this.y, 
                player.x, player.y
            );
            
            this.pathUpdateCounter = 0;
            this.currentPathIndex = 0;
            
            // Limit path length to prevent excessive computation
            if (this.path.length > MAX_PATH_LENGTH) {
                this.path = this.path.slice(0, MAX_PATH_LENGTH);
            }
        }
        
        // Move along path if available
        if (this.path.length && this.currentPathIndex < this.path.length && distance > TILE_SIZE * 0.8) {
            const [targetX, targetY] = this.path[this.currentPathIndex];
            
            // Calculate direction to next path node
            const pathDx = targetX - this.x;
            const pathDy = targetY - this.y;
            const pathDistance = Math.sqrt(pathDx*pathDx + pathDy*pathDy);
            
            // If close enough to current waypoint, move to next
            if (pathDistance < TILE_SIZE / 2) {
                this.currentPathIndex += 1;
            } else {
                // Normalize direction
                let moveX = 0, moveY = 0;
                if (pathDistance > 0) {
                    moveX = pathDx / pathDistance;
                    moveY = pathDy / pathDistance;
                }
                
                // Move towards next path node
                const newX = this.x + moveX * ENEMY_SPEED * TILE_SIZE;
                const newY = this.y + moveY * ENEMY_SPEED * TILE_SIZE;
                
                // Map coordinates
                const mapX = Math.floor(newX / TILE_SIZE);
                const mapY = Math.floor(newY / TILE_SIZE);
                
                // Check if position is valid
                if (mapX >= 0 && mapX < MAP_WIDTH && mapY >= 0 && mapY < MAP_HEIGHT && MAP[mapY][mapX] === 0) {
                    this.x = newX;
                    this.y = newY;
                }
            }
        }
        
        // Handle attack cooldown
        if (this.attackCooldown > 0) {
            this.attackCooldown -= 1;
        }
        
        // Check if in attack range
        let attacking = false;
        if (distance < TILE_SIZE * ENEMY_ATTACK_RANGE && this.attackCooldown === 0) {
            attacking = true;
            this.attackCooldown = ENEMY_ATTACK_COOLDOWN;
        }
        
        return attacking;
    }
    
    // Take damage and return true if dead
    takeDamage(damage = 1) {
        this.hp -= damage;
        this.hitEffect = 5; // Visual effect duration
        return this.hp <= 0; // Return true if dead
    }
    
    // Get current sprite based on viewing angle
    getCurrentSprite(playerAngle) {
        // Normalize angle relative to player's view
        const relativeAngle = (this.angle - playerAngle + 180) % 360;
        
        // Front facing: -45 to 45 degrees
        if ((relativeAngle >= 315 || relativeAngle < 45)) {
            return textureManager.enemyTextures.front;
        }
        // Back: 135 to 225 degrees
        else if (relativeAngle >= 135 && relativeAngle < 225) {
            return textureManager.enemyTextures.back;
        }
        // Side: 45 to 135 degrees or 225 to 315 degrees
        else {
            // Choose which side to show and whether to flip based on angle
            return textureManager.enemyTextures.side;
        }
    }
    
    // Get information about whether the sprite should be flipped
    shouldFlipSprite(playerAngle) {
        const relativeAngle = (this.angle - playerAngle + 180) % 360;
        
        // If showing the side view, we need to determine if we should flip it
        if ((relativeAngle >= 45 && relativeAngle < 135) || 
            (relativeAngle >= 225 && relativeAngle < 315)) {
            // Flip when looking at left side (225-315 degrees)
            return relativeAngle >= 225 && relativeAngle < 315;
        }
        
        return false;
    }
    
    // Draw enemy on minimap
    drawOnMinimap(ctx, minimapScale, showPath = false) {
        const x = Math.floor(this.x / TILE_SIZE * minimapScale);
        const y = Math.floor(this.y / TILE_SIZE * minimapScale);
        
        // Enemy color (red, brighter if hit)
        const color = this.hitEffect > 0 ? 'rgb(255, 0, 0)' : 'rgb(200, 50, 50)';
        
        // Draw enemy dot
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw enemy facing direction
        const dirX = x + Math.cos(this.angle * Math.PI / 180) * 5;
        const dirY = y + Math.sin(this.angle * Math.PI / 180) * 5;
        
        ctx.strokeStyle = 'rgb(255, 200, 50)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(dirX, dirY);
        ctx.stroke();
        
        // Draw path if enabled
        if (showPath && this.path.length) {
            // Draw path nodes
            ctx.strokeStyle = 'rgba(0, 255, 255, 0.5)';
            ctx.beginPath();
            
            for (let i = 0; i < this.path.length - 1; i++) {
                const startX = Math.floor(this.path[i][0] / TILE_SIZE * minimapScale);
                const startY = Math.floor(this.path[i][1] / TILE_SIZE * minimapScale);
                const endX = Math.floor(this.path[i+1][0] / TILE_SIZE * minimapScale);
                const endY = Math.floor(this.path[i+1][1] / TILE_SIZE * minimapScale);
                
                if (i === 0) {
                    ctx.moveTo(startX, startY);
                }
                ctx.lineTo(endX, endY);
            }
            
            ctx.stroke();
            
            // Highlight current target node
            if (this.currentPathIndex < this.path.length) {
                const nodeX = Math.floor(this.path[this.currentPathIndex][0] / TILE_SIZE * minimapScale);
                const nodeY = Math.floor(this.path[this.currentPathIndex][1] / TILE_SIZE * minimapScale);
                
                ctx.fillStyle = 'rgb(0, 255, 0)';
                ctx.beginPath();
                ctx.arc(nodeX, nodeY, 2, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    }
}

// Enemy Manager class to handle spawning, updating, and rendering enemies
class EnemyManager {
    constructor(pathfinding, audioManager) {
        this.enemies = [];
        this.spawnCooldown = ENEMY_SPAWN_COOLDOWN;
        this.showPaths = false; // Toggle for showing paths on minimap
        this.spawnAttempts = 0; // Track consecutive spawn failures
        this.pathfinding = pathfinding;
        this.audioManager = audioManager;
    }
    
    // Update all enemies and check for player interaction
    update(player, weapon, deltaTime) {
        // Process existing enemies
        for (let i = this.enemies.length - 1; i >= 0; i--) {
            const enemy = this.enemies[i];
            
            // Update enemy and check if attacking
            const attacking = enemy.update(player, this.pathfinding);
            
            // If enemy is attacking player
            if (attacking) {
                const playerDied = player.takeDamage(ENEMY_DAMAGE);
                
                // Play hit sound
                if (this.audioManager) {
                    this.audioManager.playSound('playerHit');
                }
                
                if (playerDied) {
                    console.log("Player died!");
                    return true; // Player is dead
                }
            }
            
            // Check if player is shooting this enemy
            if (weapon.firing) {
                // Calculate vector from player to enemy
                const dx = enemy.x - player.x;
                const dy = enemy.y - player.y;
                const distance = Math.sqrt(dx*dx + dy*dy);
                
                // Check if player is looking at enemy (angle check)
                const enemyAngle = Math.atan2(dy, dx) * 180 / Math.PI;
                const playerAngle = player.angle % 360;
                
                // Calculate angle difference with proper wrapping
                let angleDiff = Math.abs(enemyAngle - playerAngle);
                angleDiff = Math.min(angleDiff, Math.abs(enemyAngle - playerAngle + 360), Math.abs(enemyAngle - playerAngle - 360));
                
                // Make the hit detection more forgiving
                const hitAngleThreshold = HALF_FOV * 1.2;
                const hitDistanceThreshold = TILE_SIZE * 8;
                
                // Check if enemy is in front of player and within view angle
                if (distance < hitDistanceThreshold && angleDiff < hitAngleThreshold) {
                    const enemyKilled = enemy.takeDamage();
                    
                    // Play hit sound
                    if (this.audioManager) {
                        this.audioManager.playSound('enemyHit');
                    }
                    
                    if (enemyKilled) {
                        // Play death sound
                        if (this.audioManager) {
                            this.audioManager.playSound('enemyDeath');
                        }
                        
                        this.enemies.splice(i, 1);
                        player.score += 100;
                        console.log(`Enemy killed! Total enemies: ${this.enemies.length}`);
                    }
                }
            }
        }
        
        // Spawn new enemies if needed
        this.spawnCooldown -= 1;
        if (this.spawnCooldown <= 0 && this.enemies.length < MAX_ENEMIES) {
            if (this.spawnEnemy(player)) {
                // Reset cooldown and attempts counter on successful spawn
                this.spawnCooldown = ENEMY_SPAWN_COOLDOWN;
                this.spawnAttempts = 0;
                console.log(`Enemy spawned! Total enemies: ${this.enemies.length}`);
            } else {
                // Increment failed attempts counter
                this.spawnAttempts += 1;
                
                // If we've had multiple failures, try again sooner but not immediately
                if (this.spawnAttempts > 3) {
                    this.spawnCooldown = Math.floor(ENEMY_SPAWN_COOLDOWN / 3);
                    
                    // Reset attempts to prevent continuous rapid attempts
                    if (this.spawnAttempts > 5) {
                        this.spawnAttempts = 0;
                    }
                } else {
                    // Regular cooldown for first few attempts
                    this.spawnCooldown = ENEMY_SPAWN_COOLDOWN;
                }
            }
        }
        
        return false; // Player is still alive
    }
    
    // Try to spawn a new enemy at a valid location
    spawnEnemy(player) {
        const maxAttempts = 30;
        let attempts = 0;
        
        while (attempts < maxAttempts) {
            attempts += 1;
            
            // Random map position (avoiding edges)
            const x = Math.floor(Math.random() * (MAP_WIDTH - 2)) + 1;
            const y = Math.floor(Math.random() * (MAP_HEIGHT - 2)) + 1;
            
            // Check if position is valid (not in a wall)
            if (MAP[y][x] === 0) {
                // Check if another enemy is already at this position
                let positionOccupied = false;
                for (const enemy of this.enemies) {
                    const enemyTileX = Math.floor(enemy.x / TILE_SIZE);
                    const enemyTileY = Math.floor(enemy.y / TILE_SIZE);
                    if (enemyTileX === x && enemyTileY === y) {
                        positionOccupied = true;
                        break;
                    }
                }
                
                if (positionOccupied) continue;
                
                // Check distance from player
                const dx = x * TILE_SIZE - player.x;
                const dy = y * TILE_SIZE - player.y;
                const distance = Math.sqrt(dx*dx + dy*dy);
                
                // Only spawn if far enough from player
                if (distance > TILE_SIZE * 3) {
                    // Check reachability: can this enemy reach the player from here?
                    const spawnPosX = x * TILE_SIZE + TILE_SIZE / 2; // Center of tile
                    const spawnPosY = y * TILE_SIZE + TILE_SIZE / 2;
                    
                    // Use pathfinding to check if a path exists
                    const path = this.pathfinding.findPath(spawnPosX, spawnPosY, player.x, player.y);
                    
                    // If a path exists, this is a valid spawn position
                    if (path.length > 1) { // Ensure path has at least 2 points
                        // Create a new enemy at this position
                        const newEnemy = new Enemy(spawnPosX, spawnPosY);
                        
                        // Give it the initial path to the player
                        newEnemy.path = path;
                        
                        this.enemies.push(newEnemy);
                        return true;
                    }
                }
            }
        }
        
        console.log(`Failed to spawn enemy after ${maxAttempts} attempts`);
        return false;
    }
    
    // Draw all enemies on the minimap
    drawOnMinimap(ctx, minimapScale) {
        for (const enemy of this.enemies) {
            enemy.drawOnMinimap(ctx, minimapScale, this.showPaths);
        }
    }
    
    // Toggle showing path lines on minimap
    togglePaths() {
        this.showPaths = !this.showPaths;
    }
}