// Raycaster.js - Core raycasting engine for rendering the 3D view

class Raycaster {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // Resize canvas to match screen dimensions
        this.resize();
        
        // Create buffer for wall strips
        this.wallBuffer = this.ctx.createImageData(RAY_COUNT, SCREEN_HEIGHT);
        
        // Performance settings
        this.skipRays = 1; // Render every nth ray
        this.quality = 1; // Rendering quality multiplier (lower for better performance)
        
        // Create sky and floor colors
        this.createSkyGradient();
        this.createFloorGradient();
    }
    
    // Update canvas size to match container
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Update gradients when resizing
        if (this.ctx) {
            this.createSkyGradient();
            this.createFloorGradient();
        }
    }
    
    // Create sky gradient
    createSkyGradient() {
        const skyHeight = Math.floor(this.canvas.height / 2);
        this.skyGradient = this.ctx.createLinearGradient(0, 0, 0, skyHeight);
        this.skyGradient.addColorStop(0, "rgb(50, 50, 200)");
        this.skyGradient.addColorStop(1, "rgb(100, 100, 255)");
    }
    
    // Create floor gradient
    createFloorGradient() {
        const floorStart = Math.floor(this.canvas.height / 2);
        this.floorGradient = this.ctx.createLinearGradient(0, floorStart, 0, this.canvas.height);
        this.floorGradient.addColorStop(0, "rgb(40, 40, 40)");
        this.floorGradient.addColorStop(1, "rgb(80, 80, 80)");
    }
    
    // Draw sky and floor backgrounds
    drawBackground() {
        // Draw sky
        this.ctx.fillStyle = this.skyGradient;
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height / 2);
        
        // Draw floor
        this.ctx.fillStyle = this.floorGradient;
        this.ctx.fillRect(0, this.canvas.height / 2, this.canvas.width, this.canvas.height / 2);
    }
    
    // Cast rays and render the 3D scene
    render(player, enemies = [], showMinimap = true) {
        // Clear canvas
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw sky and floor
        this.drawBackground();
        
        // Prepare for raycasting
        const screenHeight = this.canvas.height;
        const screenWidth = this.canvas.width;
        const halfHeight = screenHeight / 2;
        const startAngle = player.angle - HALF_FOV;
        const stripWidth = WALL_STRIP_WIDTH * this.quality;
        
        // For sprite rendering
        const zBuffer = new Array(RAY_COUNT).fill(Infinity);
        
        // Cast rays
        for (let ray = 0; ray < RAY_COUNT; ray += this.skipRays) {
            // Calculate ray angle
            const rayAngle = (startAngle + (ray / RAY_COUNT) * FOV) * Math.PI / 180;
            
            // Ray direction vector
            const rayDirX = Math.cos(rayAngle);
            const rayDirY = Math.sin(rayAngle);
            
            // DDA Algorithm 
            let mapX = Math.floor(player.x / TILE_SIZE);
            let mapY = Math.floor(player.y / TILE_SIZE);
            
            // Calculate delta distance
            const deltaDistX = Math.abs(1 / rayDirX);
            const deltaDistY = Math.abs(1 / rayDirY);
            
            // Initial step direction
            const stepX = rayDirX >= 0 ? 1 : -1;
            const stepY = rayDirY >= 0 ? 1 : -1;
            
            // Calculate initial side distance
            let sideDistX, sideDistY;
            
            if (rayDirX < 0) {
                sideDistX = (player.x / TILE_SIZE - mapX) * deltaDistX;
            } else {
                sideDistX = (mapX + 1.0 - player.x / TILE_SIZE) * deltaDistX;
            }
            
            if (rayDirY < 0) {
                sideDistY = (player.y / TILE_SIZE - mapY) * deltaDistY;
            } else {
                sideDistY = (mapY + 1.0 - player.y / TILE_SIZE) * deltaDistY;
            }
            
            // Perform DDA
            let hit = false;
            let side = 0; // 0 for x-side, 1 for y-side
            
            while (!hit) {
                // Jump to next map square
                if (sideDistX < sideDistY) {
                    sideDistX += deltaDistX;
                    mapX += stepX;
                    side = 0;
                } else {
                    sideDistY += deltaDistY;
                    mapY += stepY;
                    side = 1;
                }
                
                // Check if ray is out of bounds
                if (mapX < 0 || mapX >= MAP_WIDTH || mapY < 0 || mapY >= MAP_HEIGHT) {
                    break;
                }
                
                // Check if ray hit a wall
                if (MAP[mapY][mapX] > 0) {
                    hit = true;
                }
            }
            
            // If we hit a wall, draw a vertical wall slice
            if (hit) {
                // Calculate perpendicular wall distance to avoid fisheye effect
                let perpWallDist;
                if (side === 0) {
                    perpWallDist = (mapX - player.x / TILE_SIZE + (1 - stepX) / 2) / rayDirX;
                } else {
                    perpWallDist = (mapY - player.y / TILE_SIZE + (1 - stepY) / 2) / rayDirY;
                }
                
                // Store distance in z-buffer for sprite rendering
                zBuffer[ray] = perpWallDist;
                
                // Calculate wall height
                const lineHeight = Math.floor(screenHeight / perpWallDist);
                
                // Calculate drawing boundaries
                let drawStart = Math.max(0, halfHeight - lineHeight / 2);
                let drawEnd = Math.min(screenHeight - 1, halfHeight + lineHeight / 2);
                
                // Get wall texture
                const wallTexture = MAP[mapY][mapX] - 1; // Convert to 0-based index
                
                // Calculate where exactly the wall was hit
                let wallX;
                if (side === 0) {
                    wallX = player.y / TILE_SIZE + perpWallDist * rayDirY;
                } else {
                    wallX = player.x / TILE_SIZE + perpWallDist * rayDirX;
                }
                wallX -= Math.floor(wallX);
                
                // X coordinate on the texture
                let texX = Math.floor(wallX * TILE_SIZE);
                if ((side === 0 && rayDirX > 0) || (side === 1 && rayDirY < 0)) {
                    texX = TILE_SIZE - texX - 1;
                }
                
                // Calculate shade based on distance and side
                const baseShadeFactor = side === 1 ? 0.8 : 1.0;
                
                // Distance fog effect
                const distanceFactor = Math.min(1.0, perpWallDist / MAX_DEPTH);
                const shadeFactor = baseShadeFactor * (1.0 - distanceFactor * 0.6);
                
                // Draw vertical wall strip
                const stripHeight = drawEnd - drawStart;
                if (stripHeight > 0) {
                    // Create a scaled vertical strip of the texture
                    // Calculate texture step for proper scaling
                    const step = TILE_SIZE / lineHeight;
                    
                    // Starting texture position based on where drawing begins
                    let texPos = (drawStart - halfHeight + lineHeight / 2) * step;
                    
                    // For each pixel in the strip
                    for (let y = drawStart; y < drawEnd; y++) {
                        // Get the y-coordinate on the texture
                        const texY = Math.floor(texPos) % TILE_SIZE;
                        texPos += step;
                        
                        // Get the pixel color from the texture
                        const [r, g, b] = textureManager.getTexturePixel('wall', wallTexture, texX, texY);
                        
                        // Apply shading
                        const shadedR = Math.floor(r * shadeFactor);
                        const shadedG = Math.floor(g * shadeFactor);
                        const shadedB = Math.floor(b * shadeFactor);
                        
                        // Draw the pixel
                        this.ctx.fillStyle = `rgb(${shadedR}, ${shadedG}, ${shadedB})`;
                        this.ctx.fillRect(ray * stripWidth, y, stripWidth, 1);
                    }
                }
            } else {
                // If no wall was hit, set z-buffer to maximum depth
                zBuffer[ray] = MAX_DEPTH;
            }
        }
        
        // Render enemies (sprites)
        this.renderEnemies(player, enemies, zBuffer);
        
        // Draw minimap if enabled
        if (showMinimap) {
            this.drawMinimap(player, enemies);
        }
        
        // Draw hit effect (red overlay when player is hit)
        if (player.hitEffect > 0) {
            const alpha = Math.min(0.6, player.hitEffect / 10 * 0.6);
            this.ctx.fillStyle = `rgba(255, 0, 0, ${alpha})`;
            this.ctx.fillRect(0, 0, screenWidth, screenHeight);
        }
    }
    
    // Render enemies using sprite casting technique
    renderEnemies(player, enemies, zBuffer) {
        // Convert player's angle to radians
        const playerAngleRad = player.angle * Math.PI / 180;
        
        // Sort enemies by distance (render far to near for proper occlusion)
        const enemiesWithDist = enemies.map(enemy => {
            const dx = enemy.x - player.x;
            const dy = enemy.y - player.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            return { enemy, dist };
        });
        
        // Sort by distance (far to near)
        enemiesWithDist.sort((a, b) => b.dist - a.dist);
        
        // Render each enemy
        for (const { enemy, dist } of enemiesWithDist) {
            // Skip if the sprite is too far
            if (dist > MAX_DEPTH * TILE_SIZE) continue;
            
            // Calculate sprite angle relative to player's view
            const spriteAngle = Math.atan2(enemy.y - player.y, enemy.x - player.x) - playerAngleRad;
            
            // Normalize angle to -π to π
            let normalizedAngle = spriteAngle;
            while (normalizedAngle > Math.PI) normalizedAngle -= 2 * Math.PI;
            while (normalizedAngle < -Math.PI) normalizedAngle += 2 * Math.PI;
            
            // Check if sprite is in field of view (with some margin)
            if (Math.abs(normalizedAngle) > HALF_FOV_RAD * 1.5) continue;
            
            // Calculate sprite screen position
            const spriteScreenX = Math.floor((0.5 + normalizedAngle / FOV_RAD) * this.canvas.width);
            
            // Calculate sprite size based on distance
            const spriteSize = Math.min(this.canvas.height, Math.floor(this.canvas.height / (dist / TILE_SIZE)));
            
            // Calculate sprite drawing boundaries
            const spriteTop = Math.max(0, Math.floor(this.canvas.height / 2 - spriteSize / 2));
            const spriteBottom = Math.min(this.canvas.height, Math.floor(this.canvas.height / 2 + spriteSize / 2));
            
            // Calculate horizontal span of the sprite
            const spriteWidth = spriteSize;
            const spriteLeft = Math.floor(spriteScreenX - spriteWidth / 2);
            const spriteRight = spriteLeft + spriteWidth;
            
            // Get the appropriate sprite based on view angle
            const sprite = enemy.getCurrentSprite(player.angle);
            const shouldFlip = enemy.shouldFlipSprite(player.angle);
            
            // Draw sprite only where it's visible in front of walls
            for (let x = Math.max(0, spriteLeft); x < Math.min(this.canvas.width, spriteRight); x++) {
                // Find the ray that corresponds to this x position
                const rayIdx = Math.floor(x / WALL_STRIP_WIDTH / this.quality) * this.skipRays;
                
                // Ensure ray index is within bounds
                if (rayIdx >= 0 && rayIdx < zBuffer.length) {
                    // Only draw if sprite is closer than the wall at this ray
                    if (dist / TILE_SIZE < zBuffer[rayIdx]) {
                        // Calculate the x position on the sprite texture
                        let texX = Math.floor((x - spriteLeft) / spriteWidth * TILE_SIZE);
                        
                        // Flip texture if needed
                        if (shouldFlip) {
                            texX = TILE_SIZE - texX - 1;
                        }
                        
                        // Create a surface for the sprite strip
                        const stripHeight = spriteBottom - spriteTop;
                        
                        // Draw vertical strip of the sprite
                        const stripWidth = WALL_STRIP_WIDTH * this.quality;
                        
                        // Get sprite data
                        const tempCanvas = document.createElement('canvas');
                        tempCanvas.width = 1;
                        tempCanvas.height = stripHeight;
                        const tempCtx = tempCanvas.getContext('2d');
                        
                        // Draw sprite strip to temporary canvas
                        tempCtx.drawImage(
                            sprite,
                            texX, 0, 1, TILE_SIZE,
                            0, 0, 1, stripHeight
                        );
                        
                        // Apply hit effect tint if needed
                        if (enemy.hitEffect > 0) {
                            tempCtx.fillStyle = 'rgba(255, 0, 0, 0.5)';
                            tempCtx.fillRect(0, 0, 1, stripHeight);
                        }
                        
                        // Draw the strip to main canvas
                        this.ctx.drawImage(tempCanvas, x, spriteTop, stripWidth, stripHeight);
                    }
                }
            }
        }
    }
    
    // Draw minimap in the corner
    drawMinimap(player, enemies) {
        // Minimap settings
        const minimapSize = 150;
        const minimapScale = minimapSize / Math.max(MAP_WIDTH, MAP_HEIGHT);
        const minimapX = 10;
        const minimapY = 10;
        
        // Create a separate canvas for the minimap
        const minimapCanvas = document.createElement('canvas');
        minimapCanvas.width = minimapSize;
        minimapCanvas.height = minimapSize;
        const minimapCtx = minimapCanvas.getContext('2d');
        
        // Fill background with semi-transparent black
        minimapCtx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        minimapCtx.fillRect(0, 0, minimapSize, minimapSize);
        
        // Draw grid lines (optional)
        minimapCtx.strokeStyle = 'rgba(40, 40, 40, 0.4)';
        minimapCtx.lineWidth = 0.5;
        
        for (let x = 0; x <= MAP_WIDTH; x += 4) {
            minimapCtx.beginPath();
            minimapCtx.moveTo(x * minimapScale, 0);
            minimapCtx.lineTo(x * minimapScale, minimapSize);
            minimapCtx.stroke();
        }
        
        for (let y = 0; y <= MAP_HEIGHT; y += 4) {
            minimapCtx.beginPath();
            minimapCtx.moveTo(0, y * minimapScale);
            minimapCtx.lineTo(minimapSize, y * minimapScale);
            minimapCtx.stroke();
        }
        
        // Draw walls
        for (let y = 0; y < MAP_HEIGHT; y++) {
            for (let x = 0; x < MAP_WIDTH; x++) {
                if (MAP[y][x] > 0) {
                    minimapCtx.fillStyle = 'rgb(200, 200, 200)';
                    minimapCtx.fillRect(
                        x * minimapScale,
                        y * minimapScale,
                        minimapScale,
                        minimapScale
                    );
                }
            }
        }
        
        // Draw player
        player.drawOnMinimap(minimapCtx, minimapScale);
        
        // Draw enemies (if EnemyManager is provided)
        if (enemies instanceof EnemyManager) {
            enemies.drawOnMinimap(minimapCtx, minimapScale);
        } else if (Array.isArray(enemies)) {
            for (const enemy of enemies) {
                enemy.drawOnMinimap(minimapCtx, minimapScale);
            }
        }
        
        // Draw minimap title
        minimapCtx.font = '10px Arial';
        minimapCtx.fillStyle = 'rgb(200, 200, 200)';
        minimapCtx.textAlign = 'center';
        minimapCtx.fillText('MINIMAP', minimapSize / 2, 10);
        
        // Draw border
        minimapCtx.strokeStyle = 'rgb(150, 150, 150)';
        minimapCtx.lineWidth = 1;
        minimapCtx.strokeRect(0, 0, minimapSize, minimapSize);
        
        // Draw the minimap on the main canvas
        this.ctx.drawImage(minimapCanvas, minimapX, minimapY);
    }
}