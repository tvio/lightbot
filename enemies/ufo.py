"""
LightBot - UFO Enemy
Rychlý nepřítel, který letí přes obrazovku a při zničení nechá bonus
"""
from .base_enemy import BaseEnemy
import math
import random
from typing import Optional


class Ufo(BaseEnemy):
    """UFO - rychlý nepřítel, který letí přes obrazovku a nechává bonus"""
    
    # Konfigurace UFO
    ENEMY_TYPE_NAME = "ufo"
    GIF_PATH = None  # Načte se z game_config.yaml
    RADIUS = 15
    SPEED = 4  # Vysoká rychlost
    ANIMATION_FRAME_DURATION = 0.1
    SCALE_MULTIPLIER = 2
    MOVEMENT_TYPE = "flythrough"  # Nový typ - letí přes obrazovku
    DIRECTION_CHANGE_TIME_RANGE = [0, 0]  # Nemění směr
    MAX_HEALTH = 1
    
    # Flag pro bonus
    DROPS_BONUS = True
    
    def __init__(self, x: float, y: float, side_direction: Optional[int] = None, 
                 target_x: Optional[float] = None, target_y: Optional[float] = None):
        """
        Inicializuj UFO
        
        Args:
            x, y: Počáteční pozice
            side_direction: Nepoužívá se
            target_x, target_y: Cílová pozice (kam letí)
        """
        super().__init__(x, y, side_direction, target_x, target_y)
        
        # Flag pro kontrolu, zda už opustilo obrazovku
        self.has_left_screen = False
    
    def _setup_movement(self, side_direction: Optional[int]):
        """Nastav pohyb pro UFO - letí přímo k cíli"""
        if self.target_x is not None and self.target_y is not None:
            # Vypočítej směr k cíli
            dx = self.target_x - self.center_x
            dy = self.target_y - self.center_y
            distance = math.sqrt(dx * dx + dy * dy)
            
            if distance > 0:
                # Normalizuj a nastav rychlost
                self.change_x = (dx / distance) * self.SPEED
                self.change_y = (dy / distance) * self.SPEED
                
                # Nastav rotaci sprite podle směru
                angle = math.degrees(math.atan2(dy, dx))
                self.angle = -angle
        else:
            # Fallback - letí doprava
            self.change_x = self.SPEED
            self.change_y = 0
            self.angle = 0
    
    def update(self, delta_time: float = 1/60):
        """
        Update pozice UFO
        
        UFO letí přímo a zmizí když opustí obrazovku (bez wraparound)
        """
        # Aktualizuj animaci
        if self.animation_textures and len(self.animation_textures) > 1 and not self.exploding:
            self.animation_timer += delta_time
            if self.animation_timer >= self.ANIMATION_FRAME_DURATION:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.animation_textures)
                self.texture = self.animation_textures[self.current_frame]
        
        # Pokud exploduje, použij základní logiku
        if self.exploding:
            self.explode_timer -= delta_time
            self.update_explosion()
            if self.explode_timer <= 0:
                self.remove_from_sprite_lists()
            return
        
        # Pohyb
        self.center_x += self.change_x
        self.center_y += self.change_y
        
        # Kontrola, zda opustilo obrazovku (bez wraparound - prostě zmizí)
        margin = self.RADIUS * self.SCALE_MULTIPLIER + 50
        if (self.center_x < -margin or 
            self.center_x > self.SCREEN_WIDTH + margin or
            self.center_y < -margin or 
            self.center_y > self.SCREEN_HEIGHT + margin):
            self.remove_from_sprite_lists()

