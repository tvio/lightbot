"""
LightBot - Base Enemy class
Základní třída pro všechny typy nepřátel
"""
import arcade
import math
import random
from typing import Optional, List, Tuple
from infrastruktura import load_enemy_animations


class BaseEnemy(arcade.Sprite):
    """Základní třída pro nepřátele"""
    
    # Třídní proměnné - přepíší se v podtřídách
    ENEMY_TYPE_NAME = "base_enemy"
    GIF_PATH = None
    RADIUS = 15
    SPEED = 1
    ANIMATION_FRAME_DURATION = 0.15
    SCALE_MULTIPLIER = 2
    MOVEMENT_TYPE = "sideway"  # "sideway" nebo "direct"
    DIRECTION_CHANGE_TIME_RANGE = [5, 12]  # [min, max] sekund
    MAX_HEALTH = 1  # Kolik hitů vydrží nepřítel
    
    # Třídní proměnné pro screen dimensions (nastaví se z main)
    SCREEN_WIDTH = 1600
    SCREEN_HEIGHT = 1000
    
    # Cache pro animace - sdílený mezi všemi instancemi stejného typu
    _animation_cache: Optional[List[arcade.Texture]] = None
    _base_texture_size: Optional[int] = None
    
    def __init__(self, x: float, y: float, side_direction: Optional[int] = None, target_x: Optional[float] = None, target_y: Optional[float] = None):
        """
        Inicializuj nepřítele
        
        Args:
            x, y: Počáteční pozice
            side_direction: -1 (levá strana) nebo +1 (pravá strana), None = náhodně
            target_x, target_y: Cílová pozice (pro direct pohyb)
        """
        # Načti animované framy z cache (sdílené textury)
        animation_textures = self._load_cached_animations()
        
        self.animation_textures = animation_textures
        self.current_frame = 0
        self.animation_timer = 0
        
        if animation_textures:
            # Nastav první frame
            super().__init__(animation_textures[0])
            self.center_x = x
            self.center_y = y
            
            # Škáluj na správnou velikost
            if self._base_texture_size and self._base_texture_size > 0:
                self.scale = (self.RADIUS * 2 * self.SCALE_MULTIPLIER) / self._base_texture_size
        else:
            # Fallback - kruh
            enemy_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                arcade.color.YELLOW,
                outer_alpha=255
            )
            super().__init__(enemy_texture, center_x=x, center_y=y)
        
        # Stav pro výbuch
        self.exploding = False
        self.explode_timer = 0
        self.blink_state = False
        
        # Životy
        self.health = self.MAX_HEALTH
        self.max_health = self.MAX_HEALTH
        
        # Rotace - náhodně
        random_angle = random.uniform(0, 360)
        self.angle = -random_angle
        
        # Ulož cílovou pozici pro direct pohyb
        self.target_x = target_x
        self.target_y = target_y
        
        # Pohyb podle typu
        self._setup_movement(side_direction)
    
    @classmethod
    def _load_cached_animations(cls) -> Optional[List[arcade.Texture]]:
        """Načti animace - sdíleno mezi všemi instancemi"""
        if cls.GIF_PATH is None:
            return None
            
        # Pokud máme v cache, vrátíme z cache
        if cls._animation_cache is not None:
            return cls._animation_cache
        
        # Jinak načteme
        textures, base_size = load_enemy_animations(cls.GIF_PATH)
        if textures:
            cls._animation_cache = textures
            cls._base_texture_size = base_size
            return textures
        
        return None
    
    def _setup_movement(self, side_direction: Optional[int]):
        """Nastav pohyb nepřítele podle typu"""
        if self.MOVEMENT_TYPE == "sideway":
            self._setup_sideway_movement(side_direction)
        elif self.MOVEMENT_TYPE == "direct":
            self._setup_direct_movement()
        elif self.MOVEMENT_TYPE == "player_seeking":
            self._setup_player_seeking_movement()
        else:
            self._setup_sideway_movement(side_direction)
    
    def _setup_sideway_movement(self, side_direction: Optional[int]):
        """Postranní pohyb (jako krab)"""
        if side_direction is None:
            self.side_direction = random.choice([-1, 1])
        else:
            self.side_direction = side_direction
        
        # Úhel pohybu = úhel rotace + offset podle side_direction
        movement_angle_degrees = self.angle + (self.side_direction * 90)
        movement_angle_rad = math.radians(abs(movement_angle_degrees))
        
        self.change_x = math.cos(movement_angle_rad) * self.SPEED
        self.change_y = math.sin(movement_angle_rad) * self.SPEED
        
        # Časovač pro změnu směru
        self.movement_timer = 0
        self.direction_change_time = random.uniform(
            self.DIRECTION_CHANGE_TIME_RANGE[0],
            self.DIRECTION_CHANGE_TIME_RANGE[1]
        )
    
    def _setup_direct_movement(self):
        """Přímý pohyb (hvězda směřuje přímo)"""
        # Pokud máme cílovou pozici, směřuj k ní
        if self.target_x is not None and self.target_y is not None:
            dx = self.target_x - self.center_x
            dy = self.target_y - self.center_y
            angle_to_target = math.atan2(dy, dx)
            
            self.change_x = math.cos(angle_to_target) * self.SPEED
            self.change_y = math.sin(angle_to_target) * self.SPEED
            
            # Nastav rotaci sprite podle směru pohybu
            self.angle = -math.degrees(angle_to_target)
        else:
            # Jinak pohyb náhodným směrem
            movement_angle_rad = math.radians(abs(self.angle))
            
            self.change_x = math.cos(movement_angle_rad) * self.SPEED
            self.change_y = math.sin(movement_angle_rad) * self.SPEED
    
    def _setup_player_seeking_movement(self):
        """Pohyb sledující hráče (Prudic)"""
        # Inicializuj player reference (nastaví se z main.py při spawnu)
        self.player = None
        
        # Časovač pro změnu směru (update pohybu směrem k hráči)
        self.movement_timer = 0
        self.direction_change_time = random.uniform(
            self.DIRECTION_CHANGE_TIME_RANGE[0],
            self.DIRECTION_CHANGE_TIME_RANGE[1]
        )
    
    def update(self, delta_time: float = 1/60):
        """Update pozice a pohybového vzoru"""
        # Aktualizuj animaci
        if self.animation_textures and len(self.animation_textures) > 1 and not self.exploding:
            self.animation_timer += delta_time
            if self.animation_timer >= self.ANIMATION_FRAME_DURATION:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.animation_textures)
                self.texture = self.animation_textures[self.current_frame]
        
        # Výbuch
        if self.exploding:
            self.explode_timer -= delta_time
            self.update_explosion()
            if self.explode_timer <= 0:
                self.remove_from_sprite_lists()
                return
        
        # Pokud vybuchuje, nehýbej se
        if self.exploding:
            return
        
        # Pohyb
        self.center_x += self.change_x
        self.center_y += self.change_y
        
        # Wraparound
        self._handle_wraparound()
        
        # Aktualizuj pohyb podle typu
        if self.MOVEMENT_TYPE == "sideway":
            self._update_sideway_movement(delta_time)
        elif self.MOVEMENT_TYPE == "player_seeking":
            self._update_player_seeking_movement(delta_time)
    
    def _handle_wraparound(self):
        """Zabal nepřítele kolem okrajů obrazovky"""
        if self.center_x < -self.RADIUS:
            self.center_x = self.SCREEN_WIDTH - self.RADIUS
        elif self.center_x > self.SCREEN_WIDTH + self.RADIUS:
            self.center_x = self.RADIUS
            
        if self.center_y < -self.RADIUS:
            self.center_y = self.SCREEN_HEIGHT - self.RADIUS
        elif self.center_y > self.SCREEN_HEIGHT + self.RADIUS:
            self.center_y = self.RADIUS
    
    def _update_sideway_movement(self, delta_time: float):
        """Aktualizuj postranní pohyb"""
        self.movement_timer += delta_time
        
        # Pohyb s oblouky
        movement_angle_degrees = self.angle + (self.side_direction * 90)
        movement_angle_rad = math.radians(abs(movement_angle_degrees))
        
        if random.random() < 0.3:  # 30% šance každý frame
            current_movement_angle = movement_angle_rad + random.uniform(-0.02, 0.02)
            self.change_x = math.cos(current_movement_angle) * self.SPEED
            self.change_y = math.sin(current_movement_angle) * self.SPEED
        else:
            self.change_x = math.cos(movement_angle_rad) * self.SPEED
            self.change_y = math.sin(movement_angle_rad) * self.SPEED
        
        # Změna směru
        if self.movement_timer >= self.direction_change_time:
            self.movement_timer = 0
            self.direction_change_time = random.uniform(
                self.DIRECTION_CHANGE_TIME_RANGE[0],
                self.DIRECTION_CHANGE_TIME_RANGE[1]
            )
            self.side_direction *= -1
            
            # Přepočítej pohyb
            movement_angle_degrees = self.angle + (self.side_direction * 90)
            movement_angle_rad = math.radians(abs(movement_angle_degrees))
            self.change_x = math.cos(movement_angle_rad) * self.SPEED
            self.change_y = math.sin(movement_angle_rad) * self.SPEED
    
    def _update_player_seeking_movement(self, delta_time: float):
        """Aktualizuj pohyb sledující hráče (Prudic)"""
        self.movement_timer += delta_time
        
        # Pravidelně aktualizuj směr k hráči
        if self.movement_timer >= self.direction_change_time:
            self.movement_timer = 0
            self.direction_change_time = random.uniform(
                self.DIRECTION_CHANGE_TIME_RANGE[0],
                self.DIRECTION_CHANGE_TIME_RANGE[1]
            )
            
            # Směřuj k hráči
            if self.player and hasattr(self.player, 'center_x'):
                dx = self.player.center_x - self.center_x
                dy = self.player.center_y - self.center_y
                angle_to_player = math.atan2(dy, dx)
                
                self.change_x = math.cos(angle_to_player) * self.SPEED
                self.change_y = math.sin(angle_to_player) * self.SPEED
                
                # Nastav rotaci sprite podle směru pohybu
                self.angle = -math.degrees(angle_to_player)
    
    def take_damage(self, damage: int = 1):
        """Ubeř život nepříteli
        
        Args:
            damage: Kolik životů ubrat
        
        Returns:
            True pokud nepřítel zemřel, False pokud přežil
        """
        self.health -= damage
        if self.health <= 0:
            self.start_explosion()
            return True
        return False
    
    def start_explosion(self):
        """Začni výbuch"""
        self.exploding = True
        self.explode_timer = 0.2
        self.blink_state = True
        self.health = 0
    
    def update_explosion(self):
        """Aktualizuj vizuál výbuchu"""
        if self.exploding:
            self.blink_state = not self.blink_state
            if self.blink_state:
                color = arcade.color.RED
            else:
                color = arcade.color.ORANGE_RED
                
            red_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                color,
                outer_alpha=255
            )
            self.texture = red_texture
