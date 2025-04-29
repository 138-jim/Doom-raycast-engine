// Textures.js - Handles loading and creation of all game textures

class TextureManager {
    constructor() {
        this.wallTextures = [];
        this.enemyTextures = {};
        this.weaponTextures = {};
        this.loaded = false;
    }

    // Preload all textures and return a promise that resolves when loading is complete
    async loadTextures(progressCallback) {
        try {
            // Create wall textures
            this.createWallTextures();
            
            // Create weapon textures
            this.createWeaponTextures();
            
            // Create enemy textures
            this.createEnemyTextures();
            
            // Update progress (50% for texture creation)
            if (progressCallback) progressCallback(0.5);
            
            // Load sound assets (simulate loading time)
            await new Promise(resolve => setTimeout(resolve, 500));
            
            // Mark textures as loaded
            this.loaded = true;
            
            // Update progress (100% for completion)
            if (progressCallback) progressCallback(1.0);
            
            return true;
        } catch (error) {
            console.error("Error loading textures:", error);
            return false;
        }
    }

    // Create procedural wall textures
    createWallTextures() {
        // Brick texture
        const brickCanvas = document.createElement('canvas');
        brickCanvas.width = brickCanvas.height = TILE_SIZE;
        const brickCtx = brickCanvas.getContext('2d');
        
        // Darker, richer red for base
        brickCtx.fillStyle = 'rgb(140, 50, 30)';
        brickCtx.fillRect(0, 0, TILE_SIZE, TILE_SIZE);
        
        // Create more defined brick pattern
        for (let y = 0; y < TILE_SIZE; y += 8) {
            for (let x = 0; x < TILE_SIZE; x += 16) {
                const offset = (y % 16 === 0) ? 8 : 0;
                
                // Make the mortar thinner and more defined
                brickCtx.fillStyle = 'rgb(190, 100, 60)';
                brickCtx.fillRect(x + offset + 1, y + 1, 7, 3);
                
                // Add subtle brick texture/variations (30% of the bricks)
                if (Math.random() > 0.7) {
                    const shade = Math.floor(Math.random() * 40) - 20;
                    const brickColor = `rgb(
                        ${Math.min(255, Math.max(0, 190 + shade))}, 
                        ${Math.min(255, Math.max(0, 100 + Math.floor(shade/2)))}, 
                        ${Math.min(255, Math.max(0, 60 + Math.floor(shade/3)))}
                    )`;
                    brickCtx.fillStyle = brickColor;
                    brickCtx.fillRect(x + offset + 2, y + 2, 5, 1);
                }
            }
        }
        
        // Stone texture
        const stoneCanvas = document.createElement('canvas');
        stoneCanvas.width = stoneCanvas.height = TILE_SIZE;
        const stoneCtx = stoneCanvas.getContext('2d');
        
        // Darker base for contrast
        stoneCtx.fillStyle = 'rgb(70, 70, 70)';
        stoneCtx.fillRect(0, 0, TILE_SIZE, TILE_SIZE);
        
        // Draw stones with better definition and variation
        for (let y = 0; y < TILE_SIZE; y += 8) {
            for (let x = 0; x < TILE_SIZE; x += 8) {
                const shade = Math.floor(Math.random() * 50) + 70;
                
                // Add subtle variation to each stone block
                const stoneColor = `rgb(
                    ${shade}, 
                    ${shade}, 
                    ${shade + Math.floor(Math.random() * 20) - 10}
                )`;
                stoneCtx.fillStyle = stoneColor;
                stoneCtx.fillRect(x, y, 7, 7);
                
                // Add highlights/shadows to create more depth
                const edgeShade = Math.max(30, shade - 40);
                stoneCtx.fillStyle = `rgb(${edgeShade}, ${edgeShade}, ${edgeShade})`;
                
                // Draw bottom and right edge lines
                stoneCtx.fillRect(x, y + 7, 7, 1);
                stoneCtx.fillRect(x + 7, y, 1, 7);
                
                // Add subtle crack or texture detail to some blocks
                if (Math.random() > 0.8) {
                    const detailShade = Math.min(200, shade + 30);
                    stoneCtx.fillStyle = `rgb(${detailShade}, ${detailShade}, ${detailShade})`;
                    stoneCtx.beginPath();
                    stoneCtx.moveTo(x + 1, y + 1);
                    stoneCtx.lineTo(x + 3, y + 3);
                    stoneCtx.stroke();
                }
            }
        }
        
        // Add textures to array
        this.wallTextures.push({
            image: brickCanvas,
            data: brickCtx.getImageData(0, 0, TILE_SIZE, TILE_SIZE).data
        });
        
        this.wallTextures.push({
            image: stoneCanvas,
            data: stoneCtx.getImageData(0, 0, TILE_SIZE, TILE_SIZE).data
        });
    }

