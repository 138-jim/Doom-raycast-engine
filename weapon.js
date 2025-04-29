// Weapon.js - Handles weapon logic, rendering, and effects

class Weapon {
    constructor(audioManager) {
        this.recoil = 0;
        this.firing = false;
        this.cooldown = 0;
        this.flashDuration = 0;
        this.ammo = WEAPON_MAX_AMMO;
        this.reloading = false;
        this.reloadTimer = 0;
        
        // Store audio manager for sound effects
        this.audioManager = audioManager;
    }
    
    // Attempt to fire the weapon
    fire() {
        if (this.cooldown === 0 && !this.reloading) {
            if (this.ammo > 0) {
                // Trigger recoil and effects
                this.recoil = WEAPON_RECOIL;
                this.firing = true;
                this.cooldown = WEAPON_FIRE_COOLDOWN;
                this.flashDuration = 4;
                
                // Reduce ammo
                this.ammo -= 1;
                
                // Play sound
                if (this.audioManager) {
                    this.audioManager.playSound('gunShot');
                }
                
                return true;
            } else {
                // Empty gun click
                if (this.audioManager) {
                    this.audioManager.playSound('gunEmpty');
                }
                
                // Shorter cooldown for empty
                this.cooldown = Math.floor(WEAPON_FIRE_COOLDOWN / 2);
                
                return false;
            }
        }
        return false;
    }
    
    // Start reloading the weapon
    reload() {
        if (!this.reloading && this.ammo < WEAPON_MAX_AMMO) {
            this.reloading = true;
            this.reloadTimer = WEAPON_RELOAD_TIME;
            
            // Play reload sound
            if (this.audioManager) {
                this.audioManager.playSound('gunReload');
            }
        }
    }
    
    // Update weapon state each frame
    update() {
        // Handle recoil recovery
        if (this.recoil > 0) {
            this.recoil -= WEAPON_RECOIL_RECOVERY_SPEED;
            if (this.recoil < 0) {
                this.recoil = 0;
            }
        }
        
        // Handle cooldown
        if (this.cooldown > 0) {
            this.cooldown -= 1;
            if (this.cooldown === 0) {
                this.firing = false;
            }
        }
        
        // Handle muzzle flash
        if (this.flashDuration > 0) {
            this.flashDuration -= 1;
        }
        
        // Handle reloading
        if (this.reloading) {
            this.reloadTimer -= 1;
            if (this.reloadTimer <= 0) {
                this.ammo = WEAPON_MAX_AMMO;
                this.reloading = false;
            }
        }
    }
    
    // Draw the weapon and its effects
    draw(ctx, screenWidth, screenHeight) {
        // Calculate position with recoil
        const weaponImage = textureManager.weaponTextures.gun;
        const weaponWidth = weaponImage.width;
        const weaponHeight = weaponImage.height;
        const weaponX = screenWidth / 2 - weaponWidth / 2;
        const weaponY = screenHeight - weaponHeight + Math.floor(this.recoil);
        
        // Draw weapon
        ctx.drawImage(weaponImage, weaponX, weaponY);
        
        // Draw muzzle flash when firing
        if (this.flashDuration > 0) {
            const flashImage = textureManager.weaponTextures.muzzleFlash;
            const flashX = weaponX + 100;
            const flashY = weaponY + 25;
            ctx.drawImage(flashImage, flashX, flashY);
        }
        
        // Draw ammo counter
        ctx.font = '20px Arial';
        ctx.fillStyle = 'white';
        ctx.textAlign = 'right';
        const ammoText = `AMMO: ${this.ammo}/${WEAPON_MAX_AMMO}`;
        ctx.fillText(ammoText, screenWidth - 20, screenHeight - 20);
        
        // Update ammo text in UI
        const ammoTextElement = document.getElementById('ammo-text');
        if (ammoTextElement) {
            ammoTextElement.textContent = ammoText;
        }
        
        // Show reloading text
        if (this.reloading) {
            ctx.fillStyle = 'rgb(255, 200, 50)';
            ctx.fillText('RELOADING...', screenWidth - 20, screenHeight - 50);
        }
    }
}

// Audio Manager for handling game sounds
class AudioManager {
    constructor() {
        this.sounds = {};
        this.music = null;
        this.volumes = {
            master: 0.7,
            sfx: 0.5,
            music: 0.5
        };
    }
    
    // Load all audio files
    async loadSounds() {
        try {
            // Create directory for sounds if it doesn't exist in the server code
            
            // Load sound effects
            for (const [name, file] of Object.entries(AUDIO_FILES)) {
                // Create empty sound object (actual loading happens below for browser compatibility)
                this.sounds[name] = new Audio();
            }
            
            return true;
        } catch (error) {
            console.error("Error loading sounds:", error);
            return false;
        }
    }
    
    // Simulate actual sound loading for browser that might need user interaction
    activateAudio() {
        // Only try to load sounds after user interaction
        for (const [name, file] of Object.entries(AUDIO_FILES)) {
            try {
                // Use the predefined paths from constants.js
                this.sounds[name].src = file;
                
                // Set volume appropriate for sound type
                if (name === 'menuMusic') {
                    this.sounds[name].volume = this.volumes.master * this.volumes.music;
                    this.sounds[name].loop = true;
                } else {
                    this.sounds[name].volume = this.volumes.master * this.volumes.sfx;
                }
            } catch (error) {
                console.warn(`Could not load sound: ${name}`, error);
            }
        }
        
        // Store music separately for easier control
        this.music = this.sounds.menuMusic;
    }
    
    // Play a sound effect
    playSound(name) {
        if (!this.sounds[name]) return;
        
        try {
            // Clone the audio to allow overlapping sounds
            const sound = this.sounds[name].cloneNode();
            
            // Set volume based on current settings
            if (name === 'menuMusic') {
                sound.volume = this.volumes.master * this.volumes.music;
            } else {
                sound.volume = this.volumes.master * this.volumes.sfx;
            }
            
            sound.play().catch(error => {
                // Browser may prevent autoplay without user interaction
                console.warn(`Could not play sound: ${name}`, error);
            });
        } catch (error) {
            console.warn(`Error playing sound: ${name}`, error);
        }
    }
    
    // Play background music
    playMusic() {
        if (this.music) {
            this.music.volume = this.volumes.master * this.volumes.music;
            this.music.currentTime = 0;
            this.music.play().catch(error => {
                console.warn("Could not play music", error);
            });
        }
    }
    
    // Stop background music
    stopMusic() {
        if (this.music) {
            this.music.pause();
            this.music.currentTime = 0;
        }
    }
    
    // Update volume settings
    setVolume(type, value) {
        if (type in this.volumes) {
            this.volumes[type] = value;
            
            // Update music volume if it's playing
            if (type === 'master' || type === 'music') {
                if (this.music) {
                    this.music.volume = this.volumes.master * this.volumes.music;
                }
            }
        }
    }
}