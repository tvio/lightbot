"""
LightBot - Fáze 2
Koule následující myš + rotující dělo (WSAD)
"""
import arcade
import math

# Konstanty
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1000
SCREEN_TITLE = "LightBot - Fáze 2"
ROBOT_RADIUS = 20
PERIMETER_RADIUS = 25  # Těsně u koule (mezera 5px)
CANNON_LENGTH = 15
ROTATION_SPEED = 3  # stupně za frame
LASER_DURATION = 0.1  # Jak dlouho laser svítí (sekundy)
LASER_RECHARGE_TIME = 3.0  # Čas dobití děla po střelbě (sekundy)
DAY_LENGTH = 30.0  # Délka dne v sekundách
NIGHT_LENGTH = 30.0  # Délka noci v sekundách
MINE_RADIUS = 6  # Poloměr miny (liché číslo pro přesný střed)
MINE_CORE_RADIUS = 5  # Poloměr červeného středu (liché)
BLINK_SPEED = 1  # Jak rychle bliká střed (cykly za sekundu)
MAX_MINES = 15  # Maximální počet min na obrazovce
ENEMY_RADIUS = 15  # Poloměr nepřítele
ENEMY_SPEED = 1  # Základní rychlost nepřítele (zpomaleno o 50%)
ENEMY_SPAWN_TIME = 1  # Jak často se spawn nepřítel (sekundy)
MAX_SPAWN_MARGIN = 40  # Maximální vzdálenost od okraje při spawnu


class Player(arcade.Sprite):
    """Sprite pro hráče (robota)"""
    def __init__(self, x, y):
        # Vytvoř texturu pro hráče (bílý kruh)
        player_texture = arcade.make_soft_circle_texture(
            ROBOT_RADIUS * 2,
            arcade.color.WHITE,
            outer_alpha=255
        )
        super().__init__(player_texture, center_x=x, center_y=y)
        
        # Stav pro konec hry
        self.game_over = False
        self.explode_timer = 0
        self.blink_state = False
    
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
                ROBOT_RADIUS * 2,
                color,
                outer_alpha=255
            )
            self.texture = red_texture


class Mine(arcade.Sprite):
    """Sprite pro minu"""
    def __init__(self, x, y):
        # Vytvoř texturu pro minu
        mine_texture = arcade.make_soft_circle_texture(
            MINE_RADIUS * 2,
            arcade.color.BLUE,
            outer_alpha=255
        )
        super().__init__(mine_texture, center_x=x, center_y=y)
        self.blink_state = False
    
    def draw_core(self, blink_on):
        """Vykresli blikající červený střed"""
        if blink_on:
            arcade.draw_circle_filled(
                self.center_x, self.center_y,
                MINE_CORE_RADIUS,
                arcade.color.RED
            )


# Globální cache pro animační textury (sdílené mezi všemi nepřáteli)
_enemy_animation_cache = None
_enemy_base_texture_size = None

def load_enemy_animations():
    """Načte animační textury jednou a uloží do cache (singleton pattern)"""
    global _enemy_animation_cache, _enemy_base_texture_size
    
    if _enemy_animation_cache is not None:
        return _enemy_animation_cache, _enemy_base_texture_size
    
    try:
        from PIL import Image
        import io
        
        gif_path = "pict/crab-red.gif"
        gif_image = Image.open(gif_path)
        
        textures = []
        frame_count = 0
        
        # Extrahuj všechny framy z GIFu
        try:
            while True:
                gif_image.seek(frame_count)
                
                # Konvertuj na RGBA pokud není
                if gif_image.mode != 'RGBA':
                    frame_img = gif_image.convert('RGBA')
                else:
                    frame_img = gif_image.copy()
                
                # Ulož do BytesIO
                img_bytes = io.BytesIO()
                frame_img.save(img_bytes, format='PNG')
                img_bytes.seek(0)
                
                # Načti jako texture v Arcade
                texture = arcade.load_texture(img_bytes)
                textures.append(texture)
                
                frame_count += 1
        except EOFError:
            pass
        
        if textures:
            # Ulož do cache
            _enemy_animation_cache = textures
            # Zjisti základní velikost (použijeme pro škálování)
            test_texture = textures[0]
            _enemy_base_texture_size = max(test_texture.width, test_texture.height)
            return textures, _enemy_base_texture_size
        else:
            raise ValueError("Žádné framy v GIFu")
    except Exception as e:
        print(f"Nelze načíst GIF kraba: {e}")
        return None, None


