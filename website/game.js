// Game.js - Main game loop and state management

// Main Game class
class Game {
    constructor() {
        // Get canvas and create raycaster
        this.canvas = document.getElementById('gameCanvas');
        this.raycaster = new Raycaster(this.canvas);
        
        // Create audio manager
        this.audioManager = new AudioManager();
        
        // Create pathfinding system
        this.pathfinding = new Pathfinding();
        
        // Game objects (initialized when game starts)
        this.player = null;
        this.weapon = null;
        this.enemyManager = null;
        
        // Game state
        this.state = GameState.LOADING;
        this.prevState = null;
        this.isMouseLocked = false;
        
        // Performance tracking
        this.lastTime = 0;
        this.deltaTime = 0;
        this.fps = 0;
        this.frameCount = 0;
        this.fpsUpdateTime = 0;
        
        // Game loop optimization variables
        this.accumulatedTime = 0;
        this.unfocusedTime = 0;
        this.lastFocused = true;
        
        // Mouse movement
        this.mouseDx = 0;
        
        // Initialize screens
        this.screens = {
            menu: document.getElementById('menu-screen'),
            options: document.getElementById('options-screen'),
            gameOver: document.getElementById('game-over-screen'),
            loading: document.getElementById('loading-screen')
        };
        
        // UI elements
        this.uiOverlay = document.getElementById('ui-overlay');
        this.healthBar = document.getElementById('health-bar');
        this.healthText = document.getElementById('health-text');
        this.scoreText = document.getElementById('score-text');
        this.fpsCounter = document.getElementById('fps-counter');
        this.finalScore = document.getElementById('final-score');
        this.controlsText = document.getElementById('controls-text');
        this.progressBar = document.getElementById('progress');
        
        // Buttons
        this.buttons = {
            start: document.getElementById('start-button'),
            options: document.getElementById('options-button'),
            quit: document.getElementById('quit-button'),
            back: document.getElementById('back-button'),
            restart: document.getElementById('restart-button'),
            menu: document.getElementById('menu-button')
        };
        
        // Volume sliders
        this.sliders = {
            master: document.getElementById('master-volume'),
            sfx: document.getElementById('sfx-volume'),
            music: document.getElementById('music-volume')
        };
        
        this.sliderValues = {
            master: document.getElementById('master-volume-value'),
            sfx: document.getElementById('sfx-volume-value'),
            music: document.getElementById('music-volume-value')
        };
        
        // Initialize event listeners
        this.initEvents();
        
        // Start loading resources
        this.loadResources();
    }
    