    // Create weapon textures
    createWeaponTextures() {
        // Create a gun image
        const gunCanvas = document.createElement('canvas');
        gunCanvas.width = 150;
        gunCanvas.height = 120;
        const gunCtx = gunCanvas.getContext('2d');
        
        // Use clearRect to ensure transparency
        gunCtx.clearRect(0, 0, gunCanvas.width, gunCanvas.height);
        
        // Gun barrel
        gunCtx.fillStyle = 'rgb(50, 50, 50)';
        gunCtx.fillRect(60, 20, 40, 10);
        
        // Gun body
        gunCtx.fillStyle = 'rgb(70, 70, 70)';
        gunCtx.fillRect(40, 30, 70, 40);
        
        gunCtx.fillStyle = 'rgb(60, 60, 60)';
        gunCtx.fillRect(50, 70, 50, 30);
        
        // Gun handle
        gunCtx.fillStyle = 'rgb(80, 50, 30)';
        gunCtx.fillRect(60, 70, 30, 50);
        
        // Gun details
        gunCtx.fillStyle = 'rgb(100, 100, 100)';
        gunCtx.fillRect(45, 35, 60, 10);
        
        gunCtx.fillStyle = 'rgb(30, 30, 30)';
        gunCtx.fillRect(95, 25, 10, 5);
        
        // Create muzzle flash effect
        const flashCanvas = document.createElement('canvas');
        flashCanvas.width = 60;
        flashCanvas.height = 40;
        const flashCtx = flashCanvas.getContext('2d');
        
        // Clear for transparency
        flashCtx.clearRect(0, 0, flashCanvas.width, flashCanvas.height);
        
        // Yellow-orange circular flash with transparency
        const gradient = flashCtx.createRadialGradient(20, 20, 0, 20, 20, 20);
        gradient.addColorStop(0, 'rgba(255, 255, 130, 0.9)');
        gradient.addColorStop(0.5, 'rgba(255, 220, 130, 0.7)');
        gradient.addColorStop(1, 'rgba(255, 220, 130, 0)');
        
        flashCtx.fillStyle = gradient;
        flashCtx.beginPath();
        flashCtx.arc(20, 20, 20, 0, Math.PI * 2);
        flashCtx.fill();
        
        // Inner glow
        const innerGradient = flashCtx.createRadialGradient(30, 20, 0, 30, 20, 15);
        innerGradient.addColorStop(0, 'rgba(255, 255, 255, 0.9)');
        innerGradient.addColorStop(0.7, 'rgba(255, 160, 50, 0.7)');
        innerGradient.addColorStop(1, 'rgba(255, 160, 50, 0)');
        
        flashCtx.fillStyle = innerGradient;
        flashCtx.beginPath();
        flashCtx.arc(30, 20, 15, 0, Math.PI * 2);
        flashCtx.fill();
        
        // Random spark lines
        flashCtx.strokeStyle = 'rgba(255, 255, 200, 0.8)';
        flashCtx.lineWidth = 2;
        
        for (let i = 0; i < 5; i++) {
            const startX = 30;
            const startY = 20;
            const endX = startX + Math.floor(Math.random() * 20) + 10;
            const endY = startY + Math.floor(Math.random() * 30) - 15;
            
            flashCtx.beginPath();
            flashCtx.moveTo(startX, startY);
            flashCtx.lineTo(endX, endY);
            flashCtx.stroke();
        }
        
        // Store weapon textures
        this.weaponTextures = {
            gun: gunCanvas,
            muzzleFlash: flashCanvas
        };
    }