class Enemy(arcade.Sprite):
    """Sprite pro nepřítele s inteligentním pohybem a animací"""
    def __init__(self, x, y, side_direction=None):
        # Načti animované framy z globálního cache (sdílené textury)
        animation_textures, base_size = load_enemy_animations()
        
        self.animation_textures = animation_textures
        self.current_frame = 0
        self.animation_timer = 0
        self.frame_duration = 0.15  # 150ms per frame = ~6.7 FPS (pomalejší = lepší výkon)
        
        if animation_textures:
            # Nastav první frame (použijeme sdílenou texturu)
            super().__init__(animation_textures[0])
            self.center_x = x
            self.center_y = y
            
            # Škáluj na správnou velikost (zachovej poměr stran) - o 100% větší
            if base_size and base_size > 0:
                self.scale = (ENEMY_RADIUS * 2 * 2) / base_size  # 2x větší
        else:
            # Fallback na žlutý kruh, pokud se nepodaří načíst GIF
            print(f"Nelze načíst GIF kraba. Používám fallback kruh.")
            enemy_texture = arcade.make_soft_circle_texture(
                ENEMY_RADIUS * 2,
                arcade.color.YELLOW,
                outer_alpha=255
            )
            super().__init__(enemy_texture, center_x=x, center_y=y)
        
        # Stav pro výbuch
        self.exploding = False
        self.explode_timer = 0
        
        # Krab má náhodnou rotaci při spawnu
        import random
        # Náhodný úhel rotace (kam kouká) - libovolný úhel 0-360°
        random_angle = random.uniform(0, 360)
        # Podle testu: ROTATION_OFFSET = 0 (bez offsetu, rotace jde proti směru)
        # Použijeme záporné úhly pro správnou rotaci
        self.angle = -random_angle  # Záporné úhly pro správnou orientaci
        
        # Směr pohybu je bokem (kolmo na to, kam kouká)
        # Podle testu: SIDE_OFFSET_LEFT = -90, SIDE_OFFSET_RIGHT = +90
        # side_direction: -1 = levá strana (-90°), +1 = pravá strana (+90°)
        # Pokud není zadán, vyber náhodně
        if side_direction is None:
            self.side_direction = random.choice([-1, 1])  # Náhodně levý nebo pravý bok
        else:
            self.side_direction = side_direction
        
        # Úhel pohybu = úhel rotace + offset podle side_direction (bokem)
        # Pokud side_direction = -1 (levá strana), přičteme -90°
        # Pokud side_direction = +1 (pravá strana), přičteme +90°
        if self.side_direction == -1:
            movement_angle_degrees = self.angle + (-90)  # Doleva
        else:
            movement_angle_degrees = self.angle + 90  # Doprava
        
        # Převod na radiány - použij abs() pro správný výsledek
        movement_angle_rad = math.radians(abs(movement_angle_degrees))
        
        # Nastav rychlost podle úhlu pohybu
        self.change_x = math.cos(movement_angle_rad) * ENEMY_SPEED
        self.change_y = math.sin(movement_angle_rad) * ENEMY_SPEED
        
        # Časovač pro změnu směru (bokem) - delší interval
        self.movement_timer = 0
        self.direction_change_time = random.uniform(5, 12)  # Za 5-12 sekund změní směr
        
    def update(self, delta_time=1/60):
        """Update pozice a pohybového vzoru"""
        import random
        
        # Aktualizuj animaci (pokud má animované framy)
        # Optimalizace: animace se aktualizuje méně často pro lepší výkon
        if self.animation_textures and len(self.animation_textures) > 1 and not self.exploding:
            self.animation_timer += delta_time
            if self.animation_timer >= self.frame_duration:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.animation_textures)
                # Použijeme sdílenou texturu z cache (není potřeba kopírovat)
                self.texture = self.animation_textures[self.current_frame]
        
        # Pokud vybuchuje, odpočítávej čas a blikej
        if self.exploding:
            self.explode_timer -= delta_time
            # Blikni každý frame pro rychlé blikání
            self.update_explosion()
            if self.explode_timer <= 0:
                # Označ pro smazání
                self.remove_from_sprite_lists()
                return
        
        # Pokud vybuchuje, nehýbej se
        if self.exploding:
            return
        
        # Pohyb
        self.center_x += self.change_x
        self.center_y += self.change_y
        
        # Wraparound jako v Asteroids - objeví se na druhé straně
        # Ale na pozici, kde je plně viditelný (na okraji obrazovky)
        if self.center_x < -ENEMY_RADIUS:
            self.center_x = SCREEN_WIDTH - ENEMY_RADIUS  # Teleport na pravý okraj
        elif self.center_x > SCREEN_WIDTH + ENEMY_RADIUS:
            self.center_x = ENEMY_RADIUS  # Teleport na levý okraj
            
        if self.center_y < -ENEMY_RADIUS:
            self.center_y = SCREEN_HEIGHT - ENEMY_RADIUS  # Teleport na horní okraj
        elif self.center_y > SCREEN_HEIGHT + ENEMY_RADIUS:
            self.center_y = ENEMY_RADIUS  # Teleport na dolní okraj
        
        # Krab chodí bokem s malými oblouky
        self.movement_timer += delta_time
        
        # Vypočítej úhel pohybu = úhel rotace + offset podle side_direction (bokem)
        if self.side_direction == -1:
            movement_angle_degrees = self.angle + (-90)  # Doleva
        else:
            movement_angle_degrees = self.angle + 90  # Doprava
        
        # Převod na radiány - použij abs() pro správný výsledek
        movement_angle_rad = math.radians(abs(movement_angle_degrees))
        
        # Přidej malé oblouky (pomalá změna směru) - každý frame malá náhodná změna
        if random.random() < 0.3:  # 30% šance každý frame
            # Aktuální úhel pohybu s malou odchylkou (oblouky)
            current_movement_angle = movement_angle_rad + random.uniform(-0.02, 0.02)
            
            # Nastav rychlost podle úhlu s oblouky (abs už je v movement_angle_rad)
            self.change_x = math.cos(current_movement_angle) * ENEMY_SPEED
            self.change_y = math.sin(current_movement_angle) * ENEMY_SPEED
        else:
            # Bez oblouků - jdi přímo bokem
            self.change_x = math.cos(movement_angle_rad) * ENEMY_SPEED
            self.change_y = math.sin(movement_angle_rad) * ENEMY_SPEED
        
        if self.movement_timer >= self.direction_change_time:
            self.movement_timer = 0
            # Nový čas do další změny směru - delší interval
            self.direction_change_time = random.uniform(5, 12)
            
            # Změň směr - otoč na opačný bok (změň side_direction)
            self.side_direction *= -1
            
            # Přepočítej směr pohybu
            if self.side_direction == -1:
                movement_angle_degrees = self.angle + (-90)  # Doleva
            else:
                movement_angle_degrees = self.angle + 90  # Doprava
            # Převod na radiány - použij abs() pro správný výsledek
            movement_angle_rad = math.radians(abs(movement_angle_degrees))
            
            # Aktualizuj pohyb
            self.change_x = math.cos(movement_angle_rad) * ENEMY_SPEED
            self.change_y = math.sin(movement_angle_rad) * ENEMY_SPEED
        
        # Rotace zůstává stejná (podle spawnu)
        # self.angle se nemění
    
    def start_explosion(self):
        """Začni výbuch - zčervení"""
        self.exploding = True
        self.explode_timer = 0.2  # Bliká 0.2 sekundy
        self.blink_state = True  # Pro blikání
    
    def update_explosion(self):
        """Aktualizuj blikání při výbuchu"""
        if self.exploding:
            # Rychle bliká mezi červenou a jasnější červenou
            self.blink_state = not self.blink_state
            if self.blink_state:
                color = arcade.color.RED
            else:
                color = arcade.color.ORANGE_RED  # Jasnější červená
                
            red_texture = arcade.make_soft_circle_texture(
                ENEMY_RADIUS * 2,
                color,
                outer_alpha=255
            )
            self.texture = red_texture


