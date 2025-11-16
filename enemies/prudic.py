"""
LightBot - Prudic Enemy
Nepřítel Prudic - těžký nepřítel, který jde přímo na hráče a vydrží 5 hitů
"""
from .base_enemy import BaseEnemy
import math
import random
from typing import Optional, List
from infrastruktura import load_sprite_sheet
import arcade


class Prudic(BaseEnemy):
    """Prudic - těžký nepřítel s 5 životy"""
    
    # Konfigurace Prudice
    ENEMY_TYPE_NAME = "prudic"
    GIF_PATH = None  # Nepoužíváme GIF
    SPRITE_SHEET_PATH = None  # Nepoužíváme sprite sheet
    SPRITE_IMAGE_PATH = None  # Načte se z game_config.yaml
    SPRITE_WIDTH = 0  # Nepoužívá se
    SPRITE_HEIGHT = 0  # Nepoužívá se
    SPRITE_COLUMNS = 1  # Nepoužívá se
    SPRITE_ROWS = 1  # Nepoužívá se
    
    RADIUS = 20
    SPEED = 0.8  # Pomalejší než ostatní
    ANIMATION_FRAME_DURATION = 0.15
    SCALE_MULTIPLIER = 4  # Zvětšeno o 100% (z 2 na 4)
    MOVEMENT_TYPE = "player_seeking"  # Jde přímo na hráče
    DIRECTION_CHANGE_TIME_RANGE = [0.5, 0.5]  # Každých 0.5s přehodnocuje cíl
    MAX_HEALTH = 5  # Vydrží 5 hitů
    
    # Parametry rotace obrázku (animace - nezávislá na směru pohybu)
    ROTATION_SPEED = 120  # stupně za sekundu (360° za 3s)
    
    # Parametry otáčení směru pohybu (stejné jako torpédo)
    MAX_ROTATION_SPEED = 120  # stupně za sekundu
    
    @classmethod
    def _load_cached_animations(cls) -> Optional[List[arcade.Texture]]:
        """Načti statický obrázek pro rotaci - sdíleno mezi všemi instancemi"""
        # Pokud máme v cache, vrátíme z cache
        if cls._animation_cache is not None:
            return cls._animation_cache
        
        # Načteme jeden PNG obrázek
        try:
            texture = arcade.load_texture(cls.SPRITE_IMAGE_PATH)
            # Vytvoříme list s jedním texture (pro kompatibilitu s BaseEnemy)
            textures = [texture]
            
            # Zjisti základní velikost
            base_size = max(texture.width, texture.height)
            
            cls._animation_cache = textures
            cls._base_texture_size = base_size
            return textures
        except Exception as e:
            print(f"CHYBA: Nelze nacist obrazek {cls.SPRITE_IMAGE_PATH}: {e}")
            return None
    
    def __init__(self, x: float, y: float, side_direction: Optional[int] = None, 
                 target_x: Optional[float] = None, target_y: Optional[float] = None):
        """
        Inicializuj Prudic
        
        Args:
            x, y: Počáteční pozice
            side_direction: Nepoužívá se pro Prudic
            target_x, target_y: Nepoužívá se (Prudic si vybírá cíl samo)
        """
        # Reference na hráče (bude nastavena z main.py)
        self.player = None
        
        # Aktuální cíl (hráč)
        self.current_target = None
        
        # Aktuální směr pohybu (úhel v radiánech)
        self.movement_angle = 0
        
        super().__init__(x, y, side_direction, target_x, target_y)
        
        # Úhel rotace obrázku (pro animaci rotace) - nezávislý na směru pohybu
        self.rotation_angle = 0.0  # V stupních
    
    def _setup_movement(self, side_direction: Optional[int]):
        """Nastav pohyb pro Prudic - přepíše základní metodu"""
        # Začni s náhodným směrem
        # self.angle je již nastaven v BaseEnemy.__init__ jako náhodný
        # Převeď ho na radiány pro movement_angle
        self.movement_angle = math.radians(-self.angle)  # Záporně kvůli Arcade konvenci
        
        self.change_x = math.cos(self.movement_angle) * self.SPEED
        self.change_y = math.sin(self.movement_angle) * self.SPEED
        
        # Časovač pro aktualizaci cíle
        self.movement_timer = 0
        self.direction_change_time = self.DIRECTION_CHANGE_TIME_RANGE[0]
    
    def calculate_angle_to_target(self, target_x: float, target_y: float) -> float:
        """
        Vypočítej úhel k cíli
        
        Args:
            target_x, target_y: Pozice cíle
            
        Returns:
            Úhel v radiánech
        """
        dx = target_x - self.center_x
        dy = target_y - self.center_y
        return math.atan2(dy, dx)
    
    def smooth_rotate_towards(self, target_angle: float, delta_time: float) -> float:
        """
        Plynule otoč směrem k cílovému úhlu
        
        Stejná logika jako u torpéda - plynulé otáčení s omezenou rychlostí.
        
        Args:
            target_angle: Cílový úhel (radiány)
            delta_time: Časový krok (sekundy)
            
        Returns:
            Nový úhel pohybu (radiány)
        """
        # 1. Vypočítej rozdíl úhlů
        angle_diff = target_angle - self.movement_angle
        
        # 2. Normalizuj do rozsahu [-π, π] (nejkratší cesta)
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        # 3. Omez maximální rychlost otáčení
        max_rotation = math.radians(self.MAX_ROTATION_SPEED) * delta_time
        
        if abs(angle_diff) <= max_rotation:
            # Můžeme se otočit přímo k cíli
            return target_angle
        else:
            # Otočíme se jen o maximální povolenou hodnotu
            if angle_diff > 0:
                return self.movement_angle + max_rotation
            else:
                return self.movement_angle - max_rotation
    
    def update_player_seeking_behavior(self, delta_time: float):
        """
        Aktualizuj chování sledování hráče
        
        Používá stejnou logiku jako torpédo, ale pouze pro hráče (bez min).
        
        Logika:
        1. Najdi hráče
        2. Plynule otoč směrem k hráči
        3. Aktualizuj rychlost pohybu
        """
        # 1. Kontrola časovače pro přehodnocení cíle
        self.movement_timer += delta_time
        
        should_reevaluate = False
        if self.movement_timer >= self.direction_change_time:
            self.movement_timer = 0
            should_reevaluate = True
        
        # 2. Najdi cíl (hráč)
        target_x = None
        target_y = None
        
        if should_reevaluate or self.current_target is None:
            if self.player:
                # Cíl je hráč
                self.current_target = self.player
                target_x = self.player.center_x
                target_y = self.player.center_y
        else:
            # Použij aktuální cíl (hráč)
            if self.current_target:
                target_x = self.current_target.center_x
                target_y = self.current_target.center_y
        
        # 3. Pokud máme cíl, otoč se k němu
        if target_x is not None and target_y is not None:
            target_angle = self.calculate_angle_to_target(target_x, target_y)
            self.movement_angle = self.smooth_rotate_towards(target_angle, delta_time)
            
            # 4. Aktualizuj rychlost podle směru
            self.change_x = math.cos(self.movement_angle) * self.SPEED
            self.change_y = math.sin(self.movement_angle) * self.SPEED
    
    def update(self, delta_time: float = 1/60):
        """
        Update pozice a rotace obrázku
        
        Přepíše základní update metodu
        """
        # Aktualizuj rotaci obrázku (animace - 360° za 3s) - nezávislá na směru pohybu
        self.rotation_angle += self.ROTATION_SPEED * delta_time
        if self.rotation_angle >= 360:
            self.rotation_angle -= 360
        
        # Nastav vizuální rotaci sprite (nezávisle na směru pohybu)
        self.angle = -self.rotation_angle  # Záporně kvůli Arcade konvenci
        
        # Pokud exploduje, použij základní logiku
        if self.exploding:
            self.explode_timer += delta_time
            
            # Blikání (každých 0.1s)
            if int(self.explode_timer * 10) % 2 == 0:
                self.visible = True
            else:
                self.visible = False
            
            # Po 1s zmiz
            if self.explode_timer > 1.0:
                self.kill()
            return
        
        # Aktualizuj chování sledování hráče
        self.update_player_seeking_behavior(delta_time)
        
        # Pohyb
        self.center_x += self.change_x
        self.center_y += self.change_y
        
        # Wraparound (ze základní třídy)
        if self.center_x < -self.RADIUS:
            self.center_x = self.SCREEN_WIDTH + self.RADIUS
        elif self.center_x > self.SCREEN_WIDTH + self.RADIUS:
            self.center_x = -self.RADIUS
        
        if self.center_y < -self.RADIUS:
            self.center_y = self.SCREEN_HEIGHT + self.RADIUS
        elif self.center_y > self.SCREEN_HEIGHT + self.RADIUS:
            self.center_y = -self.RADIUS

