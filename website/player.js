// Player.js - Handles player movement, collision, and state

class Player {
    constructor(x, y, angle = 0) {
        // Position (in map coordinates)
        this.x = x * TILE_SIZE + TILE_SIZE / 2;
        this.y = y * TILE_SIZE + TILE_SIZE / 2;
        this.angle = angle;
        
        // Movement settings
        this.movementSpeed = 5;
        this.rotationSpeed = 3;
        this.mouseSensitivity = 0.2;
        
        // Player stats
        this.health = PLAYER_MAX_HEALTH;
        this.hitEffect = 0; // For red flash when hit
        this.score = 0;
        
        // Input state
        this.keys = {
            forward: false,
            backward: false,
            strafeLeft: false,
            strafeRight: false,
            rotateLeft: false,
            rotateRight: false
        };
    }
    
    // Handle taking damage and return whether player died
    takeDamage(damage) {
        this.health -= damage;
        this.hitEffect = 10; // Duration of red effect
        return this.health <= 0;
    }
    
    // Set key state based on keyboard input
    setKey(key, isPressed) {
        switch(key) {
            case 'w': this.keys.forward = isPressed; break;
            case 's': this.keys.backward = isPressed; break;
            case 'a': this.keys.strafeLeft = isPressed; break;
            case 'd': this.keys.strafeRight = isPressed; break;
            case 'ArrowLeft': this.keys.rotateLeft = isPressed; break;
            case 'ArrowRight': this.keys.rotateRight = isPressed; break;
        }
    }
    
    // Update player position and state based on input
    update(deltaTime, mouseDx = 0) {
        // Mouse rotation
        this.angle += mouseDx * this.mouseSensitivity;
        
        // Keyboard rotation (as backup)
        if (this.keys.rotateLeft) {
            this.angle -= this.rotationSpeed;
        }
        if (this.keys.rotateRight) {
            this.angle += this.rotationSpeed;
        }
        
        // Normalize angle to 0-360 degrees
        this.angle = (this.angle + 360) % 360;
        
        // Convert angle to radians for movement calculation
        const radAngle = this.angle * Math.PI / 180;
        
        // Calculate movement direction
        let dx = 0, dy = 0;
        
        // Forward and backward
        if (this.keys.forward) {
            dx += Math.cos(radAngle) * this.movementSpeed;
            dy += Math.sin(radAngle) * this.movementSpeed;
        }
        if (this.keys.backward) {
            dx -= Math.cos(radAngle) * this.movementSpeed;
            dy -= Math.sin(radAngle) * this.movementSpeed;
        }
        
        // Strafing left and right
        if (this.keys.strafeLeft) {
            dx += Math.cos(radAngle - Math.PI/2) * this.movementSpeed;
            dy += Math.sin(radAngle - Math.PI/2) * this.movementSpeed;
        }
        if (this.keys.strafeRight) {
            dx += Math.cos(radAngle + Math.PI/2) * this.movementSpeed;
            dy += Math.sin(radAngle + Math.PI/2) * this.movementSpeed;
        }
        
        // Check collision before moving
        this.moveWithCollision(dx, dy);
        
        // Update hit effect
        if (this.hitEffect > 0) {
            this.hitEffect -= 1;
        }
    }
    
    // Move with collision detection
    moveWithCollision(dx, dy) {
        // Calculate new position
        const newX = this.x + dx;
        const newY = this.y + dy;
        
        // Check if the new position is inside a wall
        const mapX = Math.floor(newX / TILE_SIZE);
        const mapY = Math.floor(newY / TILE_SIZE);
        
        // Make sure we're within map bounds
        if (mapX >= 0 && mapX < MAP_WIDTH && mapY >= 0 && mapY < MAP_HEIGHT) {
            // Split movement to allow sliding along walls
            // Try X movement
            const newXMapY = Math.floor(this.y / TILE_SIZE);
            if (mapX >= 0 && mapX < MAP_WIDTH && MAP[newXMapY][mapX] === 0) {
                this.x = newX;
            }
            
            // Try Y movement
            const newYMapX = Math.floor(this.x / TILE_SIZE);
            if (mapY >= 0 && mapY < MAP_HEIGHT && MAP[mapY][newYMapX] === 0) {
                this.y = newY;
            }
        }
    }
    
    // Draw player on minimap
    drawOnMinimap(ctx, minimapScale) {
        const playerX = this.x / TILE_SIZE * minimapScale;
        const playerY = this.y / TILE_SIZE * minimapScale;
        
        // Draw player dot
        ctx.fillStyle = 'red';
        ctx.beginPath();
        ctx.arc(playerX, playerY, 3, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw direction line
        const lineLength = 10;
        const dirX = playerX + Math.cos(this.angle * Math.PI / 180) * lineLength;
        const dirY = playerY + Math.sin(this.angle * Math.PI / 180) * lineLength;
        
        ctx.strokeStyle = 'red';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(playerX, playerY);
        ctx.lineTo(dirX, dirY);
        ctx.stroke();
        
        // Draw FOV cone
        const leftAngle = (this.angle - HALF_FOV) * Math.PI / 180;
        const rightAngle = (this.angle + HALF_FOV) * Math.PI / 180;
        const fovLength = 15;
        
        const leftX = playerX + Math.cos(leftAngle) * fovLength;
        const leftY = playerY + Math.sin(leftAngle) * fovLength;
        const rightX = playerX + Math.cos(rightAngle) * fovLength;
        const rightY = playerY + Math.sin(rightAngle) * fovLength;
        
        // Draw FOV as semi-transparent triangle
        ctx.fillStyle = 'rgba(255, 255, 0, 0.2)';
        ctx.beginPath();
        ctx.moveTo(playerX, playerY);
        ctx.lineTo(leftX, leftY);
        ctx.lineTo(rightX, rightY);
        ctx.closePath();
        ctx.fill();
    }
}