def find_laser_collision_with_enemies(laser_start_x, laser_start_y, laser_end_x, laser_end_y, enemy_list, debug=False):
    """Najde nejbližší kolizi laseru s nepřáteli pomocí Arcade collision detection.
    Vrací (hit, collision_x, collision_y, enemy) nebo (False, 0, 0, None)"""
    
    # Vzdálenost laseru
    dx = laser_end_x - laser_start_x
    dy = laser_end_y - laser_start_y
    laser_length = math.sqrt(dx * dx + dy * dy)
    
    if laser_length < 1:
        return False, 0, 0, None
    
    # Počet kontrolních bodů podél laseru (každých 10 pixelů)
    check_spacing = 10
    num_checks = max(1, int(laser_length / check_spacing))
    
    if debug:
        print(f"[DEBUG collision] Checking {num_checks} points along laser length {laser_length:.1f}")
    
    closest_hit = None
    closest_distance = laser_length
    
    # Vytvoř jeden kontrolní sprite (reuse pro výkon)
    check_sprite = arcade.SpriteSolidColor(20, 20, arcade.color.WHITE)
    check_sprite.alpha = 0  # Neviditelný
    
    # Zkontroluj každý kontrolní bod
    for i in range(num_checks + 1):
        # Pozice kontrolního bodu
        t = i / num_checks if num_checks > 0 else 0
        check_x = laser_start_x + dx * t
        check_y = laser_start_y + dy * t
        
        # Použij existující sprite a jen změň pozici (rychlejší)
        check_sprite.center_x = check_x
        check_sprite.center_y = check_y
        
        # Zkontroluj kolizi s nepřáteli
        hit_enemies = arcade.check_for_collision_with_list(check_sprite, enemy_list)
        
        if hit_enemies:
            if debug:
                print(f"[DEBUG collision] Point {i} at ({check_x:.1f}, {check_y:.1f}) hit {len(hit_enemies)} enemy/enemies")
            # Najdi nejbližšího nepřítele
            for enemy in hit_enemies:
                if enemy.exploding:
                    if debug:
                        print(f"  Enemy at ({enemy.center_x:.1f}, {enemy.center_y:.1f}) is exploding, skipping")
                    continue
                
                # Vzdálenost od začátku laseru
                dist = math.sqrt((check_x - laser_start_x)**2 + (check_y - laser_start_y)**2)
                
                if debug:
                    print(f"  Checking enemy at ({enemy.center_x:.1f}, {enemy.center_y:.1f}), dist={dist:.1f}, closest={closest_distance:.1f}")
                
                if dist < closest_distance:
                    closest_distance = dist
                    # Pozice kolize - pozice nepřítele směrem k laseru
                    # Spočítej směr od nepřítele k začátku laseru
                    to_start_dx = laser_start_x - enemy.center_x
                    to_start_dy = laser_start_y - enemy.center_y
                    to_start_len = math.sqrt(to_start_dx**2 + to_start_dy**2)
                    
                    if to_start_len > 0:
                        # Normalizuj a posuň o poloměr nepřítele
                        to_start_dx /= to_start_len
                        to_start_dy /= to_start_len
                        collision_x = enemy.center_x + to_start_dx * ENEMY_RADIUS
                        collision_y = enemy.center_y + to_start_dy * ENEMY_RADIUS
                    else:
                        collision_x = enemy.center_x
                        collision_y = enemy.center_y
                    
                    if debug:
                        print(f"  NEW CLOSEST HIT! collision at ({collision_x:.1f}, {collision_y:.1f})")
                    closest_hit = (collision_x, collision_y, enemy)
    
    if closest_hit:
        return True, closest_hit[0], closest_hit[1], closest_hit[2]
    
    return False, 0, 0, None