    // Create enemy textures (front, side, back views)
    createEnemyTextures() {
        const spriteSize = TILE_SIZE;
        const enemyViews = ['front', 'side', 'back'];
        this.enemyTextures = {};
        
        // Create canvases for each view
        enemyViews.forEach(view => {
            const canvas = document.createElement('canvas');
            canvas.width = canvas.height = spriteSize;
            const ctx = canvas.getContext('2d');
            
            // Clear for transparency
            ctx.clearRect(0, 0, spriteSize, spriteSize);
            
            // Common properties
            const bodyColor = 'rgb(150, 30, 30)';
            const headColor = view === 'back' ? 'rgb(90, 20, 20)' : 'rgb(180, 40, 40)';
            const headSize = spriteSize / 4;
            
            if (view === 'front') {
                // Front-facing sprite
                
                // Body
                ctx.fillStyle = bodyColor;
                ctx.fillRect(spriteSize/4, spriteSize/3, spriteSize/2, spriteSize/2);
                
                // Head
                ctx.fillStyle = headColor;
                ctx.beginPath();
                ctx.arc(spriteSize/2, spriteSize/4, headSize, 0, Math.PI * 2);
                ctx.fill();
                
                // Arms
                ctx.fillStyle = bodyColor;
                ctx.fillRect(spriteSize/8, spriteSize/3, spriteSize/6, spriteSize/3);
                ctx.fillRect(spriteSize*5/8, spriteSize/3, spriteSize/6, spriteSize/3);
                
                // Legs
                ctx.fillRect(spriteSize/3, spriteSize*5/6, spriteSize/6, spriteSize/6);
                ctx.fillRect(spriteSize/2, spriteSize*5/6, spriteSize/6, spriteSize/6);
                
                // Eyes
                const eyeOffset = spriteSize/16;
                const eyeSize = spriteSize/12;
                
                ctx.fillStyle = 'white';
                ctx.beginPath();
                ctx.arc(spriteSize/2 - eyeOffset, spriteSize/4, eyeSize, 0, Math.PI * 2);
                ctx.arc(spriteSize/2 + eyeOffset, spriteSize/4, eyeSize, 0, Math.PI * 2);
                ctx.fill();
                
                // Pupils
                const pupilSize = eyeSize/2;
                ctx.fillStyle = 'black';
                ctx.beginPath();
                ctx.arc(spriteSize/2 - eyeOffset, spriteSize/4, pupilSize, 0, Math.PI * 2);
                ctx.arc(spriteSize/2 + eyeOffset, spriteSize/4, pupilSize, 0, Math.PI * 2);
                ctx.fill();
                
            } else if (view === 'side') {
                // Side-facing sprite (looks thinner when viewed from side)
                
                // Body (narrower)
                ctx.fillStyle = bodyColor;
                ctx.fillRect(spriteSize*3/8, spriteSize/3, spriteSize/4, spriteSize/2);
                
                // Head
                ctx.fillStyle = headColor;
                ctx.beginPath();
                ctx.arc(spriteSize/2, spriteSize/4, headSize, 0, Math.PI * 2);
                ctx.fill();
                
                // Arm (one visible from side)
                ctx.fillStyle = bodyColor;
                ctx.fillRect(spriteSize*3/8, spriteSize/3, spriteSize/4, spriteSize/3);
                
                // Legs (one slightly in front of the other)
                ctx.fillRect(spriteSize*3/8, spriteSize*5/6, spriteSize/6, spriteSize/6);
                ctx.fillRect(spriteSize/2, spriteSize*5/6, spriteSize/6, spriteSize/6);
                
                // Eye (only one visible from side)
                ctx.fillStyle = 'white';
                ctx.beginPath();
                ctx.arc(spriteSize*5/8, spriteSize/4, spriteSize/12, 0, Math.PI * 2);
                ctx.fill();
                
                ctx.fillStyle = 'black';
                ctx.beginPath();
                ctx.arc(spriteSize*5/8, spriteSize/4, spriteSize/24, 0, Math.PI * 2);
                ctx.fill();
                
            } else if (view === 'back') {
                // Back-facing sprite
                
                // Body (same as front)
                ctx.fillStyle = bodyColor;
                ctx.fillRect(spriteSize/4, spriteSize/3, spriteSize/2, spriteSize/2);
                
                // Head (darker to indicate back of head)
                ctx.fillStyle = headColor;
                ctx.beginPath();
                ctx.arc(spriteSize/2, spriteSize/4, headSize, 0, Math.PI * 2);
                ctx.fill();
                
                // Arms
                ctx.fillStyle = bodyColor;
                ctx.fillRect(spriteSize/8, spriteSize/3, spriteSize/6, spriteSize/3);
                ctx.fillRect(spriteSize*5/8, spriteSize/3, spriteSize/6, spriteSize/3);
                
                // Legs
                ctx.fillRect(spriteSize/3, spriteSize*5/6, spriteSize/6, spriteSize/6);
                ctx.fillRect(spriteSize/2, spriteSize*5/6, spriteSize/6, spriteSize/6);
                
                // No eyes visible from back
            }
            
            // Store in textures object
            this.enemyTextures[view] = canvas;
        });
    }

    // Get color from texture at specific position
    getTexturePixel(textureType, textureId, x, y) {
        if (textureType === 'wall') {
            const texture = this.wallTextures[textureId];
            if (!texture) return [0, 0, 0];
            
            // Ensure x and y are within texture bounds
            x = Math.floor(x) % TILE_SIZE;
            y = Math.floor(y) % TILE_SIZE;
            
            // Calculate index in the data array (4 bytes per pixel: R,G,B,A)
            const index = (y * TILE_SIZE + x) * 4;
            
            return [
                texture.data[index],     // R
                texture.data[index + 1], // G
                texture.data[index + 2]  // B
            ];
        }
        
        return [255, 255, 255]; // Default white if texture not found
    }
}

// Create a singleton instance
const textureManager = new TextureManager();