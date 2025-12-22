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
    """Sprite pro statickou minu (záloha původní implementace)"""
    
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


# Alias pro zpětnou kompatibilitu
StaticMine = Mine


import math

class GuidedMine(arcade.Sprite):
    """Naváděná mina - sleduje nejbližšího nepřítele"""
    
    # Konfigurace naváděné miny
    SPEED = 1.2  # Stejná rychlost jako torpédo
    MAX_ROTATION_SPEED = 90  # stupně za sekundu (pomalejší než torpédo)
    DIRECTION_CHANGE_TIME = 0.3  # Jak často přehodnocuje cíl (sekundy)
    
    def __init__(self, x: float, y: float, radius: int, core_radius: int):
        """
        Inicializuj naváděnou minu
        
        Args:
            x, y: Počáteční pozice
            radius: Poloměr miny
            core_radius: Poloměr červeného středu
        """
        # Vytvoř texturu pro minu (zelená pro naváděnou)
        mine_texture = arcade.make_soft_circle_texture(
            radius * 2,
            arcade.color.LIME_GREEN,
            outer_alpha=255
        )
        super().__init__(mine_texture, center_x=x, center_y=y)
        self.radius = radius
        self.core_radius = core_radius
        self.blink_state = False
        
        # Reference na seznam nepřátel (nastaví se z main.py)
        self.enemy_list = None
        
        # Aktuální cíl
        self.current_target = None
        
        # Aktuální směr pohybu (úhel v radiánech)
        self.movement_angle = 0.0
        
        # Rychlost pohybu
        self.change_x = 0.0
        self.change_y = 0.0
        
        # Časovač pro přehodnocení cíle
        self.movement_timer = 0.0
    
    def draw_core(self, blink_on: bool):
        """Vykresli blikající červený střed"""
        if blink_on:
            arcade.draw_circle_filled(
                self.center_x, self.center_y,
                self.core_radius,
                arcade.color.RED
            )
    
    def find_closest_enemy(self):
        """
        Najdi nejbližšího nepřítele
        
        Returns:
            Nejbližší nepřítel nebo None pokud žádný není
        """
        if not self.enemy_list or len(self.enemy_list) == 0:
            return None
        
        closest_enemy = None
        closest_distance = float('inf')
        
        for enemy in self.enemy_list:
            # Přeskoč explodující nepřátele
            if hasattr(enemy, 'exploding') and enemy.exploding:
                continue
            
            dx = enemy.center_x - self.center_x
            dy = enemy.center_y - self.center_y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance < closest_distance:
                closest_distance = distance
                closest_enemy = enemy
        
        return closest_enemy
    
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
        
        Args:
            target_angle: Cílový úhel (radiány)
            delta_time: Časový krok (sekundy)
            
        Returns:
            Nový úhel pohybu (radiány)
        """
        # Vypočítej rozdíl úhlů
        angle_diff = target_angle - self.movement_angle
        
        # Normalizuj do rozsahu [-π, π] (nejkratší cesta)
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi
        
        # Omez maximální rychlost otáčení
        max_rotation = math.radians(self.MAX_ROTATION_SPEED) * delta_time
        
        if abs(angle_diff) <= max_rotation:
            return target_angle
        else:
            if angle_diff > 0:
                return self.movement_angle + max_rotation
            else:
                return self.movement_angle - max_rotation
    
    def update(self, delta_time: float = 1/60):
        """Update pozice a navádění"""
        # Časovač pro přehodnocení cíle
        self.movement_timer += delta_time
        
        should_reevaluate = False
        if self.movement_timer >= self.DIRECTION_CHANGE_TIME:
            self.movement_timer = 0
            should_reevaluate = True
        
        # Kontrola, zda aktuální cíl ještě existuje
        if self.current_target is not None:
            if self.enemy_list is None or self.current_target not in self.enemy_list:
                self.current_target = None
                should_reevaluate = True
            elif hasattr(self.current_target, 'exploding') and self.current_target.exploding:
                self.current_target = None
                should_reevaluate = True
        
        # Najdi cíl
        target_x = None
        target_y = None
        
        if should_reevaluate or self.current_target is None:
            closest_enemy = self.find_closest_enemy()
            if closest_enemy:
                self.current_target = closest_enemy
                target_x = closest_enemy.center_x
                target_y = closest_enemy.center_y
        elif self.current_target:
            target_x = self.current_target.center_x
            target_y = self.current_target.center_y
        
        # Pokud máme cíl, otoč se k němu a pohybuj se
        if target_x is not None and target_y is not None:
            target_angle = self.calculate_angle_to_target(target_x, target_y)
            self.movement_angle = self.smooth_rotate_towards(target_angle, delta_time)
            
            # Aktualizuj rychlost podle směru
            self.change_x = math.cos(self.movement_angle) * self.SPEED
            self.change_y = math.sin(self.movement_angle) * self.SPEED
        
        # Pohyb
        self.center_x += self.change_x
        self.center_y += self.change_y


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


class BonusExtraZivot(arcade.Sprite):
    """Bonus - přidá extra život"""
    
    BONUS_TYPE = "extra_zivot"
    RADIUS = 30
    
    def __init__(self, x: float, y: float):
        """
        Inicializuj bonus
        
        Args:
            x, y: Pozice bonusu
        """
        # Načti texturu z PNG
        try:
            super().__init__("pict/bonus_extra_zivot.png", center_x=x, center_y=y)
            # Škáluj na správnou velikost
            if self.texture.width > 0:
                self.scale = (self.RADIUS * 2) / max(self.texture.width, self.texture.height)
        except Exception as e:
            print(f"CHYBA: Nelze načíst bonus_extra_zivot.png: {e}")
            # Fallback - zelený kruh
            bonus_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                arcade.color.GREEN,
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


class BonusKanon(arcade.Sprite):
    """Bonus - přidá druhý kanon"""
    
    BONUS_TYPE = "kanon"
    RADIUS = 30
    
    def __init__(self, x: float, y: float):
        """
        Inicializuj bonus
        
        Args:
            x, y: Pozice bonusu
        """
        # Načti texturu z PNG
        try:
            super().__init__("pict/bonus_kanon.png", center_x=x, center_y=y)
            # Škáluj na správnou velikost
            if self.texture.width > 0:
                self.scale = (self.RADIUS * 2) / max(self.texture.width, self.texture.height)
        except Exception as e:
            print(f"CHYBA: Nelze načíst bonus_kanon.png: {e}")
            # Fallback - oranžový kruh
            bonus_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                arcade.color.ORANGE,
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


class BonusNavadeneMiny(arcade.Sprite):
    """Bonus - aktivuje naváděné miny místo statických"""
    
    BONUS_TYPE = "navadene_miny"
    RADIUS = 30
    
    def __init__(self, x: float, y: float):
        """
        Inicializuj bonus
        
        Args:
            x, y: Pozice bonusu
        """
        # Načti texturu z PNG
        try:
            super().__init__("pict/bonus_navadene_miny.png", center_x=x, center_y=y)
            # Škáluj na správnou velikost
            if self.texture.width > 0:
                self.scale = (self.RADIUS * 2) / max(self.texture.width, self.texture.height)
        except Exception as e:
            print(f"CHYBA: Nelze načíst bonus_navadene_miny.png: {e}")
            # Fallback - zelený kruh
            bonus_texture = arcade.make_soft_circle_texture(
                self.RADIUS * 2,
                arcade.color.LIME_GREEN,
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