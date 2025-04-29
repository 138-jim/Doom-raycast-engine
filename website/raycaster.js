// Raycaster.js - Core raycasting engine for rendering the 3D view

class Raycaster {
    constructor(canvas) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // Resize canvas to match screen dimensions
        this.resize();
        
        // Performance settings
        this.skipRays = 1; // Render every nth ray
        this.quality = 1; // Rendering quality multiplier (lower for better performance)
        this.adaptiveResolution = true; // Enable adaptive resolution based on FPS
        this.targetFPS = 60; // Target FPS for adaptive resolution
        this.currentFPS = 60; // Current FPS
        
        // Pre-allocate buffers for better performance
        this.wallImageData = this.ctx.createImageData(1, this.canvas.height);
        this.wallBuffer = new Uint8ClampedArray(this.wallImageData.data.buffer);
        
        // Pre-calculate sin/cos tables for performance
        this.initTrigTables();
        
        // Create sky and floor colors
        this.createSkyGradient();
        this.createFloorGradient();
        
        // Create offscreen canvas for minimap to avoid recreating it every frame
        this.minimapCanvas = document.createElement('canvas');
        this.minimapCtx = this.minimapCanvas.getContext('2d');
        this.minimapSize = 150;
        this.minimapCanvas.width = this.minimapSize;
        this.minimapCanvas.height = this.minimapSize;
        
