"""
LightBot - Fáze 2
Koule následující myš + rotující dělo (WSAD)

Refaktorované verze s modulární strukturou a YAML konfigurací
"""
import arcade
import math
import yaml
import random
import os
import glob
from typing import Tuple, Optional

# Import modulů
from player import Player, Mine
from infrastruktura import find_laser_collision_with_enemies, calculate_laser_end
from enemies.base_enemy import BaseEnemy
from enemies import Crab, Star, Torpedo, Prudic

# ============================================================================
# KONFIGURAČNÍ KONSTANTY (z game_config.yaml)
# ============================================================================

def load_config():
    """Načti konfiguraci z game_config.yaml"""
    try:
        with open('game_config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Chyba při načítání config: {e}")
        return None

CONFIG = load_config()

# Pokud se config nenačetl, použij výchozí hodnoty
if CONFIG is None:
    CONFIG = {
        'screen': {'width': 1600, 'height': 1000, 'title': 'LightBot'},
        'player': {'radius': 20, 'perimeter_radius': 25},
        'cannon': {'length': 15, 'rotation_speed': 3},
        'laser': {'duration': 0.1, 'recharge_time': 3.0},
        'day_night': {'day_length': 30.0, 'night_length': 30.0},
        'mines': {'max_count': 15},
    }

# Extrahuj hodnoty z configu
SCREEN_WIDTH = CONFIG['screen']['width']
SCREEN_HEIGHT = CONFIG['screen']['height']
SCREEN_TITLE = CONFIG['screen']['title']

ROBOT_RADIUS = CONFIG['player']['radius']
PERIMETER_RADIUS = CONFIG['player']['perimeter_radius']
DAY_ROBOT_COLOR = tuple(CONFIG['player']['color_day'])
NIGHT_ROBOT_COLOR = tuple(CONFIG['player']['color_night'])

CANNON_LENGTH = CONFIG['cannon']['length']
ROTATION_SPEED = CONFIG['cannon']['rotation_speed']

LASER_DURATION = CONFIG['laser']['duration']
LASER_RECHARGE_TIME = CONFIG['laser']['recharge_time']

SHOCKWAVE_MAX_CHARGES = CONFIG['shockwave']['max_charges']
SHOCKWAVE_RADIUS = CONFIG['shockwave']['radius']
SHOCKWAVE_ANIMATION_DURATION = CONFIG['shockwave']['animation_duration']
SHOCKWAVE_COLOR = tuple(CONFIG['shockwave']['wave_color'])

DAY_LENGTH = CONFIG['day_night']['day_length']
NIGHT_LENGTH = CONFIG['day_night']['night_length']
START_WITH_DAY = CONFIG['day_night']['start_with_day']
DAY_BACKGROUND_COLOR = tuple(CONFIG['day_night']['day_background_color'])
NIGHT_BACKGROUND_COLOR = tuple(CONFIG['day_night']['night_background_color'])

MINE_RADIUS = CONFIG['mines']['radius']
MINE_CORE_RADIUS = CONFIG['mines']['core_radius']
BLINK_SPEED = CONFIG['mines']['blink_speed']
MAX_MINES = CONFIG['mines']['max_count']

ENEMY_SPAWN_TIME = CONFIG['enemies']['spawn_time']
MAX_SPAWN_MARGIN = CONFIG['enemies']['spawn_margin']

# Enemy konfigurace
ENEMY_TYPES = {
    'crab': Crab,
    'star': Star,
    'torpedo': Torpedo,
    'prudic': Prudic,
}
ENEMY_CONFIG = CONFIG['enemies_config']

# Wave konfigurace
WAVES_CONFIG = CONFIG.get('waves', [])

# Nastav screen dimensions pro BaseEnemy (pro wraparound)
BaseEnemy.SCREEN_WIDTH = SCREEN_WIDTH
BaseEnemy.SCREEN_HEIGHT = SCREEN_HEIGHT

# Aplikuj konfiguraci na enemy třídy
for enemy_type_name, EnemyClass in ENEMY_TYPES.items():
    if enemy_type_name in ENEMY_CONFIG:
        enemy_cfg = ENEMY_CONFIG[enemy_type_name]
        # Nastav MAX_HEALTH z configu, pokud existuje
        if 'max_health' in enemy_cfg:
            EnemyClass.MAX_HEALTH = enemy_cfg['max_health']

# ============================================================================
# HUDEBNÍ SYSTÉM
# ============================================================================

def load_music_files():
    """Načti všechny MP3 soubory z music adresáře"""
    music_dir = "music"
    if not os.path.exists(music_dir):
        print(f"Adresář {music_dir} neexistuje!")
        return []
    
    mp3_files = glob.glob(os.path.join(music_dir, "*.mp3"))
    mp3_files.sort()  # Seřaď abecedně
    
    if not mp3_files:
        print(f"Žádné MP3 soubory v {music_dir}!")
        return []
    
    print(f"Nalezeno {len(mp3_files)} hudebních souborů:")
    for file in mp3_files:
        print(f"  - {os.path.basename(file)}")
    
    return mp3_files

MUSIC_FILES = load_music_files()


class Game(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)
        
        # Povol sledování výkonu pro FPS
        arcade.enable_timings()
        
        # Zapni VSync
        self.set_vsync(True)
        
        # Schovej kurzor myši
        self.set_mouse_visible(False)
        
        # Skóre
        self.score = 0
        
        # Hráč sprite
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, ROBOT_RADIUS, SHOCKWAVE_MAX_CHARGES)
        self.player_list = arcade.SpriteList(use_spatial_hash=False)
        self.player_list.append(self.player)
        
        # Úhel děla
        self.cannon_angle = 0
        
        # Animace zmizení děla v noci
        self.cannon_fade_time = 2.0
        self.cannon_fade_timer = 0.0 if START_WITH_DAY else self.cannon_fade_time
        
        # Klávesy pro rotaci
        self.rotate_left = False
        self.rotate_right = False
        
        # Laser
        self.laser_active = False
        self.laser_timer = 0
        self.laser_start_x = 0
        self.laser_start_y = 0
        self.laser_end_x = 0
        self.laser_end_y = 0
        self.debug_shot_count = 0
        
        # Den/Noc
        self.is_day = START_WITH_DAY
        
        # Systém dobití
        self.laser_charge_time = LASER_RECHARGE_TIME if START_WITH_DAY else 0
        if self.is_day:
            self.day_night_timer = DAY_LENGTH
        else:
            self.day_night_timer = NIGHT_LENGTH
        self.player_color_day = self.is_day
        
        # Nastav barvu hráče
        self.player.update_color(self.is_day, DAY_ROBOT_COLOR, NIGHT_ROBOT_COLOR)
        
        # Miny
        self.mine_list = arcade.SpriteList(use_spatial_hash=True)
        
        # Časovač pro blikání min
        self.blink_timer = 0
        
        # Shockwave animace
        self.shockwave_active = False
        self.shockwave_timer = 0
        self.shockwave_radius_current = 0
        
        # Nepřátelé
        self.enemy_list = arcade.SpriteList(use_spatial_hash=False)
        
        # Spawn timery pro každého nepřítele samostatně
        self.enemy_spawn_timers = {}
        for enemy_type in ENEMY_TYPES.keys():
            enemy_config = ENEMY_CONFIG[enemy_type]
            # Pokud má start_time 0, začni s timerem na 0 (spawn hned)
            # Jinak začni s timerem na spawn_time (spawn po spawn_time sekundách od start_time)
            if enemy_config.get('start_time', 0) == 0:
                self.enemy_spawn_timers[enemy_type] = 0
            else:
                self.enemy_spawn_timers[enemy_type] = enemy_config['spawn_time']
        
        # Celkový čas hry (pro start_time)
        self.game_time = 0
        
        # Wave systém
        self.waves = []
        self.init_waves()
        
        # FPS tracking
        self.fps_display = 0
        self.fps_timer = 0
        
        # Hudba
        self.current_music_index = 0
        self.music_files = MUSIC_FILES
        self.current_song_name = ""
        self.song_name_display_timer = 0  # Timer pro zobrazení názvu (3 sekundy)
        self.song_name_display_duration = 3.0  # 3 sekundy
        self.current_music_player = None  # Aktuální přehrávač hudby
        
        # Spusť první píseň
        if self.music_files:
            self.play_next_song()
    
    def on_draw(self):
        """Vykreslení na obrazovku"""
        # Nastav barvu pozadí
        if self.is_day:
            arcade.set_background_color(DAY_BACKGROUND_COLOR)
        else:
            arcade.set_background_color(NIGHT_BACKGROUND_COLOR)
        
        self.clear()
        
        # Vykresli miny
        self.mine_list.draw()
        
        # Vykresli blikající červené středy min
        blink_on = (self.blink_timer % 1.0) < 0.5
        for mine in self.mine_list:
            mine.draw_core(blink_on)
        
        # Vykresli nepřátele
        self.enemy_list.draw()
        
        # Vykresli hráče
        self.player_list.draw()
        
        # Vykresli vnější kruh (perimetr)
        if not self.player.game_over:
            if self.is_day:
                outline_color = DAY_ROBOT_COLOR
            else:
                outline_color = NIGHT_ROBOT_COLOR
            arcade.draw_circle_outline(
                self.player.center_x,
                self.player.center_y,
                PERIMETER_RADIUS,
                outline_color,
                2
            )
            
            # Vykresli dělo
            angle_rad = math.radians(self.cannon_angle)
            
            cannon_start_x = self.player.center_x + PERIMETER_RADIUS * math.cos(angle_rad)
            cannon_start_y = self.player.center_y + PERIMETER_RADIUS * math.sin(angle_rad)
            
            # Vypočítej délku děla
            current_cannon_length = CANNON_LENGTH
            if not self.is_day:
                fade_progress = self.cannon_fade_timer / self.cannon_fade_time
                current_cannon_length = CANNON_LENGTH * (1 - fade_progress)
            
            cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + current_cannon_length) * math.cos(angle_rad)
            cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + current_cannon_length) * math.sin(angle_rad)
            
            if current_cannon_length > 0:
                if self.is_day:
                    cannon_color = DAY_ROBOT_COLOR
                else:
                    cannon_color = NIGHT_ROBOT_COLOR
                arcade.draw_line(
                    cannon_start_x, cannon_start_y,
                    cannon_end_x, cannon_end_y,
                    cannon_color,
                    5
                )
        
        # Vykresli laser
        if self.laser_active and not self.player.game_over:
            if self.is_day:
                laser_color = DAY_ROBOT_COLOR
            else:
                laser_color = NIGHT_ROBOT_COLOR
            arcade.draw_line(
                self.laser_start_x, self.laser_start_y,
                self.laser_end_x, self.laser_end_y,
                laser_color,
                3
            )
        
        # Vykresli shockwave animaci
        if self.shockwave_active and not self.player.game_over:
            arcade.draw_circle_outline(
                self.player.center_x,
                self.player.center_y,
                self.shockwave_radius_current,
                SHOCKWAVE_COLOR,
                3
            )
        
        # Vykresli banner podle dne/noci
        if self.is_day:
            self.draw_cannon_bar()
        else:
            self.draw_battery_bar()
        
        # Vykresli název písně
        self.draw_song_name()
        
        # Vykresli skóre
        self.vykresli_skore()
        
        # Zobraz FPS
        if not hasattr(self, 'fps_text'):
            self.fps_text = arcade.Text("", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 16)
        fps = arcade.get_fps()
        self.fps_text.text = f"FPS: {fps:.1f}"
        self.fps_text.draw()
    
    def draw_cannon_bar(self):
        """Vykreslí progress bar pro dobití děla (den)"""
        bar_x = SCREEN_WIDTH // 2
        bar_y = SCREEN_HEIGHT - 40
        bar_width = 300
        bar_height = 20
        
        charge_percentage = min(1.0, self.laser_charge_time / LASER_RECHARGE_TIME)
        
        text_color = arcade.color.WHITE
        bar_outline_color = arcade.color.WHITE
        bar_fill_color = arcade.color.WHITE
        
        text_label = "Světelné dělo:"
        text_x = bar_x - bar_width // 2 - 120
        text_y = bar_y
        
        arcade.draw_text(
            text_label,
            text_x, text_y,
            text_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        bar_left = bar_x - bar_width // 2
        bar_bottom = bar_y - bar_height // 2
        bar_top = bar_y + bar_height // 2
        
        border_width = 2
        arcade.draw_lbwh_rectangle_outline(
            bar_left,
            bar_bottom,
            bar_width,
            bar_height,
            bar_outline_color,
            border_width
        )
        
        if charge_percentage > 0:
            filled_width = bar_width * charge_percentage
            filled_right = bar_left + filled_width
            
            arcade.draw_lrbt_rectangle_filled(
                bar_left,
                filled_right,
                bar_bottom,
                bar_top,
                bar_fill_color
            )
    
    def draw_battery_bar(self):
        """Vykreslí banner baterie pro shockwave (noc)"""
        bar_x = SCREEN_WIDTH // 2
        bar_y = SCREEN_HEIGHT - 40
        bar_width = 300
        bar_height = 20
        
        charge_percentage = self.player.shockwave_charges / self.player.max_shockwave_charges
        
        text_color = arcade.color.WHITE
        bar_outline_color = arcade.color.WHITE
        bar_fill_color = arcade.color.WHITE
        
        text_label = "Baterie (vln):"
        text_x = bar_x - bar_width // 2 - 120
        text_y = bar_y
        
        arcade.draw_text(
            text_label,
            text_x, text_y,
            text_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        bar_left = bar_x - bar_width // 2
        bar_bottom = bar_y - bar_height // 2
        bar_top = bar_y + bar_height // 2
        
        border_width = 2
        arcade.draw_lbwh_rectangle_outline(
            bar_left,
            bar_bottom,
            bar_width,
            bar_height,
            bar_outline_color,
            border_width
        )
        
        if charge_percentage > 0:
            filled_width = bar_width * charge_percentage
            filled_right = bar_left + filled_width
            
            arcade.draw_lrbt_rectangle_filled(
                bar_left,
                filled_right,
                bar_bottom,
                bar_top,
                bar_fill_color
            )
    
    def draw_song_name(self):
        """Vykreslí název aktuální písně (pokud je timer aktivní)"""
        if self.song_name_display_timer > 0:
            # Umístění mezi dělo a skóre (více napravo)
            text_x = SCREEN_WIDTH - 450
            text_y = SCREEN_HEIGHT - 40
            text_color = arcade.color.CYAN
            
            # Přidej symbol hudby
            song_text = f"♪ {self.current_song_name} ♪"
            
            arcade.draw_text(
                song_text,
                text_x, text_y,
                text_color,
                16,
                anchor_x="center",
                anchor_y="center",
                bold=True
            )
    
    def vykresli_skore(self):
        """Vykreslí skóre"""
        text_x = SCREEN_WIDTH - 200
        text_y = SCREEN_HEIGHT - 40
        
        score_text = f"Skóre: {self.score}"
        text_color = NIGHT_ROBOT_COLOR
        
        arcade.draw_text(
            score_text,
            text_x, text_y,
            text_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
    
    def update_laser_position(self):
        """Vypočítá pozice laseru a kolize"""
        angle_rad = math.radians(self.cannon_angle)
        cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad)
        cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad)
        
        self.laser_start_x = cannon_end_x
        self.laser_start_y = cannon_end_y
        
        # Najdi konec laseru
        screen_end_x, screen_end_y = calculate_laser_end(
            self.laser_start_x, self.laser_start_y,
            angle_rad,
            SCREEN_WIDTH, SCREEN_HEIGHT
        )
        
        # Najdi kolizi s nepřáteli
        # Použij generický RADIUS - bude se brát z konkrétního typu
        enemy_radius = ROBOT_RADIUS  # Default
        if self.enemy_list:
            enemy_radius = self.enemy_list[0].RADIUS
        
        hit, collision_x, collision_y, hit_enemy = find_laser_collision_with_enemies(
            self.laser_start_x, self.laser_start_y,
            screen_end_x, screen_end_y,
            self.enemy_list,
            enemy_radius,
            debug=False
        )
        
        # Nastav konec laseru
        if hit and hit_enemy:
            self.laser_end_x = collision_x
            self.laser_end_y = collision_y
            # Udeř nepřítele (pokud zemře, přidej skóre)
            if hit_enemy.take_damage(1):
                self.score += 1
        else:
            self.laser_end_x = screen_end_x
            self.laser_end_y = screen_end_y
    
    def on_update(self, delta_time):
        """Update logiky hry"""
        # Update hráče
        if self.player.game_over:
            self.player.explode_timer -= delta_time
            self.player.update_game_over()
            if self.player.explode_timer <= 0:
                self.restart_game()
                return
        
        if self.player.game_over:
            return
        
        # Rotace děla
        if self.rotate_left:
            self.cannon_angle += ROTATION_SPEED
        if self.rotate_right:
            self.cannon_angle -= ROTATION_SPEED
        
        self.cannon_angle = self.cannon_angle % 360
        
        # Aktualizuj den/noc
        previous_day_state = self.is_day
        self.day_night_timer -= delta_time
        if self.day_night_timer <= 0:
            self.is_day = not self.is_day
            if self.is_day:
                self.day_night_timer = DAY_LENGTH
            else:
                self.day_night_timer = NIGHT_LENGTH
                self.laser_charge_time = 0
                # Dobij baterii na začátku noci
                self.player.shockwave_charges = SHOCKWAVE_MAX_CHARGES
        
        # Aktualizuj barvu hráče
        if previous_day_state != self.is_day or not hasattr(self, 'player_color_day'):
            self.player.update_color(self.is_day, DAY_ROBOT_COLOR, NIGHT_ROBOT_COLOR)
            self.player_color_day = self.is_day
            
            if not self.is_day:
                self.cannon_fade_timer = 0.0
        
        # Aktualizuj animaci zmizení děla
        if not self.is_day and self.cannon_fade_timer < self.cannon_fade_time:
            self.cannon_fade_timer += delta_time
            if self.cannon_fade_timer > self.cannon_fade_time:
                self.cannon_fade_timer = self.cannon_fade_time
        
        # Aktualizuj dobití
        if self.is_day:
            if self.laser_charge_time < LASER_RECHARGE_TIME:
                self.laser_charge_time += delta_time
                if self.laser_charge_time > LASER_RECHARGE_TIME:
                    self.laser_charge_time = LASER_RECHARGE_TIME
        else:
            self.laser_charge_time = 0
        
        # Odpočítávej laser
        if self.laser_active:
            self.laser_timer -= delta_time
            if self.laser_timer <= 0:
                self.laser_active = False
            else:
                # Aktualizuj začátek laseru (konec zůstává stejný)
                angle_rad = math.radians(self.cannon_angle)
                cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad)
                cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad)
                self.laser_start_x = cannon_end_x
                self.laser_start_y = cannon_end_y
        
        # Aktualizuj blikání min
        self.blink_timer += delta_time * BLINK_SPEED
        
        # Aktualizuj shockwave animaci
        if self.shockwave_active:
            self.shockwave_timer += delta_time
            # Expanze vlny
            progress = self.shockwave_timer / SHOCKWAVE_ANIMATION_DURATION
            self.shockwave_radius_current = SHOCKWAVE_RADIUS * progress
            
            # Kontrola kolize s nepřáteli
            for enemy in self.enemy_list:
                if enemy.exploding:
                    continue
                
                # Vzdálenost od hráče (mezi středy)
                dx = enemy.center_x - self.player.center_x
                dy = enemy.center_y - self.player.center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Pokud okraj vlny dosáhne okraje nepřítele, zničit ho
                # distance = vzdálenost mezi středy
                # Pro kolizi: okraj vlny >= okraj nepřítele
                if distance <= self.shockwave_radius_current + enemy.RADIUS:
                    # Udeř nepřítele (pokud zemře, přidej skóre)
                    if enemy.take_damage(1):
                        self.score += 1
            
            # Konec animace
            if self.shockwave_timer >= SHOCKWAVE_ANIMATION_DURATION:
                self.shockwave_active = False
                self.shockwave_timer = 0
        
        # Aktualizuj celkový čas hry
        self.game_time += delta_time
        
        # Spawn nepřátel - každý typ samostatně
        for enemy_type in ENEMY_TYPES.keys():
            enemy_config = ENEMY_CONFIG[enemy_type]
            
            # Kontrola, zda už můžeme spawnovat tento typ (start_time)
            if self.game_time < enemy_config['start_time']:
                continue
            
            # Kontrola maximálního počtu
            current_count = sum(1 for enemy in self.enemy_list 
                              if enemy.ENEMY_TYPE_NAME == enemy_type)
            if current_count >= enemy_config['max_count']:
                continue
            
            # Aktualizuj spawn timer
            self.enemy_spawn_timers[enemy_type] -= delta_time
            if self.enemy_spawn_timers[enemy_type] <= 0:
                self.enemy_spawn_timers[enemy_type] = enemy_config['spawn_time']
                self.spawn_enemy(enemy_type)
        
        # Update nepřátel
        self.enemy_list.update(delta_time)
        
        # Kolize nepřátel s minami
        enemies_to_remove = []
        mines_to_remove = []
        
        for enemy in self.enemy_list:
            if enemy.exploding:
                continue
            
            hit_mines = arcade.check_for_collision_with_list(enemy, self.mine_list)
            
            if hit_mines:
                # Udeř nepřítele (pokud zemře, odstraň ho)
                if enemy.take_damage(1):
                    enemies_to_remove.append(enemy)
                    self.score += 1
                
                # Odstraň miny (jen pokud nepřítel zemřel, jinak jen poškození)
                if enemy.health <= 0:
                    for mine in hit_mines:
                        if mine not in mines_to_remove:
                            mines_to_remove.append(mine)
        
        for mine in mines_to_remove:
            mine.remove_from_sprite_lists()
        
        # Kolize nepřátel s hráčem
        if not self.player.game_over:
            hit_enemies = arcade.check_for_collision_with_list(self.player, self.enemy_list)
            
            # Kolize s kanonem
            angle_rad = math.radians(self.cannon_angle)
            cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad)
            cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad)
            cannon_start_x = self.player.center_x + PERIMETER_RADIUS * math.cos(angle_rad)
            cannon_start_y = self.player.center_y + PERIMETER_RADIUS * math.sin(angle_rad)
            
            cannon_length = math.sqrt((cannon_end_x - cannon_start_x)**2 + (cannon_end_y - cannon_start_y)**2)
            
            for enemy in self.enemy_list:
                if enemy.exploding:
                    continue
                
                dx = cannon_end_x - cannon_start_x
                dy = cannon_end_y - cannon_start_y
                
                px = enemy.center_x - cannon_start_x
                py = enemy.center_y - cannon_start_y
                
                if cannon_length > 0:
                    t = max(0, min(1, (px * dx + py * dy) / (cannon_length ** 2)))
                    
                    closest_x = cannon_start_x + t * dx
                    closest_y = cannon_start_y + t * dy
                    
                    dist = math.sqrt((enemy.center_x - closest_x)**2 + (enemy.center_y - closest_y)**2)
                    
                    if dist < (enemy.RADIUS + 5):
                        if enemy not in hit_enemies:
                            hit_enemies.append(enemy)
            
            if hit_enemies:
                self.player.start_game_over()
        
        # Aktualizuj hudbu
        self.update_music(delta_time)
        
        # Aktualizuj wave systém
        self.update_waves(delta_time)
    
    def spawn_enemy(self, enemy_type=None):
        """Vytvoř nového nepřítele
        
        Args:
            enemy_type: Typ nepřítele ('crab', 'star', ...). Pokud None, vybere náhodně.
        """
        # Pokud není zadán typ, vyber náhodně
        if enemy_type is None:
            enemy_type = random.choice(list(ENEMY_TYPES.keys()))
        
        EnemyClass = ENEMY_TYPES[enemy_type]
        
        # Vyber náhodný okraj
        edge = random.randint(0, 3)
        margin = EnemyClass.RADIUS + 30
        
        if edge == 0:  # Nahoře
            x = random.randint(margin, SCREEN_WIDTH - margin)
            y = SCREEN_HEIGHT - margin
        elif edge == 1:  # Vpravo
            x = SCREEN_WIDTH - margin
            y = random.randint(margin, SCREEN_HEIGHT - margin)
        elif edge == 2:  # Dole
            x = random.randint(margin, SCREEN_WIDTH - margin)
            y = margin
        else:  # Vlevo
            x = margin
            y = random.randint(margin, SCREEN_HEIGHT - margin)
        
        # Střed obrazovky jako cíl
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # Vytvoř enemy - pro direct pohyb předej cílovou pozici
        if EnemyClass.MOVEMENT_TYPE == "direct":
            enemy = EnemyClass(x, y, side_direction=None, target_x=center_x, target_y=center_y)
        else:
            enemy = EnemyClass(x, y, side_direction=None)
        
        # Pokud je to torpédo, nastav reference na miny a hráče
        if enemy.MOVEMENT_TYPE == "seeking":
            enemy.mine_list = self.mine_list
            enemy.player = self.player
        
        # Pokud je to Prudic (player_seeking), nastav reference na hráče
        if enemy.MOVEMENT_TYPE == "player_seeking":
            enemy.player = self.player
        
        # Pokud je to postranní pohyb (krab), nastav optimální směr
        if enemy.MOVEMENT_TYPE == "sideway":
            dx = center_x - x
            dy = center_y - y
            angle_to_center = math.degrees(math.atan2(dy, dx))
            
            crab_angle = enemy.angle
            
            movement_left = abs(crab_angle + (-90))
            movement_right = abs(crab_angle + 90)
            
            angle_to_center_norm = angle_to_center % 360
            if angle_to_center_norm < 0:
                angle_to_center_norm += 360
            
            movement_left_norm = movement_left % 360
            movement_right_norm = movement_right % 360
            
            diff_left = min(abs(movement_left_norm - angle_to_center_norm), 
                           360 - abs(movement_left_norm - angle_to_center_norm))
            diff_right = min(abs(movement_right_norm - angle_to_center_norm), 
                            360 - abs(movement_right_norm - angle_to_center_norm))
            
            if diff_left < diff_right:
                enemy.side_direction = -1
            else:
                enemy.side_direction = 1
            
            # Přepočítej pohyb
            if enemy.side_direction == -1:
                movement_angle_degrees = enemy.angle + (-90)
            else:
                movement_angle_degrees = enemy.angle + 90
            movement_angle_rad = math.radians(abs(movement_angle_degrees))
            enemy.change_x = math.cos(movement_angle_rad) * enemy.SPEED
            enemy.change_y = math.sin(movement_angle_rad) * enemy.SPEED
        
        self.enemy_list.append(enemy)
    
    def activate_shockwave(self):
        """Aktivuje shockwave vlnu (pouze v noci a pokud má hráč náboje)"""
        if not self.is_day and self.player.shockwave_charges > 0 and not self.shockwave_active:
            self.shockwave_active = True
            self.shockwave_timer = 0
            self.shockwave_radius_current = 0
            self.player.shockwave_charges -= 1
    
    def restart_game(self):
        """Restart hry"""
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = SCREEN_HEIGHT // 2
        self.player.game_over = False
        self.player.explode_timer = 0
        self.player.shockwave_charges = SHOCKWAVE_MAX_CHARGES
        
        self.score = 0
        
        self.mine_list.clear()
        self.enemy_list.clear()
        
        # Reset spawn timerů pro každého nepřítele
        for enemy_type in ENEMY_TYPES.keys():
            enemy_config = ENEMY_CONFIG[enemy_type]
            # Pokud má start_time 0, začni s timerem na 0 (spawn hned)
            if enemy_config.get('start_time', 0) == 0:
                self.enemy_spawn_timers[enemy_type] = 0
            else:
                self.enemy_spawn_timers[enemy_type] = enemy_config['spawn_time']
        
        # Reset herního času
        self.game_time = 0
        
        # Reset wave systému
        for wave in self.waves:
            wave['last_trigger'] = -999
        
        self.laser_active = False
        self.laser_charge_time = LASER_RECHARGE_TIME if START_WITH_DAY else 0
        
        self.is_day = START_WITH_DAY
        if self.is_day:
            self.day_night_timer = DAY_LENGTH
        else:
            self.day_night_timer = NIGHT_LENGTH
        
        # Reset animace děla
        self.cannon_fade_timer = 0.0 if START_WITH_DAY else self.cannon_fade_time
        
        # Aktualizuj barvu hráče
        self.player.update_color(self.is_day, DAY_ROBOT_COLOR, NIGHT_ROBOT_COLOR)
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Pohyb myši"""
        if not self.player.game_over:
            self.player.center_x = x
            self.player.center_y = y
    
    def init_waves(self):
        """Inicializuj wave systém z konfigurace"""
        for wave_config in WAVES_CONFIG:
            wave = {
                'name': wave_config['name'],
                'trigger_time': wave_config['trigger_time'],
                'repeat_interval': wave_config.get('repeat_interval', 0),
                'last_trigger': -999,  # Čas posledního spuštění
                'enemies': wave_config['enemies']
            }
            self.waves.append(wave)
        
        if self.waves:
            print(f"Načteno {len(self.waves)} vln nepřátel")
    
    def update_waves(self, delta_time):
        """Aktualizuj wave systém - kontrola časů a spouštění vln"""
        for wave in self.waves:
            # Kontrola, zda je čas spustit vlnu
            time_since_last = self.game_time - wave['last_trigger']
            
            # První spuštění
            if wave['last_trigger'] < 0 and self.game_time >= wave['trigger_time']:
                self.spawn_wave(wave)
                wave['last_trigger'] = self.game_time
            # Opakování
            elif wave['repeat_interval'] > 0 and time_since_last >= wave['repeat_interval']:
                self.spawn_wave(wave)
                wave['last_trigger'] = self.game_time
    
    def spawn_wave(self, wave):
        """Spusť vlnu - spawn všech nepřátel z vlny"""
        print(f"🌊 WAVE: {wave['name']}")
        
        for enemy_config in wave['enemies']:
            enemy_type = enemy_config['type']
            count = enemy_config['count']
            pattern = enemy_config['spawn_pattern']
            
            # Spawn podle pattern
            if pattern == "circle":
                self.spawn_wave_circle(enemy_type, count)
            elif pattern == "left":
                self.spawn_wave_left(enemy_type, count)
            elif pattern == "right":
                self.spawn_wave_right(enemy_type, count)
    
    def spawn_wave_circle(self, enemy_type, count):
        """Spawn nepřátel v kruhu kolem obrazovky"""
        EnemyClass = ENEMY_TYPES[enemy_type]
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        for i in range(count):
            # Rozděl kruhem rovnoměrně
            angle = (360 / count) * i
            angle_rad = math.radians(angle)
            
            # Vyber vzdálenost od středu (na okraji obrazovky)
            # Použij větší z rozměrů + margin
            distance = max(SCREEN_WIDTH, SCREEN_HEIGHT) // 2 + 50
            
            x = center_x + distance * math.cos(angle_rad)
            y = center_y + distance * math.sin(angle_rad)
            
            # Vytvoř nepřítele směřujícího ke středu
            if EnemyClass.MOVEMENT_TYPE == "direct":
                enemy = EnemyClass(x, y, side_direction=None, target_x=center_x, target_y=center_y)
            else:
                enemy = EnemyClass(x, y, side_direction=None)
            
            # Nastavení pro torpédo
            if enemy.MOVEMENT_TYPE == "seeking":
                enemy.mine_list = self.mine_list
                enemy.player = self.player
            
            # Nastavení pro Prudic (player_seeking)
            if enemy.MOVEMENT_TYPE == "player_seeking":
                enemy.player = self.player
            
            # Pro krab/sideway nastav směr směrem ke středu
            if enemy.MOVEMENT_TYPE == "sideway":
                dx = center_x - x
                dy = center_y - y
                angle_to_center = math.degrees(math.atan2(dy, dx))
                
                crab_angle = enemy.angle
                movement_left = abs(crab_angle + (-90))
                movement_right = abs(crab_angle + 90)
                
                angle_to_center_norm = angle_to_center % 360
                if angle_to_center_norm < 0:
                    angle_to_center_norm += 360
                
                movement_left_norm = movement_left % 360
                movement_right_norm = movement_right % 360
                
                diff_left = min(abs(movement_left_norm - angle_to_center_norm), 
                               360 - abs(movement_left_norm - angle_to_center_norm))
                diff_right = min(abs(movement_right_norm - angle_to_center_norm), 
                                360 - abs(movement_right_norm - angle_to_center_norm))
                
                if diff_left < diff_right:
                    enemy.side_direction = -1
                else:
                    enemy.side_direction = 1
                
                if enemy.side_direction == -1:
                    movement_angle_degrees = enemy.angle + (-90)
                else:
                    movement_angle_degrees = enemy.angle + 90
                movement_angle_rad = math.radians(abs(movement_angle_degrees))
                enemy.change_x = math.cos(movement_angle_rad) * enemy.SPEED
                enemy.change_y = math.sin(movement_angle_rad) * enemy.SPEED
            
            self.enemy_list.append(enemy)
    
    def spawn_wave_left(self, enemy_type, count):
        """Spawn nepřátel na levé straně směřujících doprava"""
        EnemyClass = ENEMY_TYPES[enemy_type]
        margin = EnemyClass.RADIUS + 30
        
        # Cíl napravo
        target_x = SCREEN_WIDTH + 100
        
        for i in range(count):
            # Rozděl rovnoměrně po levé straně
            y = (SCREEN_HEIGHT / (count + 1)) * (i + 1)
            x = -margin
            
            target_y = y  # Stejná výška
            
            # Vytvoř nepřítele
            if EnemyClass.MOVEMENT_TYPE == "direct":
                enemy = EnemyClass(x, y, side_direction=None, target_x=target_x, target_y=target_y)
            else:
                enemy = EnemyClass(x, y, side_direction=None)
                # Pro sideway nastav směr doprava
                enemy.change_x = enemy.SPEED
                enemy.change_y = 0
            
            # Nastavení pro torpédo
            if enemy.MOVEMENT_TYPE == "seeking":
                enemy.mine_list = self.mine_list
                enemy.player = self.player
            
            # Nastavení pro Prudic (player_seeking)
            if enemy.MOVEMENT_TYPE == "player_seeking":
                enemy.player = self.player
            
            self.enemy_list.append(enemy)
    
    def spawn_wave_right(self, enemy_type, count):
        """Spawn nepřátel na pravé straně směřujících doleva"""
        EnemyClass = ENEMY_TYPES[enemy_type]
        margin = EnemyClass.RADIUS + 30
        
        # Cíl nalevo
        target_x = -100
        
        for i in range(count):
            # Rozděl rovnoměrně po pravé straně
            y = (SCREEN_HEIGHT / (count + 1)) * (i + 1)
            x = SCREEN_WIDTH + margin
            
            target_y = y  # Stejná výška
            
            # Vytvoř nepřítele
            if EnemyClass.MOVEMENT_TYPE == "direct":
                enemy = EnemyClass(x, y, side_direction=None, target_x=target_x, target_y=target_y)
            else:
                enemy = EnemyClass(x, y, side_direction=None)
                # Pro sideway nastav směr doleva
                enemy.change_x = -enemy.SPEED
                enemy.change_y = 0
            
            # Nastavení pro torpédo
            if enemy.MOVEMENT_TYPE == "seeking":
                enemy.mine_list = self.mine_list
                enemy.player = self.player
            
            # Nastavení pro Prudic (player_seeking)
            if enemy.MOVEMENT_TYPE == "player_seeking":
                enemy.player = self.player
            
            self.enemy_list.append(enemy)
    
    def play_next_song(self):
        """Přehraj další píseň v seznamu (cyklicky)"""
        if not self.music_files:
            return
        
        # Zastav předchozí píseň, pokud hraje
        if self.current_music_player:
            # V Arcade používáme delete() pro zastavení a uvolnění playeru
            self.current_music_player.delete()
            self.current_music_player = None
        
        # Načti aktuální píseň
        current_file = self.music_files[self.current_music_index]
        
        # Extrahuj název (bez .mp3)
        self.current_song_name = os.path.basename(current_file).replace('.mp3', '')
        
        # Reset timeru pro zobrazení názvu
        self.song_name_display_timer = self.song_name_display_duration
        
        # Přehraj píseň pomocí Arcade
        # streaming=True pro velké hudební soubory (nenahrává celý soubor do paměti)
        music_sound = arcade.load_sound(current_file, streaming=True)
        self.current_music_player = music_sound.play(volume=0.5)
        
        print(f"♪ Přehrávám: {self.current_song_name}")
        
        # Přejdi na další píseň (cyklicky)
        self.current_music_index = (self.current_music_index + 1) % len(self.music_files)
    
    def update_music(self, delta_time):
        """Aktualizuj hudbu - kontrola konce písně"""
        # Kontrola, zda píseň skončila
        if self.current_music_player:
            # get_stream_position() vrací pozici přehrávání
            # Pokud je None nebo player už neexistuje, píseň skončila
            if not self.current_music_player.playing:
                # Píseň skončila, přehraj další
                self.play_next_song()
        elif self.music_files:
            # Žádný player, ale máme soubory -> spusť první
            self.play_next_song()
        
        # Aktualizuj timer pro zobrazení názvu
        if self.song_name_display_timer > 0:
            self.song_name_display_timer -= delta_time
    
    def can_fire_laser(self):
        """Zkontroluj, zda lze střílet"""
        return self.is_day and self.laser_charge_time >= LASER_RECHARGE_TIME
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Kliknutí myši"""
        if self.player.game_over:
            return
        
        if button == arcade.MOUSE_BUTTON_LEFT:
            # V noci aktivuj shockwave místo laseru
            if not self.is_day:
                self.activate_shockwave()
            else:
                # Ve dne střílej laserem
                if not self.can_fire_laser():
                    return
                
                self.laser_active = True
                self.laser_timer = LASER_DURATION
                self.laser_charge_time = 0
                self.debug_shot_count += 1
                self.update_laser_position()
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            if len(self.mine_list) < MAX_MINES:
                mine = Mine(self.player.center_x, self.player.center_y, MINE_RADIUS, MINE_CORE_RADIUS)
                self.mine_list.append(mine)
    
    def on_key_press(self, key, modifiers):
        """Stisknutí klávesy"""
        if self.player.game_over:
            return
        
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.rotate_left = True
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.rotate_right = True
    
    def on_key_release(self, key, modifiers):
        """Uvolnění klávesy"""
        if self.player.game_over:
            return
        
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.rotate_left = False
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.rotate_right = False


def main():
    game = Game()
    arcade.run()


if __name__ == "__main__":
    main()

