"""
LightBot - Fáze 2
Koule následující myš + rotující dělo (WSAD)

Refaktorované verze s modulární strukturou a YAML konfigurací
"""
import arcade
import math
import yaml
import random
from typing import Tuple, Optional

# Import modulů
from player import Player, Mine
from infrastruktura import find_laser_collision_with_enemies, calculate_laser_end
from enemies.base_enemy import BaseEnemy
from enemies import Crab, Star

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

DAY_LENGTH = CONFIG['day_night']['day_length']
NIGHT_LENGTH = CONFIG['day_night']['night_length']
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
}
ENEMY_CONFIG = CONFIG['enemies_config']

# Nastav screen dimensions pro BaseEnemy (pro wraparound)
BaseEnemy.SCREEN_WIDTH = SCREEN_WIDTH
BaseEnemy.SCREEN_HEIGHT = SCREEN_HEIGHT


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
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, ROBOT_RADIUS)
        self.player_list = arcade.SpriteList(use_spatial_hash=False)
        self.player_list.append(self.player)
        
        # Úhel děla
        self.cannon_angle = 0
        
        # Animace zmizení děla v noci
        self.cannon_fade_time = 2.0
        self.cannon_fade_timer = 0.0
        
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
        
        # Systém dobití
        self.laser_charge_time = LASER_RECHARGE_TIME
        
        # Den/Noc
        self.is_day = True
        self.day_night_timer = DAY_LENGTH
        self.player_color_day = True
        
        # Nastav barvu hráče
        self.player.update_color(self.is_day, DAY_ROBOT_COLOR, NIGHT_ROBOT_COLOR)
        
        # Miny
        self.mine_list = arcade.SpriteList(use_spatial_hash=True)
        
        # Časovač pro blikání min
        self.blink_timer = 0
        
        # Nepřátelé
        self.enemy_list = arcade.SpriteList(use_spatial_hash=False)
        
        # Spawn timer
        self.enemy_spawn_timer = 0
        self.spawn_enemy()
        
        # FPS tracking
        self.fps_display = 0
        self.fps_timer = 0
    
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
        
        # Vykresli progress bar
        self.draw_charge_bar()
        
        # Vykresli skóre
        self.vykresli_skore()
        
        # Zobraz FPS
        if not hasattr(self, 'fps_text'):
            self.fps_text = arcade.Text("", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 16)
        fps = arcade.get_fps()
        self.fps_text.text = f"FPS: {fps:.1f}"
        self.fps_text.draw()
    
    def draw_charge_bar(self):
        """Vykreslí progress bar pro dobití"""
        bar_x = SCREEN_WIDTH // 2
        bar_y = SCREEN_HEIGHT - 40
        bar_width = 300
        bar_height = 20
        
        charge_percentage = min(1.0, self.laser_charge_time / LASER_RECHARGE_TIME)
        
        text_color = arcade.color.WHITE
        bar_outline_color = arcade.color.WHITE
        bar_fill_color = arcade.color.WHITE
        
        text_label = "Světelné dělo :"
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
            hit_enemy.start_explosion()
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
        
        # Spawn nepřátel
        self.enemy_spawn_timer -= delta_time
        if self.enemy_spawn_timer <= 0:
            self.enemy_spawn_timer = ENEMY_SPAWN_TIME
            self.spawn_enemy()
        
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
                enemy.start_explosion()
                enemies_to_remove.append(enemy)
                self.score += 1
                
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
    
    def spawn_enemy(self):
        """Vytvoř nového nepřítele"""
        # Vyber náhodně typ nepřítele
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
    
    def restart_game(self):
        """Restart hry"""
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = SCREEN_HEIGHT // 2
        self.player.game_over = False
        self.player.explode_timer = 0
        self.player.update_color(self.is_day, DAY_ROBOT_COLOR, NIGHT_ROBOT_COLOR)
        
        self.score = 0
        
        self.mine_list.clear()
        self.enemy_list.clear()
        
        self.enemy_spawn_timer = 0
        self.spawn_enemy()
        
        self.laser_active = False
        self.laser_charge_time = LASER_RECHARGE_TIME
        
        self.is_day = True
        self.day_night_timer = DAY_LENGTH
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Pohyb myši"""
        if not self.player.game_over:
            self.player.center_x = x
            self.player.center_y = y
    
    def can_fire_laser(self):
        """Zkontroluj, zda lze střílet"""
        return self.is_day and self.laser_charge_time >= LASER_RECHARGE_TIME
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Kliknutí myši"""
        if self.player.game_over:
            return
        
        if button == arcade.MOUSE_BUTTON_LEFT:
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

