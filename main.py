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
import time
from typing import Tuple, Optional

# Import modulů
from player import Player, Mine, GuidedMine, BonusBomba, BonusMiny, BonusShockwave, BonusExtraZivot, BonusKanon, BonusNavadeneMiny
from menu import GameMenu
from infrastruktura import find_laser_collision_with_enemies, calculate_laser_end
from enemies.base_enemy import BaseEnemy
from enemies import Crab, Star, Torpedo, Prudic, Ufo

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

LIGHT_BOMB_STARTING = CONFIG['light_bomb']['starting']  # True/False - má hráč na začátku bombu?
LIGHT_BOMB_ANIMATION_DURATION = CONFIG['light_bomb']['animation_duration']
LIGHT_BOMB_COLOR = tuple(CONFIG['light_bomb']['wave_color'])

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
    'ufo': Ufo,
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
        # Nastav animation_path z configu (pro GIF nebo PNG)
        if 'animation_path' in enemy_cfg:
            animation_path = enemy_cfg['animation_path']
            # Pokud má třída GIF_PATH, použij ho
            if hasattr(EnemyClass, 'GIF_PATH'):
                EnemyClass.GIF_PATH = animation_path
            # Pokud má třída SPRITE_IMAGE_PATH (Prudic), použij ho
            if hasattr(EnemyClass, 'SPRITE_IMAGE_PATH'):
                EnemyClass.SPRITE_IMAGE_PATH = animation_path
        else:
            # Varování, pokud není animation_path v configu
            print(f"VAROVANI: {enemy_type_name} nema animation_path v game_config.yaml")

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
        # Druhý laser (pro druhé dělo)
        self.laser_start_x_2 = 0
        self.laser_start_y_2 = 0
        self.laser_end_x_2 = 0
        self.laser_end_y_2 = 0
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
        self.shockwave_hit_enemies = set()  # Nepřátelé zasažení touto vlnou (aby každý dostal damage jen jednou)
        
        # Světelná atomová bomba
        self.light_bomb_count = 1 if LIGHT_BOMB_STARTING else 0
        self.light_bomb_active = False
        self.light_bomb_timer = 0
        self.light_bomb_radius_current = 0
        
        # Respawn bomba (menší světelná bomba při použití extra života)
        self.respawn_bomb_active = False
        self.respawn_bomb_timer = 0
        self.respawn_bomb_radius_current = 0
        self.respawn_bomb_max_radius = min(SCREEN_WIDTH, SCREEN_HEIGHT) // 2  # Půlka obrazovky
        
        # Nepřátelé
        self.enemy_list = arcade.SpriteList(use_spatial_hash=False)
        
        # Bonusy (padají z UFO)
        self.bonus_list = arcade.SpriteList(use_spatial_hash=False)
        self.collected_bonus_types = set()  # Typy bonusů, které hráč už sebral (nemohou znovu padnout)
        if LIGHT_BOMB_STARTING:
            self.collected_bonus_types.add("bomba")  # Má bombu od začátku
        self.current_max_mines = MAX_MINES  # Aktuální max počet min (může se zvýšit bonusem)
        self.current_shockwave_radius = SHOCKWAVE_RADIUS  # Aktuální poloměr shockwave (může se zvýšit bonusem)
        self.extra_lives = 0  # Extra životy (bonus)
        self.has_second_cannon = False  # Druhé dělo (bonus)
        self.has_guided_mines = False  # Naváděné miny (bonus)
        
        # Spawn timery pro každého nepřítele samostatně
        self.enemy_spawn_timers = {}
        for enemy_type in ENEMY_TYPES.keys():
            # Timer vždy začíná na 0 - první spawn nastane hned jakmile game_time >= start_time
            self.enemy_spawn_timers[enemy_type] = 0
        
        # Celkový čas hry (pro start_time)
        self.game_time = 0
        
        # Wave systém
        self.waves = []
        self.init_waves()
        
        # FPS tracking
        self.fps_display = 0
        self.fps_timer = 0
        
        # Menu systém
        self.menu = GameMenu(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Hudba
        self.music_files = MUSIC_FILES
        # Vyber náhodnou píseň pro start, pak pokračuj v abecedním pořadí
        self.current_music_index = random.randint(0, len(self.music_files) - 1) if self.music_files else 0
        self.current_song_name = ""
        self.song_name_display_timer = 0  # Timer pro zobrazení názvu (3 sekundy)
        self.song_name_display_duration = 3.0  # 3 sekundy
        self.current_music_player = None  # Aktuální přehrávač hudby
        
        # Ovládání hudby - detekce dvojitého stisku E
        self.last_e_press_time = 0
        self.double_press_threshold = 0.4  # 400ms pro dvojité stisknutí
        
        # Spusť první píseň (náhodně vybranou)
        if self.music_files:
            self.play_song_at_index(self.current_music_index)
    
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
        
        # Vykresli bonusy
        self.bonus_list.draw()
        
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
                
                # Vykresli druhé dělo (opačný směr) pokud má bonus
                if self.has_second_cannon:
                    angle_rad_2 = math.radians(self.cannon_angle + 180)
                    cannon_start_x_2 = self.player.center_x + PERIMETER_RADIUS * math.cos(angle_rad_2)
                    cannon_start_y_2 = self.player.center_y + PERIMETER_RADIUS * math.sin(angle_rad_2)
                    cannon_end_x_2 = self.player.center_x + (PERIMETER_RADIUS + current_cannon_length) * math.cos(angle_rad_2)
                    cannon_end_y_2 = self.player.center_y + (PERIMETER_RADIUS + current_cannon_length) * math.sin(angle_rad_2)
                    arcade.draw_line(
                        cannon_start_x_2, cannon_start_y_2,
                        cannon_end_x_2, cannon_end_y_2,
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
            # Druhý laser (pokud má druhé dělo)
            if self.has_second_cannon:
                arcade.draw_line(
                    self.laser_start_x_2, self.laser_start_y_2,
                    self.laser_end_x_2, self.laser_end_y_2,
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
                5  # Tloušťka kruhu (mírně zvětšeno)
            )
        
        # Vykresli light bomb animaci (velká vlna ze středu)
        if self.light_bomb_active and not self.player.game_over:
            arcade.draw_circle_outline(
                self.player.center_x,
                self.player.center_y,
                self.light_bomb_radius_current,
                LIGHT_BOMB_COLOR,
                20  # Tloušťka kruhu - více hrozivé
            )
        
        # Vykresli respawn bomb animaci (menší vlna při použití extra života)
        if self.respawn_bomb_active and not self.player.game_over:
            arcade.draw_circle_outline(
                self.player.center_x,
                self.player.center_y,
                self.respawn_bomb_radius_current,
                (100, 255, 100),  # Zelená barva pro respawn
                15  # Tloušťka kruhu
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
        
        # Vykresli počet světelných bomb (nahoře vlevo)
        self.draw_light_bomb_count()
        
        # Vykresli stav bonusů (nahoře vlevo pod světelnou bombou)
        self.draw_bonus_status()
        
        # Zobraz "F1 menu" vlevo nahoře
        arcade.draw_text(
            "F1 menu",
            10,
            SCREEN_HEIGHT - 30,
            (150, 150, 150),
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        # Zobraz FPS vpravo pod časem
        fps = arcade.get_fps()
        fps_text_x = SCREEN_WIDTH - 200
        fps_text_y = SCREEN_HEIGHT - 90  # Pod časem (čas je na -65)
        arcade.draw_text(
            f"FPS: {fps:.1f}",
            fps_text_x,
            fps_text_y,
            (100, 100, 100),
            14,
            anchor_x="left",
            anchor_y="center"
        )
        
        # Vykresli menu (pokud je viditelné)
        self.menu.draw()
    
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
        """Vykreslí skóre a herní čas"""
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
        
        # Herní čas (sekundy,milisekundy)
        seconds = int(self.game_time)
        milliseconds = int((self.game_time - seconds) * 1000)
        time_text = f"Čas: {seconds},{milliseconds:03d}s"
        
        arcade.draw_text(
            time_text,
            text_x, text_y - 25,
            text_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
    
    def draw_light_bomb_count(self):
        """Vykreslí stav světelné bomby nahoře vlevo"""
        text_x = 10
        text_y = SCREEN_HEIGHT - 70  # Pod FPS
        
        # Zobraz ano/ne podle toho, jestli má bombu
        has_bomb = "bomba" in self.collected_bonus_types
        bomb_status = "ano" if has_bomb else "ne"
        bomb_text = f"Světelná bomba: {bomb_status}"
        
        # Barva podle dostupnosti (zlatá pokud máš, šedá pokud ne)
        if has_bomb and self.light_bomb_count > 0:
            text_color = LIGHT_BOMB_COLOR
        else:
            text_color = (100, 100, 100)
        
        arcade.draw_text(
            bomb_text,
            text_x, text_y,
            text_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
    
    def draw_bonus_status(self):
        """Vykreslí stav všech bonusů nahoře vlevo"""
        text_x = 10
        base_y = SCREEN_HEIGHT - 100  # Pod světelnou bombou
        line_height = 25
        
        # Barvy
        color_active = (100, 255, 100)  # Zelená pro aktivní (ano)
        color_inactive = (100, 100, 100)  # Šedá pro neaktivní (ne)
        
        # 1. Extra život (ano/ne)
        has_extra_life = "extra_zivot" in self.collected_bonus_types
        lives_status = "ano" if has_extra_life else "ne"
        lives_color = color_active if has_extra_life else color_inactive
        arcade.draw_text(
            f"Extra život: {lives_status}",
            text_x, base_y,
            lives_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        # 2. Extra miny (zdvojnásobení max počtu)
        has_miny_bonus = "miny" in self.collected_bonus_types
        miny_status = "ano" if has_miny_bonus else "ne"
        miny_color = color_active if has_miny_bonus else color_inactive
        arcade.draw_text(
            f"Extra miny: {miny_status}",
            text_x, base_y - line_height,
            miny_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        # 3. Shockwave bonus radius
        has_shockwave_bonus = "shockwave" in self.collected_bonus_types
        shockwave_status = "ano" if has_shockwave_bonus else "ne"
        shockwave_color = color_active if has_shockwave_bonus else color_inactive
        arcade.draw_text(
            f"Shockwave bonus: {shockwave_status}",
            text_x, base_y - line_height * 2,
            shockwave_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        # 4. Druhé dělo
        has_cannon_bonus = "kanon" in self.collected_bonus_types
        cannon_status = "ano" if has_cannon_bonus else "ne"
        cannon_color = color_active if has_cannon_bonus else color_inactive
        arcade.draw_text(
            f"Druhé dělo: {cannon_status}",
            text_x, base_y - line_height * 3,
            cannon_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        # 5. Naváděné miny
        has_guided_mines = "navadene_miny" in self.collected_bonus_types
        guided_status = "ano" if has_guided_mines else "ne"
        guided_color = color_active if has_guided_mines else color_inactive
        arcade.draw_text(
            f"Naváděné miny: {guided_status}",
            text_x, base_y - line_height * 4,
            guided_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
    
    def update_laser_position(self, do_damage=True):
        """Vypočítá pozice laseru a kolize
        
        Args:
            do_damage: Pokud True, udělí damage nepřátelům při kolizi
        """
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
            # Udeř nepřítele (pokud zemře, přidej skóre a bonus) - pouze pokud do_damage=True
            if do_damage:
                if hit_enemy.take_damage(1):
                    self.score += 1
                    self.spawn_bonus_from_enemy(hit_enemy)
        else:
            self.laser_end_x = screen_end_x
            self.laser_end_y = screen_end_y
        
        # Druhý laser (pokud má druhé dělo)
        if self.has_second_cannon:
            angle_rad_2 = math.radians(self.cannon_angle + 180)
            cannon_end_x_2 = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad_2)
            cannon_end_y_2 = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad_2)
            
            self.laser_start_x_2 = cannon_end_x_2
            self.laser_start_y_2 = cannon_end_y_2
            
            # Najdi konec druhého laseru
            screen_end_x_2, screen_end_y_2 = calculate_laser_end(
                self.laser_start_x_2, self.laser_start_y_2,
                angle_rad_2,
                SCREEN_WIDTH, SCREEN_HEIGHT
            )
            
            # Najdi kolizi s nepřáteli (druhý laser)
            hit_2, collision_x_2, collision_y_2, hit_enemy_2 = find_laser_collision_with_enemies(
                self.laser_start_x_2, self.laser_start_y_2,
                screen_end_x_2, screen_end_y_2,
                self.enemy_list,
                enemy_radius,
                debug=False
            )
            
            # Nastav konec druhého laseru
            if hit_2 and hit_enemy_2:
                self.laser_end_x_2 = collision_x_2
                self.laser_end_y_2 = collision_y_2
                # Udeř nepřítele (pokud zemře, přidej skóre a bonus) - pouze pokud do_damage=True
                if do_damage:
                    if hit_enemy_2.take_damage(1):
                        self.score += 1
                        self.spawn_bonus_from_enemy(hit_enemy_2)
            else:
                self.laser_end_x_2 = screen_end_x_2
                self.laser_end_y_2 = screen_end_y_2
    
    def on_update(self, delta_time):
        """Update logiky hry"""
        # Pokud je menu otevřené, zastavíme game loop
        if self.menu.visible:
            # Pouze aktualizuj hudbu (aby hrála i v menu)
            self.update_music(delta_time)
            return
        
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
                # Přepočítej celý laser (start i konec) - sleduje aktuální úhel děla
                # do_damage=False - damage se uděluje pouze při výstřelu, ne každý frame
                self.update_laser_position(do_damage=False)
        
        # Aktualizuj naváděné miny (pokud existují)
        for mine in self.mine_list:
            if isinstance(mine, GuidedMine):
                mine.update(delta_time)
        
        # Aktualizuj blikání min
        self.blink_timer += delta_time * BLINK_SPEED
        
        # Aktualizuj shockwave animaci
        if self.shockwave_active:
            self.shockwave_timer += delta_time
            # Expanze vlny (používá current_shockwave_radius, který může být zvětšen bonusem)
            progress = self.shockwave_timer / SHOCKWAVE_ANIMATION_DURATION
            self.shockwave_radius_current = self.current_shockwave_radius * progress
            
            # Kontrola kolize s nepřáteli
            for enemy in self.enemy_list:
                if enemy.exploding:
                    continue
                
                # Přeskoč nepřátele, kteří už byli zasaženi touto vlnou
                if id(enemy) in self.shockwave_hit_enemies:
                    continue
                
                # Vzdálenost od hráče (mezi středy)
                dx = enemy.center_x - self.player.center_x
                dy = enemy.center_y - self.player.center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Použij VIZUÁLNÍ poloměr nepřítele (RADIUS * SCALE_MULTIPLIER)
                visual_radius = enemy.RADIUS * getattr(enemy, 'SCALE_MULTIPLIER', 1)
                
                # Pokud okraj vlny dosáhne okraje nepřítele, zničit ho
                # distance = vzdálenost mezi středy
                # Pro kolizi: okraj vlny >= okraj nepřítele
                if distance <= self.shockwave_radius_current + visual_radius:
                    # Označ nepřítele jako zasaženého touto vlnou
                    self.shockwave_hit_enemies.add(id(enemy))
                    # Udeř nepřítele (pokud zemře, přidej skóre a bonus)
                    if enemy.take_damage(1):
                        self.score += 1
                        self.spawn_bonus_from_enemy(enemy)
            
            # Konec animace
            if self.shockwave_timer >= SHOCKWAVE_ANIMATION_DURATION:
                self.shockwave_active = False
                self.shockwave_timer = 0
                self.shockwave_hit_enemies.clear()  # Reset pro další vlnu
        
        # Aktualizuj light bomb animaci (světelná atomová bomba)
        if self.light_bomb_active:
            self.light_bomb_timer += delta_time
            # Expanze vlny přes celou obrazovku
            progress = self.light_bomb_timer / LIGHT_BOMB_ANIMATION_DURATION
            # Maximální poloměr = diagonála obrazovky (aby dosáhla do všech rohů)
            max_radius = math.sqrt(SCREEN_WIDTH ** 2 + SCREEN_HEIGHT ** 2)
            self.light_bomb_radius_current = max_radius * progress
            
            # Zniči všechny nepřátele, které vlna zasáhne
            for enemy in self.enemy_list:
                if enemy.exploding:
                    continue
                
                # Vzdálenost od hráče (mezi středy)
                dx = enemy.center_x - self.player.center_x
                dy = enemy.center_y - self.player.center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Použij VIZUÁLNÍ poloměr nepřítele (RADIUS * SCALE_MULTIPLIER)
                visual_radius = enemy.RADIUS * getattr(enemy, 'SCALE_MULTIPLIER', 1)
                
                # Pokud okraj vlny dosáhne okraje nepřítele, zničit ho
                if distance <= self.light_bomb_radius_current + visual_radius:
                    # Instakill - udělí damage = max_health
                    damage = getattr(enemy, 'MAX_HEALTH', 1)
                    if enemy.take_damage(damage):
                        self.score += 1
                        self.spawn_bonus_from_enemy(enemy)
            
            # Konec animace
            if self.light_bomb_timer >= LIGHT_BOMB_ANIMATION_DURATION:
                self.light_bomb_active = False
                self.light_bomb_timer = 0
        
        # Aktualizuj respawn bomb animaci (menší bomba při použití extra života)
        if self.respawn_bomb_active:
            self.respawn_bomb_timer += delta_time
            # Expanze vlny (půlka obrazovky)
            progress = self.respawn_bomb_timer / LIGHT_BOMB_ANIMATION_DURATION
            self.respawn_bomb_radius_current = self.respawn_bomb_max_radius * progress
            
            # Zniči nepřátele v dosahu
            for enemy in self.enemy_list:
                if enemy.exploding:
                    continue
                
                # Vzdálenost od hráče (mezi středy)
                dx = enemy.center_x - self.player.center_x
                dy = enemy.center_y - self.player.center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Použij VIZUÁLNÍ poloměr nepřítele
                visual_radius = enemy.RADIUS * getattr(enemy, 'SCALE_MULTIPLIER', 1)
                
                # Pokud okraj vlny dosáhne okraje nepřítele, zničit ho
                if distance <= self.respawn_bomb_radius_current + visual_radius:
                    damage = getattr(enemy, 'MAX_HEALTH', 1)
                    if enemy.take_damage(damage):
                        self.score += 1
            
            # Konec animace
            if self.respawn_bomb_timer >= LIGHT_BOMB_ANIMATION_DURATION:
                self.respawn_bomb_active = False
                self.respawn_bomb_timer = 0
        
        # Aktualizuj celkový čas hry
        self.game_time += delta_time
        
        # Spawn nepřátel - každý typ samostatně
        for enemy_type in ENEMY_TYPES.keys():
            enemy_config = ENEMY_CONFIG[enemy_type]
            
            # Kontrola, zda už můžeme spawnovat tento typ (start_time)
            if self.game_time < enemy_config['start_time']:
                continue
            
            # UFO neletí pokud má hráč všechny bonusy
            if enemy_type == "ufo" and self.has_all_bonuses():
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
        
        # Update bonusů
        self.bonus_list.update(delta_time)
        
        # Kolize hráče s bonusy
        if not self.player.game_over:
            collected_bonuses = arcade.check_for_collision_with_list(self.player, self.bonus_list)
            for bonus in collected_bonuses:
                bonus_type = getattr(bonus, 'BONUS_TYPE', 'unknown')
                
                if bonus_type == "bomba":
                    # Přidej náboj do světelné bomby
                    self.light_bomb_count += 1
                    self.collected_bonus_types.add("bomba")  # Označ jako sebraný
                    print(f"💣 Bonus sebrán! Světelná bomba aktivována!")
                
                elif bonus_type == "miny":
                    # Zdvojnásob maximální počet min
                    self.current_max_mines *= 2
                    self.collected_bonus_types.add("miny")  # Označ jako sebraný
                    print(f"💣 Bonus sebrán! Max min: {self.current_max_mines}")
                
                elif bonus_type == "shockwave":
                    # Zdvojnásob poloměr shockwave
                    self.current_shockwave_radius *= 2
                    self.collected_bonus_types.add("shockwave")  # Označ jako sebraný
                    print(f"💣 Bonus sebrán! Shockwave radius: {self.current_shockwave_radius}")
                
                elif bonus_type == "extra_zivot":
                    # Přidej extra život
                    self.extra_lives += 1
                    self.collected_bonus_types.add("extra_zivot")  # Označ jako sebraný
                    print(f"💚 Bonus sebrán! Extra život aktivován!")
                
                elif bonus_type == "kanon":
                    # Aktivuj druhé dělo
                    self.has_second_cannon = True
                    self.collected_bonus_types.add("kanon")  # Označ jako sebraný
                    print(f"🔫 Bonus sebrán! Druhé dělo aktivováno!")
                
                elif bonus_type == "navadene_miny":
                    # Aktivuj naváděné miny
                    self.has_guided_mines = True
                    self.collected_bonus_types.add("navadene_miny")  # Označ jako sebraný
                    print(f"🎯 Bonus sebrán! Naváděné miny aktivovány!")
                
                bonus.remove_from_sprite_lists()
        
        # Kolize nepřátel s minami
        enemies_to_remove = []
        mines_to_remove = []
        
        for enemy in self.enemy_list:
            if enemy.exploding:
                continue
            
            hit_mines = arcade.check_for_collision_with_list(enemy, self.mine_list)
            
            if hit_mines:
                # Udeř nepřítele (pokud zemře, odstraň ho a bonus)
                if enemy.take_damage(1):
                    enemies_to_remove.append(enemy)
                    self.score += 1
                    self.spawn_bonus_from_enemy(enemy)
                
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
            
            # Během respawn bomby je hráč chráněn
            if hit_enemies and not self.respawn_bomb_active:
                if self.extra_lives > 0:
                    # Spotřebuj extra život a respawnuj
                    self.use_extra_life()
                else:
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
        
        # Speciální spawn pro UFO (flythrough) - letí přes obrazovku
        if EnemyClass.MOVEMENT_TYPE == "flythrough":
            self.spawn_ufo(EnemyClass)
            return
        
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
    
    def spawn_ufo(self, EnemyClass):
        """Spawn UFO - letí přes obrazovku v náhodném směru
        
        Dráha je 10-30% od středu obrazovky (ne úplně v kraji ani ve středu)
        """
        margin = EnemyClass.RADIUS * EnemyClass.SCALE_MULTIPLIER + 50
        
        # Vyber náhodný okraj pro start (0=horní, 1=pravý, 2=dolní, 3=levý)
        start_edge = random.randint(0, 3)
        
        # Offset od středu (10-30% od středu obrazovky)
        offset_percent = random.uniform(0.1, 0.3)
        offset_direction = random.choice([-1, 1])  # Nahoře/dole nebo vlevo/vpravo od středu
        
        if start_edge == 0:  # Start nahoře
            # X pozice: střed + offset
            x = SCREEN_WIDTH // 2 + offset_direction * offset_percent * SCREEN_WIDTH // 2
            y = SCREEN_HEIGHT + margin
            # Cíl: dole (opačná strana)
            target_x = SCREEN_WIDTH // 2 - offset_direction * offset_percent * SCREEN_WIDTH // 2
            target_y = -margin
        elif start_edge == 1:  # Start vpravo
            x = SCREEN_WIDTH + margin
            y = SCREEN_HEIGHT // 2 + offset_direction * offset_percent * SCREEN_HEIGHT // 2
            # Cíl: vlevo
            target_x = -margin
            target_y = SCREEN_HEIGHT // 2 - offset_direction * offset_percent * SCREEN_HEIGHT // 2
        elif start_edge == 2:  # Start dole
            x = SCREEN_WIDTH // 2 + offset_direction * offset_percent * SCREEN_WIDTH // 2
            y = -margin
            # Cíl: nahoře
            target_x = SCREEN_WIDTH // 2 - offset_direction * offset_percent * SCREEN_WIDTH // 2
            target_y = SCREEN_HEIGHT + margin
        else:  # Start vlevo
            x = -margin
            y = SCREEN_HEIGHT // 2 + offset_direction * offset_percent * SCREEN_HEIGHT // 2
            # Cíl: vpravo
            target_x = SCREEN_WIDTH + margin
            target_y = SCREEN_HEIGHT // 2 - offset_direction * offset_percent * SCREEN_HEIGHT // 2
        
        # Vytvoř UFO
        enemy = EnemyClass(x, y, target_x=target_x, target_y=target_y)
        self.enemy_list.append(enemy)
    
    def activate_shockwave(self):
        """Aktivuje shockwave vlnu (pouze v noci a pokud má hráč náboje)"""
        if not self.is_day and self.player.shockwave_charges > 0 and not self.shockwave_active:
            self.shockwave_active = True
            self.shockwave_timer = 0
            self.shockwave_radius_current = 0
            self.shockwave_hit_enemies.clear()  # Reset zasažených nepřátel
            self.player.shockwave_charges -= 1
    
    def has_all_bonuses(self):
        """Zkontroluj, jestli má hráč všechny bonusy"""
        all_bonus_types = {"bomba", "extra_zivot", "miny", "shockwave", "kanon", "navadene_miny"}
        return all_bonus_types.issubset(self.collected_bonus_types)
    
    def spawn_bonus_from_enemy(self, enemy):
        """Vytvoř náhodný bonus pokud nepřítel má DROPS_BONUS"""
        if getattr(enemy, 'DROPS_BONUS', False):
            # Seznam dostupných bonusů (ty, které hráč ještě nesebral)
            available_bonuses = []
            
            # Bonus bomba - jen pokud nebyl sebrán
            if "bomba" not in self.collected_bonus_types:
                available_bonuses.append(("bomba", BonusBomba))
            
            # Bonus extra život - jen pokud nebyl sebrán
            if "extra_zivot" not in self.collected_bonus_types:
                available_bonuses.append(("extra_zivot", BonusExtraZivot))
            
            # Bonus miny - jen pokud nebyl sebrán
            if "miny" not in self.collected_bonus_types:
                available_bonuses.append(("miny", BonusMiny))
            
            # Bonus shockwave - jen pokud nebyl sebrán
            if "shockwave" not in self.collected_bonus_types:
                available_bonuses.append(("shockwave", BonusShockwave))
            
            # Bonus kanon (druhé dělo) - jen pokud nebyl sebrán
            if "kanon" not in self.collected_bonus_types:
                available_bonuses.append(("kanon", BonusKanon))
            
            # Bonus naváděné miny - jen pokud nebyl sebrán
            if "navadene_miny" not in self.collected_bonus_types:
                available_bonuses.append(("navadene_miny", BonusNavadeneMiny))
            
            # Náhodně vyber bonus
            if available_bonuses:
                bonus_type, BonusClass = random.choice(available_bonuses)
                bonus = BonusClass(enemy.center_x, enemy.center_y)
                self.bonus_list.append(bonus)
                print(f"🎁 UFO zničeno! Bonus '{bonus_type}' vytvořen na ({enemy.center_x:.0f}, {enemy.center_y:.0f})")
    
    def use_extra_life(self):
        """Použij extra život - respawn uprostřed s menší světelnou bombou"""
        self.extra_lives -= 1
        print(f"💔 Ztracen extra život! Zbývá: {self.extra_lives}")
        
        # Přesuň hráče doprostřed obrazovky
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = SCREEN_HEIGHT // 2
        
        # Aktivuj respawn bombu (menší světelná bomba - půlka obrazovky)
        self.respawn_bomb_active = True
        self.respawn_bomb_timer = 0
        self.respawn_bomb_radius_current = 0
        
        # Resetuj VŠECHNY bonusy - hráč musí znovu sbírat vše
        self.collected_bonus_types.clear()
        self.current_max_mines = MAX_MINES
        self.current_shockwave_radius = SHOCKWAVE_RADIUS
        self.has_second_cannon = False  # Reset druhého děla
        self.has_guided_mines = False  # Reset naváděných min
        self.light_bomb_count = 0  # Bez bomby - musí znovu sebrat
        
        print("🔄 RESPAWN! Všechny bonusy ztraceny - musíš znovu sbírat.")
    
    def activate_light_bomb(self):
        """Aktivuje světelnou atomovou bombu (zničí všechny nepřátele)"""
        if self.light_bomb_count > 0 and not self.light_bomb_active:
            self.light_bomb_active = True
            self.light_bomb_timer = 0
            self.light_bomb_radius_current = 0
            self.light_bomb_count -= 1
            print("💥 SVĚTELNÁ ATOMOVÁ BOMBA AKTIVOVÁNA!")
    
    def restart_game(self):
        """Restart hry"""
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = SCREEN_HEIGHT // 2
        self.player.game_over = False
        self.player.explode_timer = 0
        self.player.shockwave_charges = SHOCKWAVE_MAX_CHARGES
        
        # Reset světelné atomové bomby
        self.light_bomb_count = 1 if LIGHT_BOMB_STARTING else 0
        self.light_bomb_active = False
        self.light_bomb_timer = 0
        
        # Reset respawn bomby
        self.respawn_bomb_active = False
        self.respawn_bomb_timer = 0
        
        self.score = 0
        
        self.mine_list.clear()
        self.enemy_list.clear()
        self.bonus_list.clear()
        self.collected_bonus_types.clear()  # Reset sebraných bonusů
        if LIGHT_BOMB_STARTING:
            self.collected_bonus_types.add("bomba")  # Má bombu od začátku
        self.current_max_mines = MAX_MINES  # Reset max min
        self.current_shockwave_radius = SHOCKWAVE_RADIUS  # Reset shockwave radius
        self.extra_lives = 0  # Reset extra životů
        self.has_second_cannon = False  # Reset druhého děla
        self.has_guided_mines = False  # Reset naváděných min
        
        # Reset spawn timerů pro každého nepřítele
        for enemy_type in ENEMY_TYPES.keys():
            # Timer vždy začíná na 0 - první spawn nastane hned jakmile game_time >= start_time
            self.enemy_spawn_timers[enemy_type] = 0
        
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
        # V menu aktualizuj výběr podle pozice myši
        if self.menu.visible:
            self.menu.select_by_mouse(x, y)
            return
        
        if not self.player.game_over and not self.respawn_bomb_active:
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
            # První spuštění (last_trigger < 0 znamená, že vlna ještě nebyla spuštěna)
            if wave['last_trigger'] < 0 and self.game_time >= wave['trigger_time']:
                print(f"🌊 Spouštím vlnu '{wave['name']}' (game_time={self.game_time:.2f}, trigger_time={wave['trigger_time']})")
                self.spawn_wave(wave)
                wave['last_trigger'] = self.game_time
            # Opakování (kontroluj, že vlna už byla spuštěna - last_trigger >= 0)
            elif wave['last_trigger'] >= 0 and wave['repeat_interval'] > 0:
                time_since_last = self.game_time - wave['last_trigger']
                if time_since_last >= wave['repeat_interval']:
                    print(f"🔄 Opakuji vlnu '{wave['name']}' (game_time={self.game_time:.2f}, time_since_last={time_since_last:.2f})")
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
            elif pattern == "top":
                self.spawn_wave_top(enemy_type, count)
            elif pattern == "bottom":
                self.spawn_wave_bottom(enemy_type, count)
            elif pattern == "corners":
                self.spawn_wave_corners(enemy_type, count)
    
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
    
    def spawn_wave_top(self, enemy_type, count):
        """Spawn nepřátel nahoře směřujících dolů"""
        EnemyClass = ENEMY_TYPES[enemy_type]
        margin = EnemyClass.RADIUS + 30
        
        # Cíl dole
        target_y = -100
        
        for i in range(count):
            # Rozděl rovnoměrně po horní straně
            x = (SCREEN_WIDTH / (count + 1)) * (i + 1)
            y = SCREEN_HEIGHT + margin
            
            target_x = x  # Stejná X pozice
            
            # Vytvoř nepřítele
            if EnemyClass.MOVEMENT_TYPE == "direct":
                enemy = EnemyClass(x, y, side_direction=None, target_x=target_x, target_y=target_y)
            else:
                enemy = EnemyClass(x, y, side_direction=None)
                # Pro sideway nastav směr dolů
                enemy.change_x = 0
                enemy.change_y = -enemy.SPEED
            
            # Nastavení pro torpédo
            if enemy.MOVEMENT_TYPE == "seeking":
                enemy.mine_list = self.mine_list
                enemy.player = self.player
            
            # Nastavení pro Prudic (player_seeking)
            if enemy.MOVEMENT_TYPE == "player_seeking":
                enemy.player = self.player
            
            self.enemy_list.append(enemy)
    
    def spawn_wave_bottom(self, enemy_type, count):
        """Spawn nepřátel dole směřujících nahoru"""
        EnemyClass = ENEMY_TYPES[enemy_type]
        margin = EnemyClass.RADIUS + 30
        
        # Cíl nahoře
        target_y = SCREEN_HEIGHT + 100
        
        for i in range(count):
            # Rozděl rovnoměrně po dolní straně
            x = (SCREEN_WIDTH / (count + 1)) * (i + 1)
            y = -margin
            
            target_x = x  # Stejná X pozice
            
            # Vytvoř nepřítele
            if EnemyClass.MOVEMENT_TYPE == "direct":
                enemy = EnemyClass(x, y, side_direction=None, target_x=target_x, target_y=target_y)
            else:
                enemy = EnemyClass(x, y, side_direction=None)
                # Pro sideway nastav směr nahoru
                enemy.change_x = 0
                enemy.change_y = enemy.SPEED
            
            # Nastavení pro torpédo
            if enemy.MOVEMENT_TYPE == "seeking":
                enemy.mine_list = self.mine_list
                enemy.player = self.player
            
            # Nastavení pro Prudic (player_seeking)
            if enemy.MOVEMENT_TYPE == "player_seeking":
                enemy.player = self.player
            
            self.enemy_list.append(enemy)
    
    def spawn_wave_corners(self, enemy_type, count):
        """Spawn nepřátel v rozích obrazovky"""
        EnemyClass = ENEMY_TYPES[enemy_type]
        margin = EnemyClass.RADIUS + MAX_SPAWN_MARGIN
        
        # Definuj 4 rohy
        corners = [
            (margin, margin),  # Levý horní
            (SCREEN_WIDTH - margin, margin),  # Pravý horní
            (margin, SCREEN_HEIGHT - margin),  # Levý dolní
            (SCREEN_WIDTH - margin, SCREEN_HEIGHT - margin),  # Pravý dolní
        ]
        
        # Rozděl count rovnoměrně mezi rohy
        base_count_per_corner = count // 4
        remainder = count % 4
        
        # Spawn nepřátel
        for corner_idx in range(4):
            # Počet nepřátel v tomto rohu
            corner_count = base_count_per_corner
            if corner_idx < remainder:
                corner_count += 1
            
            corner_x, corner_y = corners[corner_idx]
            
            # Spawn nepřátel v tomto rohu
            for i in range(corner_count):
                # Pro více nepřátel v rohu, rozmísti je trochu od sebe
                if corner_count > 1:
                    # Rozmísti v malém kruhu kolem rohu
                    angle_offset = (360 / corner_count) * i
                    angle_rad = math.radians(angle_offset)
                    offset_distance = EnemyClass.RADIUS * 2
                    offset_x = offset_distance * math.cos(angle_rad)
                    offset_y = offset_distance * math.sin(angle_rad)
                else:
                    offset_x = 0
                    offset_y = 0
                
                x = corner_x + offset_x
                y = corner_y + offset_y
                
                # Vytvoř nepřítele
                enemy = EnemyClass(x, y, side_direction=None)
                
                # Nastavení pro torpédo
                if enemy.MOVEMENT_TYPE == "seeking":
                    enemy.mine_list = self.mine_list
                    enemy.player = self.player
                
                # Nastavení pro Prudic (player_seeking)
                if enemy.MOVEMENT_TYPE == "player_seeking":
                    enemy.player = self.player
                
                self.enemy_list.append(enemy)
    
    def play_song_at_index(self, index: int):
        """Přehraj píseň na daném indexu"""
        if not self.music_files:
            return
        
        # Zastav předchozí píseň, pokud hraje
        if self.current_music_player:
            self.current_music_player.delete()
            self.current_music_player = None
        
        # Nastav index (s wrap around)
        self.current_music_index = index % len(self.music_files)
        
        # Načti píseň
        current_file = self.music_files[self.current_music_index]
        
        # Extrahuj název (bez .mp3)
        self.current_song_name = os.path.basename(current_file).replace('.mp3', '')
        
        # Reset timeru pro zobrazení názvu
        self.song_name_display_timer = self.song_name_display_duration
        
        # Přehraj píseň pomocí Arcade
        music_sound = arcade.load_sound(current_file, streaming=True)
        self.current_music_player = music_sound.play(volume=0.5)
        
        print(f"♪ Přehrávám: {self.current_song_name}")
    
    def play_next_song(self):
        """Přehraj další píseň v seznamu (cyklicky) - klávesa W"""
        if not self.music_files:
            return
        next_index = (self.current_music_index + 1) % len(self.music_files)
        self.play_song_at_index(next_index)
    
    def play_previous_song(self):
        """Přehraj předchozí píseň v seznamu (cyklicky) - dvojité E"""
        if not self.music_files:
            return
        prev_index = (self.current_music_index - 1) % len(self.music_files)
        self.play_song_at_index(prev_index)
    
    def restart_current_song(self):
        """Restartuj aktuální píseň od začátku - klávesa E"""
        if not self.music_files:
            return
        self.play_song_at_index(self.current_music_index)
    
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
        # V menu - kliknutí aktivuje vybranou položku
        if self.menu.visible:
            if button == arcade.MOUSE_BUTTON_LEFT:
                # Nejdřív aktualizuj výběr podle pozice
                if self.menu.select_by_mouse(x, y):
                    result = self.menu.activate_selected()
                    self._process_menu_action(result)
            return
        
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
            if len(self.mine_list) < self.current_max_mines:
                if self.has_guided_mines:
                    # Naváděná mina
                    mine = GuidedMine(self.player.center_x, self.player.center_y, MINE_RADIUS, MINE_CORE_RADIUS)
                    mine.enemy_list = self.enemy_list  # Nastav reference na nepřátele
                else:
                    # Statická mina
                    mine = Mine(self.player.center_x, self.player.center_y, MINE_RADIUS, MINE_CORE_RADIUS)
                self.mine_list.append(mine)
    
    def on_key_press(self, key, modifiers):
        """Stisknutí klávesy"""
        # F1 - otevření/zavření menu
        if key == arcade.key.F1:
            self.menu.toggle()
            # Zobraz/schovej kurzor myši podle stavu menu
            self.set_mouse_visible(self.menu.visible)
            return
        
        # Ovládání hudby - funguje vždy (i v menu a game over)
        if key == arcade.key.W:
            # W = další písnička
            self.play_next_song()
            return
        elif key == arcade.key.E:
            # E = restart aktuální / EE = předchozí písnička
            current_time = time.time()
            if current_time - self.last_e_press_time < self.double_press_threshold:
                # Dvojité stisknutí - předchozí písnička
                self.play_previous_song()
                self.last_e_press_time = 0  # Reset pro další detekci
            else:
                # Jednoduché stisknutí - restart aktuální
                self.restart_current_song()
                self.last_e_press_time = current_time
            return
        
        # Pokud je menu otevřené, zpracuj klávesy pro menu
        if self.menu.visible:
            self._handle_menu_keys(key)
            return
        
        if self.player.game_over:
            return
        
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.rotate_left = True
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.rotate_right = True
        elif key == arcade.key.Q or key == arcade.key.ENTER:
            # Světelná atomová bomba (Q pro levou ruku, Enter pro pravou)
            self.activate_light_bomb()
    
    def _handle_menu_keys(self, key):
        """Zpracování kláves v menu"""
        # ESC - zavření menu
        if key == arcade.key.ESCAPE:
            self.menu.hide()
            self.set_mouse_visible(False)
            return
        
        # Šipky nahoru/dolů - navigace
        if key == arcade.key.UP:
            self.menu.move_selection(-1)
        elif key == arcade.key.DOWN:
            self.menu.move_selection(1)
        
        # Enter - aktivace vybrané položky
        elif key == arcade.key.ENTER:
            result = self.menu.activate_selected()
            self._process_menu_action(result)
        
        # Čísla 1-6 - přímý výběr položky
        elif key == arcade.key.KEY_1:
            result = self.menu.select_by_number(1)
            self._process_menu_action(result)
        elif key == arcade.key.KEY_2:
            result = self.menu.select_by_number(2)
            self._process_menu_action(result)
        elif key == arcade.key.KEY_3:
            result = self.menu.select_by_number(3)
            self._process_menu_action(result)
        elif key == arcade.key.KEY_4:
            result = self.menu.select_by_number(4)
            self._process_menu_action(result)
        elif key == arcade.key.KEY_5:
            result = self.menu.select_by_number(5)
            self._process_menu_action(result)
        elif key == arcade.key.KEY_6:
            result = self.menu.select_by_number(6)
            self._process_menu_action(result)
    
    def _process_menu_action(self, result: Optional[str]):
        """Zpracování akce z menu"""
        if result is None:
            return
        
        # Konec hry
        if result == "action_Konec hry":
            arcade.close_window()
        
        # Zde budou další akce podle potřeby
        # Pro submenu zatím jen debug výpis
        if result.startswith("submenu_"):
            submenu_name = result.replace("submenu_", "")
            print(f"📋 Submenu '{submenu_name}' - zatím neimplementováno")
        
        # Toggle obtížnosti
        if result == "toggle_Obtížnost":
            difficulty = self.menu.items[0].value
            print(f"🎮 Obtížnost změněna na: {difficulty}")
    
    def on_key_release(self, key, modifiers):
        """Uvolnění klávesy"""
        # V menu nereagujeme na uvolnění kláves
        if self.menu.visible:
            return
        
        if self.player.game_over:
            return
        
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.rotate_left = False
        elif key == arcade.key.D or key == arcade.key.RIGHT:
            self.rotate_right = False


def preload_enemy_textures():
    """Předem načti všechny textury nepřátel, aby se hra nezasekávala při spawnu"""
    print("Načítám textury nepřátel...")
    for enemy_type, EnemyClass in ENEMY_TYPES.items():
        print(f"  - {enemy_type}...")
        # Zavolej _load_cached_animations na třídě, aby se textury načetly do cache
        EnemyClass._load_cached_animations()
    print("Textury načteny!")


def main():
    # Předem načti textury
    preload_enemy_textures()
    
    game = Game()
    arcade.run()


if __name__ == "__main__":
    main()