    // Initialize all event listeners
    initEvents() {
        // Window resize
        window.addEventListener('resize', () => {
            this.raycaster.resize();
        });
        
        // Keyboard events
        window.addEventListener('keydown', (e) => this.handleKeyDown(e));
        window.addEventListener('keyup', (e) => this.handleKeyUp(e));
        
        // Mouse events
        this.canvas.addEventListener('click', () => this.lockMouse());
        document.addEventListener('pointerlockchange', () => this.handlePointerLockChange());
        document.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        
        // Button events
        this.buttons.start.addEventListener('click', () => {
            this.startGame();
            this.audioManager.activateAudio(); // Ensure audio works after user interaction
        });
        this.buttons.options.addEventListener('click', () => {
            this.setState(GameState.OPTIONS);
            this.audioManager.activateAudio(); // Ensure audio works after user interaction
        });
        this.buttons.quit.addEventListener('click', () => this.quit());
        this.buttons.back.addEventListener('click', () => this.setState(GameState.MAIN_MENU));
        this.buttons.restart.addEventListener('click', () => this.startGame());
        this.buttons.menu.addEventListener('click', () => this.setState(GameState.MAIN_MENU));
        
        // Add a global click/keydown handler to enable audio
        const enableAudio = () => {
            if (this.audioManager) {
                this.audioManager.activateAudio();
                // If music should be playing but isn't, start it now
                if (this.audioManager.musicShouldPlay && this.state === GameState.MAIN_MENU) {
                    this.audioManager.playMusic();
                }
            }
            // Remove the event listeners once audio is activated
            document.removeEventListener('click', enableAudio);
            document.removeEventListener('keydown', enableAudio);
        };
        
        document.addEventListener('click', enableAudio);
        document.addEventListener('keydown', enableAudio);
        
        // Volume sliders
        for (const [type, slider] of Object.entries(this.sliders)) {
            slider.addEventListener('input', () => {
                const value = slider.value / 100;
                this.sliderValues[type].textContent = `${slider.value}%`;
                this.audioManager.setVolume(type, value);
            });
        }
        
        // Shoot with mouse
        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 0 && this.state === GameState.PLAYING && this.weapon) {
                this.weapon.fire();
            }
        });
    }
    
    // Handle keyboard input
    handleKeyDown(e) {
        // Skip if in text input
        if (e.target.tagName === 'INPUT') return;
        
        if (this.state === GameState.PLAYING) {
            // Movement keys
            if (['w', 'a', 's', 'd', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
                this.player.setKey(e.key, true);
            }
            
            // Special keys
            switch (e.key) {
                case 'Escape':
                    this.unlockMouse();
                    this.setState(GameState.MAIN_MENU);
                    break;
                case 'r':
                    if (this.weapon) this.weapon.reload();
                    break;
                case 'p': // Toggle showing enemy paths
                    if (this.enemyManager) this.enemyManager.togglePaths();
                    break;
            }
        } else if (this.state === GameState.GAME_OVER && e.key === 'Enter') {
            this.startGame();
        }
    }
    
    handleKeyUp(e) {
        // Movement keys
        if (['w', 'a', 's', 'd', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
            e.preventDefault();
            if (this.player) this.player.setKey(e.key, false);
        }
    }
    
    // Handle mouse pointer lock for FPS controls
    lockMouse() {
        if (this.state === GameState.PLAYING && !this.isMouseLocked) {
            this.canvas.requestPointerLock();
        }
    }
    
    unlockMouse() {
        if (this.isMouseLocked) {
            document.exitPointerLock();
        }
    }
    
    handlePointerLockChange() {
        this.isMouseLocked = document.pointerLockElement === this.canvas;
    }
    
    handleMouseMove(e) {
        if (this.isMouseLocked && this.state === GameState.PLAYING) {
            // Store mouse movement for the next frame
            this.mouseDx = e.movementX;
        }
    }
    
    // Load all game resources
    async loadResources() {
        this.setState(GameState.LOADING);
        
        // Update progress as textures load
        await textureManager.loadTextures(progress => {
            this.progressBar.style.width = `${progress * 100}%`;
        });
        
        // Load audio
        await this.audioManager.loadSounds();
        
        // Transition to menu after loading
        setTimeout(() => {
            this.setState(GameState.MAIN_MENU);
            // Mark music as ready to play, but actual playback will happen after user interaction
            this.audioManager.musicShouldPlay = true;
        }, 500);
    }
    
    // Change game state and update UI
    setState(newState) {
        this.prevState = this.state;
        this.state = newState;
        
        // Hide all screens
        for (const screen of Object.values(this.screens)) {
            screen.classList.add('hidden');
        }
        
        // Hide UI overlay when not playing
        this.uiOverlay.style.display = newState === GameState.PLAYING ? 'block' : 'none';
        this.controlsText.style.display = newState === GameState.PLAYING ? 'block' : 'none';
        
        // Show appropriate screen
        switch (newState) {
            case GameState.MAIN_MENU:
                this.screens.menu.classList.remove('hidden');
                this.unlockMouse();
                this.audioManager.playMusic();
                break;
                
            case GameState.OPTIONS:
                this.screens.options.classList.remove('hidden');
                break;
                
            case GameState.GAME_OVER:
                this.finalScore.textContent = `Final Score: ${this.player.score}`;
                this.screens.gameOver.classList.remove('hidden');
                this.unlockMouse();
                break;
                
            case GameState.LOADING:
                this.screens.loading.classList.remove('hidden');
                break;
        }
    }
    
    // Start or restart the game
    startGame() {
        // Create game objects
        this.player = new Player(1.5, 1.5, 0);
        this.weapon = new Weapon(this.audioManager);
        this.enemyManager = new EnemyManager(this.pathfinding, this.audioManager);
        
        // Reset performance counters
        this.lastTime = performance.now();
        this.fpsUpdateTime = this.lastTime;
        this.frameCount = 0;
        
        // Change state and lock mouse
        this.setState(GameState.PLAYING);
        this.lockMouse();
        
        // Stop menu music
        this.audioManager.stopMusic();
        
        // Start game loop if not already running
        if (!this.animationId) {
            this.animationId = requestAnimationFrame(timestamp => this.gameLoop(timestamp));
        }
    }
    
    // Handle quitting the game
    quit() {
        alert('To quit, simply close this browser tab.');
    }
    
    // Update game state
    update() {
        if (this.state === GameState.PLAYING) {
            // Update player with mouse input
            this.player.update(this.deltaTime, this.mouseDx);
            this.mouseDx = 0; // Reset after use
            
            // Update weapon
            this.weapon.update();
            
            // Update enemies and check for player death
            const playerDied = this.enemyManager.update(this.player, this.weapon, this.deltaTime);
            
            if (playerDied) {
                this.setState(GameState.GAME_OVER);
            }
            
            // Update health bar
            const healthPercent = (this.player.health / PLAYER_MAX_HEALTH) * 100;
            this.healthBar.style.width = `${healthPercent}%`;
            
            // Update health color based on amount
            if (healthPercent > 50) {
                this.healthBar.style.backgroundColor = '#0f0'; // Green
            } else if (healthPercent > 25) {
                this.healthBar.style.backgroundColor = '#ff8c00'; // Orange
            } else {
                this.healthBar.style.backgroundColor = '#f00'; // Red
            }
            
            // Update UI text
            this.healthText.textContent = `HEALTH: ${this.player.health}`;
            this.scoreText.textContent = `SCORE: ${this.player.score}`;
        }
        
        // Update FPS counter
        this.frameCount++;
        const elapsed = performance.now() - this.fpsUpdateTime;
        
        if (elapsed >= 1000) { // Update every second
            this.fps = Math.round(this.frameCount * 1000 / elapsed);
            this.fpsCounter.textContent = `FPS: ${this.fps}`;
            
            // Update raycaster's adaptive resolution based on current FPS
            if (this.raycaster && typeof this.raycaster.updateAdaptiveResolution === 'function') {
                this.raycaster.updateAdaptiveResolution(this.fps);
            }
            
            this.frameCount = 0;
            this.fpsUpdateTime = performance.now();
        }
    }
    
    // Render the game
    render() {
        // Render the 3D scene
        if (this.state === GameState.PLAYING) {
            this.raycaster.render(this.player, this.enemyManager);
            
            // Draw weapon on top of the scene
            this.weapon.draw(this.raycaster.ctx, this.canvas.width, this.canvas.height);
        }
    }
    
    // Main game loop with optimizations
    gameLoop(timestamp) {
        // Calculate delta time
        this.deltaTime = (timestamp - this.lastTime) / 1000; // In seconds
        this.lastTime = timestamp;
        
        // Prevent extreme delta times (e.g. after tab switch)
        if (this.deltaTime > 0.1) this.deltaTime = 0.016; // Cap at ~60fps
        
        // Skip updating the game if the tab is not focused - power saving
        if (document.hasFocus() || !this.lastFocused) {
            // Track when we last processed a frame with focus
            this.lastFocused = true;
            
            // Optimize for 60fps - only update game logic at ~60fps
            // but allow rendering at higher rates for smoother visuals
            this.accumulatedTime += this.deltaTime;
            const tickRate = 1/60; // Fixed time step (60 fps)
            
            // Process all accumulated time in fixed steps
            while (this.accumulatedTime >= tickRate) {
                // Update game state at a fixed rate
                this.update();
                this.accumulatedTime -= tickRate;
                
                // Avoid spiral of death (when updates take longer than framerate allows)
                if (this.accumulatedTime > tickRate * 3) {
                    this.accumulatedTime = 0;
                    break;
                }
            }
            
            // Render at full speed
            this.render();
        } else {
            // Tab not focused - only render at 10fps to save power
            this.lastFocused = false;
            const lowPowerInterval = 1/10; // 10fps when not focused
            
            this.unfocusedTime += this.deltaTime;
            if (this.unfocusedTime >= lowPowerInterval) {
                this.unfocusedTime = 0;
                this.render();
            }
        }
        
        // Continue the loop
        this.animationId = requestAnimationFrame(timestamp => this.gameLoop(timestamp));
    }
}

// Start the game when the page is loaded
window.addEventListener('load', () => {
    const game = new Game();
});