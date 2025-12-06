"""
LightBot - Player a Mine sprites
"""
import arcade


class Player(arcade.Sprite):
    """Sprite pro hráče (robota)"""
    
    def __init__(self, x: float, y: float, radius: int, max_shockwave_charges: int = 7):
        """
        Inicializuj hráče
        
        Args:
            x, y: Počáteční pozice
            radius: Poloměr robota
            max_shockwave_charges: Maximální počet shockwave vln
        """
        # Vytvoř texturu pro hráče (bílý kruh)
        player_texture = arcade.make_soft_circle_texture(
            radius * 2,
            arcade.color.WHITE,
            outer_alpha=255
        )
        super().__init__(player_texture, center_x=x, center_y=y)
        
        self.radius = radius
        
        # Stav pro konec hry
        self.game_over = False
        self.explode_timer = 0
        self.blink_state = False
        
        # Shockwave baterie
        self.max_shockwave_charges = max_shockwave_charges
        self.shockwave_charges = max_shockwave_charges
    
    def start_game_over(self):
        """Začni konec hry - zčervení a blikání"""
        self.game_over = True
        self.explode_timer = 0.5  # Bliká 0.5 sekundy
        self.blink_state = True
    
    def update_game_over(self):
        """Aktualizuj blikání při konci hry"""
        if self.game_over:
            # Rychle bliká mezi červenou a jasnější červenou
            self.blink_state = not self.blink_state
            if self.blink_state:
                color = arcade.color.RED
            else:
                color = arcade.color.ORANGE_RED  # Jasnější červená
                
            red_texture = arcade.make_soft_circle_texture(
                self.radius * 2,
                color,
                outer_alpha=255
            )
            self.texture = red_texture
    
    def update_color(self, is_day: bool, day_color: tuple, night_color: tuple):
        """Aktualizuj barvu robota podle dne/noci (pokud není game over)"""
        if not self.game_over:
            if is_day:
                color = day_color
            else:
                color = night_color
            
            new_texture = arcade.make_soft_circle_texture(
                self.radius * 2,
                color,
                outer_alpha=255
            )
            self.texture = new_texture


class Mine(arcade.Sprite):
    """Sprite pro minu"""
    
    def __init__(self, x: float, y: float, radius: int, core_radius: int):
        """
        Inicializuj minu
        
        Args:
            x, y: Počáteční pozice
            radius: Poloměr miny
            core_radius: Poloměr červeného středu
        """
        # Vytvoř texturu pro minu
        mine_texture = arcade.make_soft_circle_texture(
            radius * 2,
            arcade.color.BLUE,
            outer_alpha=255
        )
        super().__init__(mine_texture, center_x=x, center_y=y)
        self.radius = radius
        self.core_radius = core_radius
        self.blink_state = False
    
    def draw_core(self, blink_on: bool):
        """Vykresli blikající červený střed"""
        if blink_on:
            arcade.draw_circle_filled(
                self.center_x, self.center_y,
                self.core_radius,
                arcade.color.RED
            )


class BonusBomba(arcade.Sprite):
    """Bonus - přidá náboj do světelné bomby"""
    
    BONUS_TYPE = "bomba"
    RADIUS = 30
    
    def __init__(self, x: float, y: float):
        """
        Inicializuj bonus
        
        Args:
            x, y: Pozice bonusu
        """
        # Načti texturu z PNG
        try:
            super().__init__("pict/bonus_bomba.png", center_x=x, center_y=y)
            # Škáluj na správnou velikost
            if self.texture.width > 0:
                self.scale = (self.RADIUS * 2) / max(self.texture.width, self.texture.height)
        except Exception as e:
            print(f"CHYBA: Nelze načíst bonus_bomba.png: {e}")
            # Fallback - žlutý kruh
            bonus_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                arcade.color.GOLD,
                outer_alpha=255
            )
            super().__init__(bonus_texture, center_x=x, center_y=y)
        
        # Životnost bonusu (zmizí po 10 sekundách)
        self.lifetime = 10.0
    
    def update(self, delta_time: float = 1/60):
        """Update bonusu - životnost"""
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()


class BonusMiny(arcade.Sprite):
    """Bonus - zdvojnásobí maximální počet min"""
    
    BONUS_TYPE = "miny"
    RADIUS = 30
    
    def __init__(self, x: float, y: float):
        """
        Inicializuj bonus
        
        Args:
            x, y: Pozice bonusu
        """
        # Načti texturu z PNG
        try:
            super().__init__("pict/bonus_pocet_min.png", center_x=x, center_y=y)
            # Škáluj na správnou velikost
            if self.texture.width > 0:
                self.scale = (self.RADIUS * 2) / max(self.texture.width, self.texture.height)
        except Exception as e:
            print(f"CHYBA: Nelze načíst bonus_pocet_min.png: {e}")
            # Fallback - modrý kruh
            bonus_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                arcade.color.BLUE,
                outer_alpha=255
            )
            super().__init__(bonus_texture, center_x=x, center_y=y)
        
        # Životnost bonusu (zmizí po 10 sekundách)
        self.lifetime = 10.0
    
    def update(self, delta_time: float = 1/60):
        """Update bonusu - životnost"""
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()


class BonusShockwave(arcade.Sprite):
    """Bonus - zdvojnásobí průměr shockwave"""
    
    BONUS_TYPE = "shockwave"
    RADIUS = 30
    
    def __init__(self, x: float, y: float):
        """
        Inicializuj bonus
        
        Args:
            x, y: Pozice bonusu
        """
        # Načti texturu z PNG
        try:
            super().__init__("pict/bonus_shockwave.png", center_x=x, center_y=y)
            # Škáluj na správnou velikost
            if self.texture.width > 0:
                self.scale = (self.RADIUS * 2) / max(self.texture.width, self.texture.height)
        except Exception as e:
            print(f"CHYBA: Nelze načíst bonus_shockwave.png: {e}")
            # Fallback - bílý kruh
            bonus_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                arcade.color.WHITE,
                outer_alpha=255
            )
            super().__init__(bonus_texture, center_x=x, center_y=y)
        
        # Životnost bonusu (zmizí po 10 sekundách)
        self.lifetime = 10.0
    
    def update(self, delta_time: float = 1/60):
        """Update bonusu - životnost"""
        self.lifetime -= delta_time
        if self.lifetime <= 0:
            self.remove_from_sprite_lists()