def calculate_laser_end(start_x, start_y, angle_rad, screen_width, screen_height):
    """Spočítá, kde laser narazí na okraj obrazovky"""
    # Směrový vektor
    dx = math.cos(angle_rad)
    dy = math.sin(angle_rad)
    
    # Najdi průsečíky se všemi 4 hranami obrazovky
    t_values = []
    
    # Pravá hrana (x = screen_width)
    if dx > 0:
        t = (screen_width - start_x) / dx
        t_values.append(t)
    # Levá hrana (x = 0)
    elif dx < 0:
        t = -start_x / dx
        t_values.append(t)
    
    # Horní hrana (y = screen_height)
    if dy > 0:
        t = (screen_height - start_y) / dy
        t_values.append(t)
    # Dolní hrana (y = 0)
    elif dy < 0:
        t = -start_y / dy
        t_values.append(t)
    
    # Vyber nejmenší kladné t (nejbližší průsečík)
    if t_values:
        t = min(t for t in t_values if t > 0)
        end_x = start_x + t * dx
        end_y = start_y + t * dy
        return end_x, end_y
    
    # Fallback (nemělo by nastat)
    return start_x + 1000 * dx, start_y + 1000 * dy


class Game(arcade.Window):
    def __init__(self):
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE)
        arcade.set_background_color(arcade.color.BLACK)
        
        # Povol sledování výkonu pro FPS
        arcade.enable_timings()
        
        # Zapni VSync pro plynulejší vykreslování (redukuje trhání)
        self.set_vsync(True)
        
        # Schovej kurzor myši
        self.set_mouse_visible(False)
        
        # Hráč sprite
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.player_list = arcade.SpriteList(use_spatial_hash=False)  # Bez spatial hash (jen 1 sprite)
        self.player_list.append(self.player)
        
        # Úhel děla (0 = vpravo, 90 = nahoru)
        self.cannon_angle = 0
        
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
        self.debug_shot_count = 0  # Pro debug - počítadlo střel
        
        # Systém dobití děla
        self.laser_charge_time = LASER_RECHARGE_TIME  # Začíná plně nabitý (3.0s)
        
        # Systém dne a noci
        self.is_day = True  # True = den, False = noc
        self.day_night_timer = DAY_LENGTH  # Začínáme dnem, časovač odpočítává
        
        # Miny - SpriteList s spatial hashing pro rychlejší kolize
        self.mine_list = arcade.SpriteList(use_spatial_hash=True)
        
        # Časovač pro blikání min
        self.blink_timer = 0
        
        # Nepřátelé - SpriteList BEZ spatial hashing (spatial hash se aktualizuje při každém pohybu = pomalé)
        # Batch rendering je už optimalizovaný v SpriteList.draw()
        self.enemy_list = arcade.SpriteList(use_spatial_hash=False)
        
        # Časovač pro spawn nepřátel
        self.enemy_spawn_timer = 0  # První enemy ihned
        
        # Spawn prvního nepřítele hned
        self.spawn_enemy()
        
        # FPS tracking
        self.fps_display = 0
        self.fps_timer = 0
        
    def on_draw(self):
        """Vykreslení na obrazovku"""
        # Nastav barvu pozadí podle dne/noci
        if self.is_day:
            # Ve dne světlejší pozadí (tmavě šedé)
            arcade.set_background_color((40, 40, 50))  # Tmavě šedé s nádechem modré
        else:
            # V noci tmavé pozadí (černé)
            arcade.set_background_color(arcade.color.BLACK)
        
        self.clear()
        
        # Vykresli miny
        self.mine_list.draw()
        
        # Vykresli blikající červené středy min
        blink_on = (self.blink_timer % 1.0) < 0.5  # Bliká 50/50
        for mine in self.mine_list:
            mine.draw_core(blink_on)
        
        # Vykresli nepřátele
        self.enemy_list.draw()
        
        # Vykresli hráče (kreslí se i při game_over, ale jako červený)
        self.player_list.draw()
        
        # Vykresli vnější kruh (perimetr) - jen pokud není game over
        if not self.player.game_over:
            arcade.draw_circle_outline(
                self.player.center_x,
                self.player.center_y,
                PERIMETER_RADIUS,
                arcade.color.WHITE,
                2
            )
            
            # Vykresli dělo (tlustá čára)
            angle_rad = math.radians(self.cannon_angle)
            cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad)
            cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad)
            
            # Spočítej počáteční pozici děla (na obvodu kruhu)
            cannon_start_x = self.player.center_x + PERIMETER_RADIUS * math.cos(angle_rad)
            cannon_start_y = self.player.center_y + PERIMETER_RADIUS * math.sin(angle_rad)
            
            arcade.draw_line(
                cannon_start_x, cannon_start_y,
                cannon_end_x, cannon_end_y,
                arcade.color.RED,
                5
            )
        
        # Vykresli laser, pokud je aktivní a není game over
        if self.laser_active and not self.player.game_over:
            # DEBUG výpisy odstraněny kvůli výkonu
            arcade.draw_line(
                self.laser_start_x, self.laser_start_y,
                self.laser_end_x, self.laser_end_y,
                arcade.color.WHITE,
                3
            )
        
        # Vykresli progress bar pro dobití děla (nahoře na obrazovce)
        self.draw_charge_bar()
        
        # Vykresli stav světla (nahoře napravo)
        self.draw_light_status()
        
        # Zobraz FPS v levém horním rohu (použij arcade.Text pro lepší výkon)
        if not hasattr(self, 'fps_text'):
            self.fps_text = arcade.Text("", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 16)
        fps = arcade.get_fps()
        self.fps_text.text = f"FPS: {fps:.1f}"
        self.fps_text.draw()
    
    def draw_charge_bar(self):
        """Vykreslí progress bar pro dobití světelného děla"""
        # Pozice baru (uprostřed nahoře)
        bar_x = SCREEN_WIDTH // 2
        bar_y = SCREEN_HEIGHT - 40
        bar_width = 300
        bar_height = 20
        bar_padding = 5  # Mezera mezi textem a barem
        
        # Vypočítej procento nabití (0.0 až 1.0)
        charge_percentage = min(1.0, self.laser_charge_time / LASER_RECHARGE_TIME)
        
        # Text "Světelné dělo :"
        text_label = "Světelné dělo :"
        text_x = bar_x - bar_width // 2 - 120  # Text vlevo od baru
        text_y = bar_y
        
        # Vykresli text
        arcade.draw_text(
            text_label,
            text_x, text_y,
            arcade.color.WHITE,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
        # Vykresli bílý nevyplněný obdélník (outline)
        bar_left = bar_x - bar_width // 2
        bar_bottom = bar_y - bar_height // 2
        bar_top = bar_y + bar_height // 2
        
        # Vykresli obrys obdélníku pomocí draw_lbwh_rectangle_outline (left, bottom, width, height, color, border_width)
        border_width = 2
        arcade.draw_lbwh_rectangle_outline(
            bar_left,          # left
            bar_bottom,        # bottom
            bar_width,         # width
            bar_height,        # height
            arcade.color.WHITE,
            border_width       # border_width
        )
        
        # Vykresli vyplněný obdélník podle procenta nabití (zleva doprava)
        if charge_percentage > 0:
            filled_width = bar_width * charge_percentage
            filled_right = bar_left + filled_width  # Pravý okraj vyplněné části
            
            # Použij draw_lrbt_rectangle_filled (left, right, bottom, top, color)
            arcade.draw_lrbt_rectangle_filled(
                bar_left,          # left
                filled_right,      # right
                bar_bottom,        # bottom
                bar_top,           # top
                arcade.color.WHITE
            )
    
    def draw_light_status(self):
        """Vykreslí stav světla (Den/Noc) nahoře napravo na obrazovce"""
        # Pozice textu (napravo nahoře)
        text_x = SCREEN_WIDTH - 200
        text_y = SCREEN_HEIGHT - 40
        
        # Text podle stavu
        if self.is_day:
            status_text = "Stav světla: Den"
            text_color = arcade.color.YELLOW  # Žlutá pro den
        else:
            status_text = "Stav světla: Noc"
            text_color = arcade.color.BLUE  # Modrá pro noc
        
        # Vykresli text
        arcade.draw_text(
            status_text,
            text_x, text_y,
            text_color,
            16,
            anchor_x="left",
            anchor_y="center"
        )
        
    def update_laser_position(self):
        """Vypočítá pozice laseru a kolize s nepřáteli"""
        # Vypočítej pozice laseru
        angle_rad = math.radians(self.cannon_angle)
        cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad)
        cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad)
        
        # Pozice laseru (začátek)
        self.laser_start_x = cannon_end_x
        self.laser_start_y = cannon_end_y
        
        # Nejdřív najdi nejbližší průsečík s nepřítelem
        # Nejdřív spočítám konec na okraj obrazovky jako maximum
        screen_end_x, screen_end_y = calculate_laser_end(
            self.laser_start_x, self.laser_start_y,
            angle_rad,
            SCREEN_WIDTH, SCREEN_HEIGHT
        )
        
        # DEBUG výpisy odstraněny kvůli výkonu
        
        # Najdi kolizi s nepřáteli pomocí Arcade collision detection
        hit, collision_x, collision_y, hit_enemy = find_laser_collision_with_enemies(
            self.laser_start_x, self.laser_start_y,
            screen_end_x, screen_end_y,
            self.enemy_list,
            debug=False  # Debug vypnut kvůli výkonu
        )
        
        # Nastav konec laseru - buď na nepřítele nebo na okraj obrazovky
        if hit and hit_enemy:
            # Laser končí na nepřítele
            self.laser_end_x = collision_x
            self.laser_end_y = collision_y
            # Znič nepřítele
            hit_enemy.start_explosion()
        else:
            # Laser končí na okraji obrazovky
            self.laser_end_x = screen_end_x
            self.laser_end_y = screen_end_y
        
    def on_update(self, delta_time):
        """Update logiky hry"""
        # Update hráče (blikání při game over)
        if self.player.game_over:
            self.player.explode_timer -= delta_time
            # Blikni každý frame pro rychlé blikání
            self.player.update_game_over()
            # Po skončení blikání restart hry
            if self.player.explode_timer <= 0:
                self.restart_game()
                return
        
        # Pokud je game over, zastav vše
        if self.player.game_over:
            return
        
        # Rotace děla podle stisknutých kláves
        if self.rotate_left:
            self.cannon_angle += ROTATION_SPEED
        if self.rotate_right:
            self.cannon_angle -= ROTATION_SPEED
            
        # Normalizuj úhel (0-360)
        self.cannon_angle = self.cannon_angle % 360
        
        # Aktualizuj cyklus dne a noci
        self.day_night_timer -= delta_time
        if self.day_night_timer <= 0:
            # Přepni den/noc
            self.is_day = not self.is_day
            if self.is_day:
                self.day_night_timer = DAY_LENGTH
            else:
                self.day_night_timer = NIGHT_LENGTH
                # V noci resetuj nabití děla na 0
                self.laser_charge_time = 0
        
        # Aktualizuj dobití děla (pouze ve dne)
        if self.is_day:
            if self.laser_charge_time < LASER_RECHARGE_TIME:
                self.laser_charge_time += delta_time
                if self.laser_charge_time > LASER_RECHARGE_TIME:
                    self.laser_charge_time = LASER_RECHARGE_TIME
        else:
            # V noci je dělo na 0%
            self.laser_charge_time = 0
        
        # Odpočítávej časovač laseru
        if self.laser_active:
            self.laser_timer -= delta_time
            # DEBUG výpisy odstraněny kvůli výkonu
            if self.laser_timer <= 0:
                self.laser_active = False
            # POZICE SE NEPŘEPOČÍTÁVAJÍ - byly vypočítány při střelbě
            # Laser se pohybuje s hráčem, takže musíme aktualizovat pouze start
            # Ale konec zůstává stejný (kolize se už stala)
            else:
                # Aktualizuj pouze začátek laseru (konec zůstává stejný)
                angle_rad = math.radians(self.cannon_angle)
                cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad)
                cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad)
                self.laser_start_x = cannon_end_x
                self.laser_start_y = cannon_end_y
        
        # Aktualizuj časovač blikání min
        self.blink_timer += delta_time * BLINK_SPEED
        
        # Spawn nepřátel
        self.enemy_spawn_timer -= delta_time
        if self.enemy_spawn_timer <= 0:
            self.enemy_spawn_timer = ENEMY_SPAWN_TIME
            self.spawn_enemy()
        
        # Update nepřátel (batch update - efektivnější než jednotlivé update)
        self.enemy_list.update(delta_time)
        
        # Optimalizace: aktualizuj spatial hash jen jednou po všech update (pokud by byl zapnutý)
        # self.enemy_list.update_spatial_hash()  # Pouze pokud use_spatial_hash=True
        
        # Kolize nepřátel s minami
        enemies_to_remove = []
        mines_to_remove = []
        
        for enemy in self.enemy_list:
            if enemy.exploding:  # Přeskoč ty, co už vybuchují
                continue
                
            # Zkontroluj kolizi s minami
            hit_mines = arcade.check_for_collision_with_list(enemy, self.mine_list)
            
            if hit_mines:
                # Enemy narazil na minu
                enemy.start_explosion()
                enemies_to_remove.append(enemy)
                
                # Odstraň všechny miny, se kterými kolidoval
                for mine in hit_mines:
                    if mine not in mines_to_remove:
                        mines_to_remove.append(mine)
        
        # Odstraň miny
        for mine in mines_to_remove:
            mine.remove_from_sprite_lists()
        
        # Kolize nepřátel s hráčem (včetně kanonu)
        if not self.player.game_over:
            # Kolize s tělem hráče
            hit_enemies = arcade.check_for_collision_with_list(self.player, self.enemy_list)
            
            # Kolize s kanonem - vytvoř dočasný sprite pro kanon
            angle_rad = math.radians(self.cannon_angle)
            cannon_end_x = self.player.center_x + (PERIMETER_RADIUS + CANNON_LENGTH) * math.cos(angle_rad)
            cannon_end_y = self.player.center_y + (PERIMETER_RADIUS + CANNON_LENGTH) * math.sin(angle_rad)
            cannon_start_x = self.player.center_x + PERIMETER_RADIUS * math.cos(angle_rad)
            cannon_start_y = self.player.center_y + PERIMETER_RADIUS * math.sin(angle_rad)
            
            # Kolize s kanonem - geometrický výpočet vzdálenosti
            # Kanon je čára, zkontrolujeme vzdálenost každého enemy od této čáry
            cannon_length = math.sqrt((cannon_end_x - cannon_start_x)**2 + (cannon_end_y - cannon_start_y)**2)
            
            for enemy in self.enemy_list:
                if enemy.exploding:
                    continue
                    
                # Vzdálenost bodu od úsečky
                # Vektor kanonu
                dx = cannon_end_x - cannon_start_x
                dy = cannon_end_y - cannon_start_y
                
                # Vektor od začátku kanonu k enemy
                px = enemy.center_x - cannon_start_x
                py = enemy.center_y - cannon_start_y
                
                if cannon_length > 0:
                    # Projekce na kanon
                    t = max(0, min(1, (px * dx + py * dy) / (cannon_length ** 2)))
                    
                    # Nejbližší bod na kanonu
                    closest_x = cannon_start_x + t * dx
                    closest_y = cannon_start_y + t * dy
                    
                    # Vzdálenost enemy od kanonu
                    dist = math.sqrt((enemy.center_x - closest_x)**2 + (enemy.center_y - closest_y)**2)
                    
                    # Pokud je vzdálenost menší než součet poloměrů (kanon ~5px, enemy ~15px)
                    if dist < (ENEMY_RADIUS + 5):
                        if enemy not in hit_enemies:
                            hit_enemies.append(enemy)
            
            # Pokud nějaký enemy koliduje, konec hry
            if hit_enemies:
                self.player.start_game_over()
    
    def spawn_enemy(self):
        """Vytvoř nového nepřítele na náhodném okraji obrazovky"""
        import random
        
        # Vyber náhodný okraj (0=nahoře, 1=vpravo, 2=dole, 3=vlevo)
        edge = random.randint(0, 3)
        
        margin = ENEMY_RADIUS + 30  # Spawn s malou rezervou dovnitř
        
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
        
        # Urči směr ke středu obrazovky - krab bude jít bokem ke středu
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        
        # Vytvoř enemy s náhodnou rotací, ale side_direction určíme později
        enemy = Enemy(x, y, side_direction=None)
        
        # Směr ke středu (ve stupních)
        dx = center_x - x
        dy = center_y - y
        angle_to_center = math.degrees(math.atan2(dy, dx))
        
        # Úhel rotace kraba (záporný, může být cokoliv)
        crab_angle = enemy.angle  # Náhodná rotace z __init__
        
        # Zkus oba boky a zjisti, který vede blíž ke středu
        # Bokem doleva: crab_angle + (-90)
        # Bokem doprava: crab_angle + 90
        movement_left = abs(crab_angle + (-90))
        movement_right = abs(crab_angle + 90)
        
        # Normalizuj úhly na 0-360
        angle_to_center_norm = angle_to_center % 360
        if angle_to_center_norm < 0:
            angle_to_center_norm += 360
        
        movement_left_norm = movement_left % 360
        movement_right_norm = movement_right % 360
        
        # Najdi rozdíl (menší úhel mezi směry)
        diff_left = min(abs(movement_left_norm - angle_to_center_norm), 
                       360 - abs(movement_left_norm - angle_to_center_norm))
        diff_right = min(abs(movement_right_norm - angle_to_center_norm), 
                        360 - abs(movement_right_norm - angle_to_center_norm))
        
        # Vyber bok, který je blíž ke středu
        if diff_left < diff_right:
            enemy.side_direction = -1  # Doleva
        else:
            enemy.side_direction = 1  # Doprava
        
        # Přepočítej pohyb s novým side_direction
        if enemy.side_direction == -1:
            movement_angle_degrees = enemy.angle + (-90)
        else:
            movement_angle_degrees = enemy.angle + 90
        movement_angle_rad = math.radians(abs(movement_angle_degrees))
        enemy.change_x = math.cos(movement_angle_rad) * ENEMY_SPEED
        enemy.change_y = math.sin(movement_angle_rad) * ENEMY_SPEED
        
        self.enemy_list.append(enemy)
    
    def restart_game(self):
        """Restart hry"""
        # Reset hráče
        self.player.center_x = SCREEN_WIDTH // 2
        self.player.center_y = SCREEN_HEIGHT // 2
        self.player.game_over = False
        self.player.explode_timer = 0
        white_texture = arcade.make_soft_circle_texture(
            ROBOT_RADIUS * 2,
            arcade.color.WHITE,
            outer_alpha=255
        )
        self.player.texture = white_texture
        
        # Vymaž miny
        self.mine_list.clear()
        
        # Vymaž nepřátele
        self.enemy_list.clear()
        
        # Reset spawn timeru
        self.enemy_spawn_timer = 0
        self.spawn_enemy()
        
        # Reset laseru
        self.laser_active = False
        
        # Reset dobití děla (začíná plně nabitý)
        self.laser_charge_time = LASER_RECHARGE_TIME
        
        # Reset systému dne a noci (začíná dnem)
        self.is_day = True
        self.day_night_timer = DAY_LENGTH
    
    def on_mouse_motion(self, x, y, dx, dy):
        """Pohyb myši"""
        if not self.player.game_over:
            self.player.center_x = x
            self.player.center_y = y
    
    def can_fire_laser(self):
        """Zkontroluje, zda je dělo plně nabité a může střílet (pouze ve dne)"""
        return self.is_day and self.laser_charge_time >= LASER_RECHARGE_TIME
    
    def on_mouse_press(self, x, y, button, modifiers):
        """Kliknutí myši"""
        if self.player.game_over:
            return
            
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Vystřel laser, ale jen pokud je dělo plně nabité
            if not self.can_fire_laser():
                return  # Dělo není nabité, nelze střílet
                
            # Vystřel laser
            # DEBUG výpisy odstraněny kvůli výkonu
            self.laser_active = True
            self.laser_timer = LASER_DURATION
            self.laser_charge_time = 0  # Resetuj dobití po střelbě
            self.debug_shot_count += 1  # Zvýš počítadlo střel
            # Vypočítej pozice laseru a kolize hned
            self.update_laser_position()
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            # Polož minu na aktuální pozici robota, ale jen pokud není překročen limit
            if len(self.mine_list) < MAX_MINES:
                mine = Mine(self.player.center_x, self.player.center_y)
                self.mine_list.append(mine)
    
    def on_key_press(self, key, modifiers):
        """Stisknutí klávesy"""
        if self.player.game_over:
            return
            
        # A nebo šipka doleva = rotace doleva (proti směru hodin)
        if key == arcade.key.A or key == arcade.key.LEFT:
            self.rotate_left = True
        # D nebo šipka doprava = rotace doprava (po směru hodin)
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