        // Cache for temporary canvases (sprite rendering)
        this.spriteCanvasCache = [];
        for (let i = 0; i < 10; i++) { // Pre-allocate 10 canvases
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            this.spriteCanvasCache.push({ canvas, ctx, inUse: false });
        }
    }
    
    // Pre-calculate sin and cos values for performance
    initTrigTables() {
        const angles = 360; // Number of angles to pre-calculate
        this.sinTable = new Float32Array(angles);
        this.cosTable = new Float32Array(angles);
        
        for (let i = 0; i < angles; i++) {
            const angle = (i * Math.PI) / 180;
            this.sinTable[i] = Math.sin(angle);
            this.cosTable[i] = Math.cos(angle);
        }
    }
    
    // Get sin value from pre-calculated table
    sin(angle) {
        // Normalize angle to 0-359
        const index = Math.floor(((angle % 360) + 360) % 360);
        return this.sinTable[index];
    }
    
    // Get cos value from pre-calculated table
    cos(angle) {
        // Normalize angle to 0-359
        const index = Math.floor(((angle % 360) + 360) % 360);
        return this.cosTable[index];
    }
    
    // Update canvas size to match container
    resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        
        // Re-create image data buffer for the new size
        this.wallImageData = this.ctx.createImageData(1, this.canvas.height);
        this.wallBuffer = new Uint8ClampedArray(this.wallImageData.data.buffer);
        
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
    
    // Update render quality based on current FPS
    updateAdaptiveResolution(currentFPS) {
        if (!this.adaptiveResolution) return;
        
        this.currentFPS = currentFPS;
        
        // Adjust skip rays based on FPS
        if (currentFPS < this.targetFPS * 0.7) {
            // FPS is too low, increase skipRays (lower resolution)
            this.skipRays = Math.min(4, this.skipRays + 1);
        } else if (currentFPS > this.targetFPS * 1.2 && this.skipRays > 1) {
            // FPS is good, decrease skipRays (higher resolution)
            this.skipRays = Math.max(1, this.skipRays - 1);
        }
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
        const zBuffer = new Float32Array(RAY_COUNT);
        zBuffer.fill(MAX_DEPTH);
        
        // Pre-compute player position for DDA
        const playerMapX = player.x / TILE_SIZE;
        const playerMapY = player.y / TILE_SIZE;
        
        // Cast rays with adaptive resolution
        const rayStep = this.skipRays;
        for (let ray = 0; ray < RAY_COUNT; ray += rayStep) {
            // Calculate ray angle
            const rayAngle = (startAngle + (ray / RAY_COUNT) * FOV);
            
            // Use pre-calculated sin/cos tables for better performance
            const rayDirX = this.cos(rayAngle);
            const rayDirY = this.sin(rayAngle);
            
            // DDA Algorithm 
            let mapX = Math.floor(playerMapX);
            let mapY = Math.floor(playerMapY);
            
            // Calculate delta distance
            const deltaDistX = Math.abs(1 / rayDirX) || Number.MAX_VALUE;
            const deltaDistY = Math.abs(1 / rayDirY) || Number.MAX_VALUE;
            
            // Initial step direction
            const stepX = rayDirX >= 0 ? 1 : -1;
            const stepY = rayDirY >= 0 ? 1 : -1;
            
            // Calculate initial side distance
            let sideDistX = rayDirX < 0 
                ? (playerMapX - mapX) * deltaDistX 
                : (mapX + 1.0 - playerMapX) * deltaDistX;
            
            let sideDistY = rayDirY < 0 
                ? (playerMapY - mapY) * deltaDistY 
                : (mapY + 1.0 - playerMapY) * deltaDistY;
            
            // Perform DDA
            let hit = false;
            let side = 0; // 0 for x-side, 1 for y-side
            
            // Limit number of iterations for performance
            const MAX_DDA_STEPS = MAX_DEPTH * 2;
            let ddaSteps = 0;
            
            while (!hit && ddaSteps < MAX_DDA_STEPS) {
                ddaSteps++;
                
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
                
                // Check if ray is out of bounds (bounds check optimization)
                if ((mapX & ~(MAP_WIDTH - 1)) || (mapY & ~(MAP_HEIGHT - 1))) {
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
                const perpWallDist = side === 0 
                    ? (mapX - playerMapX + (1 - stepX) / 2) / rayDirX 
                    : (mapY - playerMapY + (1 - stepY) / 2) / rayDirY;
                
                // Store distance in z-buffer for sprite rendering
                for (let i = 0; i < rayStep; i++) {
                    if (ray + i < zBuffer.length) {
                        zBuffer[ray + i] = perpWallDist;
                    }
                }
                
                // Calculate wall height (limited for performance)
                const lineHeight = Math.min(
                    WALL_HEIGHT_LIMIT, 
                    Math.floor(screenHeight / (perpWallDist || MINIMUM_WALL_DISTANCE))
                );
                
                // Calculate drawing boundaries
                const drawStart = Math.max(0, Math.floor(halfHeight - lineHeight / 2));
                const drawEnd = Math.min(screenHeight - 1, Math.floor(halfHeight + lineHeight / 2));
                
                // Get wall texture
                const wallTexture = MAP[mapY][mapX] - 1; // Convert to 0-based index
                
                // Calculate where exactly the wall was hit (wall X coordinate)
                const wallX = side === 0 
                    ? playerMapY + perpWallDist * rayDirY
                    : playerMapX + perpWallDist * rayDirX;
                
                // Get fractional part of wallX
                const wallXFrac = wallX - Math.floor(wallX);
                
                // X coordinate on the texture
                let texX = Math.floor(wallXFrac * TILE_SIZE);
                if ((side === 0 && rayDirX > 0) || (side === 1 && rayDirY < 0)) {
                    texX = TILE_SIZE - texX - 1;
                }
                
                // Calculate shade based on distance and side
                const baseShadeFactor = side === 1 ? 0.8 : 1.0;
                
                // Distance fog effect (use less intensive calculation)
                const distanceFactor = perpWallDist / MAX_DEPTH;
                const shadeFactor = baseShadeFactor * (1.0 - distanceFactor * 0.6);
                
                // Draw vertical wall strip more efficiently using pre-allocated image data
                const stripHeight = drawEnd - drawStart;
                if (stripHeight > 0) {
                    // Calculate texture step for proper scaling
                    const step = TILE_SIZE / lineHeight;
                    
                    // Starting texture position based on where drawing begins
                    let texPos = (drawStart - halfHeight + lineHeight / 2) * step;
                    
                    // Pre-clear the image data
                    this.wallBuffer.fill(0);
                    
                    // Performance: Only process visible part of the wall
                    const textureMask = TILE_SIZE - 1; // For power-of-2 size textures
                    
                    // Fill the vertical strip buffer
                    for (let y = 0; y < stripHeight; y++) {
                        // Get the y-coordinate on the texture (bit masking for performance)
                        const texY = Math.floor(texPos) & textureMask;
                        texPos += step;
                        
                        // Get the pixel color from the texture
                        const [r, g, b] = textureManager.getTexturePixel('wall', wallTexture, texX, texY);
                        
                        // Apply shading
                        const pixelIndex = y * 4;
                        this.wallBuffer[pixelIndex] = r * shadeFactor;     // R
                        this.wallBuffer[pixelIndex + 1] = g * shadeFactor; // G
                        this.wallBuffer[pixelIndex + 2] = b * shadeFactor; // B
                        this.wallBuffer[pixelIndex + 3] = 255;             // A
                    }
                    
                    // Get image data for the vertical strip
                    this.wallImageData.data.set(this.wallBuffer.subarray(0, stripHeight * 4));
                    
                    // Batch render strips for the same ray step (fill in gaps)
                    for (let i = 0; i < rayStep; i++) {
                        if (ray + i < RAY_COUNT) {
                            const x = (ray + i) * stripWidth;
                            this.ctx.putImageData(
                                this.wallImageData, 
                                x, drawStart, 
                                0, 0, 
                                stripWidth, stripHeight
                            );
                        }
                    }
                }
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
    
    // Get an available sprite canvas from the cache
    getTemporaryCanvas(width, height) {
        // Find an unused canvas
        for (const item of this.spriteCanvasCache) {
            if (!item.inUse) {
                item.inUse = true;
                item.canvas.width = width;
                item.canvas.height = height;
                // Clear canvas
                item.ctx.clearRect(0, 0, width, height);
                return item;
            }
        }
        
        // If no available canvas, create a new one
        const canvas = document.createElement('canvas');
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        const newItem = { canvas, ctx, inUse: true };
        this.spriteCanvasCache.push(newItem);
        return newItem;
    }
    
    // Return a canvas to the cache
    releaseTemporaryCanvas(canvasItem) {
        canvasItem.inUse = false;
    }
    
    // Render enemies using sprite casting technique with optimizations
    renderEnemies(player, enemies, zBuffer) {
        // Convert player's angle to radians
        const playerAngleRad = player.angle * Math.PI / 180;
        
        let enemiesWithDist = [];
        
        // Check if enemies is an EnemyManager or an array
        if (enemies && enemies.enemies && Array.isArray(enemies.enemies)) {
            // It's an EnemyManager with an enemies array
            if (enemies.enemies.length === 0) return; // Early exit if no enemies
            
            // Use typed arrays for better performance
            const counts = enemies.enemies.length;
            const distances = new Float32Array(counts);
            const indices = new Int32Array(counts);
            
            // Calculate distances in bulk
            for (let i = 0; i < counts; i++) {
                const enemy = enemies.enemies[i];
                const dx = enemy.x - player.x;
                const dy = enemy.y - player.y;
                // Use squared distance for sorting (avoid square root)
                distances[i] = dx * dx + dy * dy;
                indices[i] = i;
            }
            
            // Sort indices by distance (furthest first - painters algorithm)
            indices.sort((a, b) => distances[b] - distances[a]);
            
            // Create sorted array of enemies with actual distances
            for (let i = 0; i < counts; i++) {
                const idx = indices[i];
                const enemy = enemies.enemies[idx];
                const dist = Math.sqrt(distances[idx]); // Only calculate sqrt here
                enemiesWithDist.push({ enemy, dist });
            }
        } else if (Array.isArray(enemies)) {
            // It's already an array of enemies - similar optimized logic
            if (enemies.length === 0) return; // Early exit if no enemies
            
            const counts = enemies.length;
            const distances = new Float32Array(counts);
            const indices = new Int32Array(counts);
            
            for (let i = 0; i < counts; i++) {
                const dx = enemies[i].x - player.x;
                const dy = enemies[i].y - player.y;
                distances[i] = dx * dx + dy * dy;
                indices[i] = i;
            }
            
            indices.sort((a, b) => distances[b] - distances[a]);
            
            for (let i = 0; i < counts; i++) {
                const idx = indices[i];
                enemiesWithDist.push({ 
                    enemy: enemies[idx], 
                    dist: Math.sqrt(distances[idx])
                });
            }
        } else {
            // No valid enemies to render
            return;
        }
        
        // Render each enemy efficiently
        for (const { enemy, dist } of enemiesWithDist) {
            // Skip if the sprite is too far
            if (dist > MAX_DEPTH * TILE_SIZE) continue;
            
            // Calculate sprite angle relative to player's view
            const dx = enemy.x - player.x;
            const dy = enemy.y - player.y;
            const spriteAngle = Math.atan2(dy, dx) - playerAngleRad;
            
            // Normalize angle to -π to π more efficiently
            let normalizedAngle = spriteAngle;
            while (normalizedAngle > Math.PI) normalizedAngle -= 2 * Math.PI;
            while (normalizedAngle < -Math.PI) normalizedAngle += 2 * Math.PI;
            
            // Check if sprite is in field of view (with some margin)
            if (Math.abs(normalizedAngle) > HALF_FOV_RAD * 1.5) continue;
            
            // Calculate sprite screen position
            const spriteScreenX = Math.floor((0.5 + normalizedAngle / FOV_RAD) * this.canvas.width);
            
            // Calculate sprite size based on distance (with limit for performance)
            const spriteSize = Math.min(
                MAX_SPRITE_SIZE, 
                Math.floor(this.canvas.height / (dist / TILE_SIZE))
            );
            
            // Early skip if sprite would be too small to see
            if (spriteSize < 4) continue;
            
            // Calculate sprite drawing boundaries
            const spriteTop = Math.max(0, Math.floor(this.canvas.height / 2 - spriteSize / 2));
            const spriteBottom = Math.min(this.canvas.height, Math.floor(this.canvas.height / 2 + spriteSize / 2));
            
            // Calculate horizontal span of the sprite
            const spriteWidth = spriteSize;
            const spriteLeft = Math.floor(spriteScreenX - spriteWidth / 2);
            const spriteRight = spriteLeft + spriteWidth;
            
            // Skip if completely off screen
            if (spriteRight < 0 || spriteLeft >= this.canvas.width) continue;
            
            // Get the appropriate sprite based on view angle
            const sprite = enemy.getCurrentSprite(player.angle);
            const shouldFlip = enemy.shouldFlipSprite(player.angle);
            
            // Use different rendering strategies based on distance for performance
            const stripHeight = spriteBottom - spriteTop;
            const stripWidth = WALL_STRIP_WIDTH * this.quality;
            
            // For distant sprites, render more efficiently with fewer strips
            const distanceFactor = dist / (MAX_DEPTH * TILE_SIZE);
            const stripSkip = distanceFactor > 0.7 ? 3 : (distanceFactor > 0.5 ? 2 : 1);
            
            // Use cached canvas for better performance
            const tempCanvasItem = this.getTemporaryCanvas(spriteRight - spriteLeft, stripHeight);
            const { canvas: tempCanvas, ctx: tempCtx } = tempCanvasItem;
            
            // Render the entire sprite image to the temporary canvas
            tempCtx.drawImage(
                sprite,
                0, 0, TILE_SIZE, TILE_SIZE,
                0, 0, spriteRight - spriteLeft, stripHeight
            );
            
            // Apply hit effect tint if needed
            if (enemy.hitEffect > 0) {
                tempCtx.fillStyle = 'rgba(255, 0, 0, 0.5)';
                tempCtx.fillRect(0, 0, spriteRight - spriteLeft, stripHeight);
            }
            
            // Draw sprite with z-buffer check for occlusion
            for (let x = Math.max(0, spriteLeft); x < Math.min(this.canvas.width, spriteRight); x += stripSkip) {
                // Find the ray that corresponds to this x position
                const rayIdx = Math.floor(x / WALL_STRIP_WIDTH / this.quality) * this.skipRays;
                
                // Ensure ray index is within bounds
                if (rayIdx >= 0 && rayIdx < zBuffer.length) {
                    // Only draw if sprite is closer than the wall at this ray
                    if (dist / TILE_SIZE < zBuffer[rayIdx]) {
                        // Draw vertical strip from pre-rendered sprite
                        this.ctx.drawImage(
                            tempCanvas,
                            x - spriteLeft, 0, stripSkip, stripHeight,
                            x, spriteTop, stripSkip, stripHeight
                        );
                    }
                }
            }
            
            // Release the temporary canvas back to the cache
            this.releaseTemporaryCanvas(tempCanvasItem);
        }
    }
    
    // Draw minimap in the corner with optimizations
    drawMinimap(player, enemies) {
        // Recalculate minimap on size change
        const minimapScale = this.minimapSize / Math.max(MAP_WIDTH, MAP_HEIGHT);
        
        // Clear the minimap canvas
        this.minimapCtx.clearRect(0, 0, this.minimapSize, this.minimapSize);
        
        // Fill background with semi-transparent black
        this.minimapCtx.fillStyle = 'rgba(0, 0, 0, 0.7)';
        this.minimapCtx.fillRect(0, 0, this.minimapSize, this.minimapSize);
        
        // Only draw grid lines in debug mode (they're expensive)
        if (false) { // Set to true to enable grid lines
            this.minimapCtx.strokeStyle = 'rgba(40, 40, 40, 0.4)';
            this.minimapCtx.lineWidth = 0.5;
            
            for (let x = 0; x <= MAP_WIDTH; x += 4) {
                this.minimapCtx.beginPath();
                this.minimapCtx.moveTo(x * minimapScale, 0);
                this.minimapCtx.lineTo(x * minimapScale, this.minimapSize);
                this.minimapCtx.stroke();
            }
            
            for (let y = 0; y <= MAP_HEIGHT; y += 4) {
                this.minimapCtx.beginPath();
                this.minimapCtx.moveTo(0, y * minimapScale);
                this.minimapCtx.lineTo(this.minimapSize, y * minimapScale);
                this.minimapCtx.stroke();
            }
        }
        
        // Draw walls more efficiently
        this.minimapCtx.fillStyle = 'rgb(200, 200, 200)';
        for (let y = 0; y < MAP_HEIGHT; y++) {
            for (let x = 0; x < MAP_WIDTH; x++) {
                if (MAP[y][x] > 0) {
                    this.minimapCtx.fillRect(
                        x * minimapScale,
                        y * minimapScale,
                        minimapScale,
                        minimapScale
                    );
                }
            }
        }
        
        // Draw player
        player.drawOnMinimap(this.minimapCtx, minimapScale);
        
        // Draw enemies (if EnemyManager is provided)
        if (enemies instanceof EnemyManager) {
            enemies.drawOnMinimap(this.minimapCtx, minimapScale);
        } else if (Array.isArray(enemies)) {
            for (const enemy of enemies) {
                enemy.drawOnMinimap(this.minimapCtx, minimapScale);
            }
        }
        
        // Draw minimap title
        this.minimapCtx.font = '10px Arial';
        this.minimapCtx.fillStyle = 'rgb(200, 200, 200)';
        this.minimapCtx.textAlign = 'center';
        this.minimapCtx.fillText('MINIMAP', this.minimapSize / 2, 10);
        
        // Draw border
        this.minimapCtx.strokeStyle = 'rgb(150, 150, 150)';
        this.minimapCtx.lineWidth = 1;
        this.minimapCtx.strokeRect(0, 0, this.minimapSize, this.minimapSize);
        
        // Draw the minimap on the main canvas (cached version)
        this.ctx.drawImage(this.minimapCanvas, 10, 10);
    }
}