"""
LightBot - Infrastrukturní funkce
Sdílené funkce pro manipulaci s animacemi, kolizemi a jinými utility
"""
import arcade
import math
from typing import Tuple, Optional, Dict, List


def load_sprite_sheet(png_path: str, sprite_width: int, sprite_height: int, 
                     columns: int, rows: int) -> Tuple[Optional[List], Optional[int]]:
    """
    Načte animační textury z PNG sprite sheetu pomocí vestavěné funkce Arcade.
    
    Arcade nemá přímo funkci pro načítání celého sprite sheetu, ale podporuje
    načítání jednotlivých spritů pomocí parametrů image_x, image_y, image_width, image_height.
    
    Args:
        png_path: Cesta k PNG souboru (např. "pict/prudicV2.png")
        sprite_width: Šířka jednoho sprite v pixelech
        sprite_height: Výška jednoho sprite v pixelech
        columns: Počet sloupců v sprite sheetu
        rows: Počet řádků v sprite sheetu
    
    Returns:
        Tuple (textures_list, base_texture_size) nebo (None, None) pokud se nepodaří
    """
    try:
        import os
        # Zkontroluj, jestli soubor existuje
        if not os.path.exists(png_path):
            print(f"CHYBA: Sprite sheet soubor neexistuje: {png_path}")
            return None, None
        
        textures = []
        
        # Načti každý sprite ze sprite sheetu pomocí vestavěné funkce Arcade
        # Procházíme řádky shora dolů, sloupce zleva doprava
        for row in range(rows):
            for col in range(columns):
                # Vypočítej pozici v sprite sheetu
                x = col * sprite_width
                y = row * sprite_height
                
                # Načti texture ze sprite sheetu pomocí vestavěné funkce Arcade
                # Zkusíme různé varianty parametrů, protože dokumentace není jasná
                try:
                    # Zkusíme s parametry image_x, image_y, image_width, image_height
                    texture = arcade.load_texture(
                        png_path,
                        image_x=x,
                        image_y=y,
                        image_width=sprite_width,
                        image_height=sprite_height
                    )
                except TypeError:
                    # Pokud to nefunguje, zkusíme s x, y, width, height
                    try:
                        texture = arcade.load_texture(
                            png_path,
                            x=x,
                            y=y,
                            width=sprite_width,
                            height=sprite_height
                        )
                    except TypeError:
                        # Pokud ani to nefunguje, použijeme PIL (fallback)
                        print(f"Varování: arcade.load_texture nepodporuje sprite sheet parametry, používám PIL fallback")
                        from PIL import Image
                        import io
                        sheet_image = Image.open(png_path)
                        if sheet_image.mode != 'RGBA':
                            sheet_image = sheet_image.convert('RGBA')
                        sprite_box = (x, y, x + sprite_width, y + sprite_height)
                        sprite_img = sheet_image.crop(sprite_box)
                        img_bytes = io.BytesIO()
                        sprite_img.save(img_bytes, format='PNG')
                        img_bytes.seek(0)
                        texture = arcade.load_texture(img_bytes)
                
                textures.append(texture)
        
        if textures:
            print(f"Úspěšně načteno {len(textures)} textur ze sprite sheetu: {png_path}")
            # Zjisti základní velikost (použijeme pro škálování)
            test_texture = textures[0]
            base_size = max(test_texture.width, test_texture.height)
            return textures, base_size
        else:
            raise ValueError(f"Žádné sprites v sprite sheetu: {png_path}")
    except Exception as e:
        print(f"Nelze načíst sprite sheet: {png_path} - {e}")
        import traceback
        traceback.print_exc()
        return None, None


def load_enemy_animations(gif_path: str) -> Tuple[Optional[List], Optional[int]]:
    """
    Načte animační textury z GIF souboru a uloží do cache (singleton pattern).
    
    Args:
        gif_path: Cesta k GIF souboru (např. "pict/crab-red.gif")
    
    Returns:
        Tuple (textures_list, base_texture_size) nebo (None, None) pokud se nepodaří
    """
    try:
        from PIL import Image
        import io
        
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
            # Zjisti základní velikost (použijeme pro škálování)
            test_texture = textures[0]
            base_size = max(test_texture.width, test_texture.height)
            return textures, base_size
        else:
            raise ValueError(f"Žádné framy v GIFu: {gif_path}")
    except Exception as e:
        print(f"Nelze načíst GIF: {gif_path} - {e}")
        return None, None


def find_laser_collision_with_enemies(
    laser_start_x: float,
    laser_start_y: float,
    laser_end_x: float,
    laser_end_y: float,
    enemy_list: arcade.SpriteList,
    enemy_radius: float,
    debug: bool = False
) -> Tuple[bool, float, float, Optional[arcade.Sprite]]:
    """
    Najde nejbližší kolizi laseru s nepřáteli pomocí Arcade collision detection.
    
    Args:
        laser_start_x, laser_start_y: Začátek laseru
        laser_end_x, laser_end_y: Konec laseru
        enemy_list: SpriteList s nepřáteli
        enemy_radius: Poloměr nepřítele (pro správný výpočet kolize)
        debug: Pokud True, vypisuj debug informace
    
    Returns:
        Tuple (hit, collision_x, collision_y, enemy_sprite) nebo (False, 0, 0, None)
    """
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
                if hasattr(enemy, 'exploding') and enemy.exploding:
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
                    to_start_dx = laser_start_x - enemy.center_x
                    to_start_dy = laser_start_y - enemy.center_y
                    to_start_len = math.sqrt(to_start_dx**2 + to_start_dy**2)
                    
                    if to_start_len > 0:
                        # Normalizuj a posuň o poloměr nepřítele
                        to_start_dx /= to_start_len
                        to_start_dy /= to_start_len
                        collision_x = enemy.center_x + to_start_dx * enemy_radius
                        collision_y = enemy.center_y + to_start_dy * enemy_radius
                    else:
                        collision_x = enemy.center_x
                        collision_y = enemy.center_y
                    
                    if debug:
                        print(f"  NEW CLOSEST HIT! collision at ({collision_x:.1f}, {collision_y:.1f})")
                    closest_hit = (collision_x, collision_y, enemy)
    
    if closest_hit:
        return True, closest_hit[0], closest_hit[1], closest_hit[2]
    
    return False, 0, 0, None


def calculate_laser_end(
    start_x: float,
    start_y: float,
    angle_rad: float,
    screen_width: int,
    screen_height: int
) -> Tuple[float, float]:
    """
    Spočítá, kde laser narazí na okraj obrazovky.
    
    Args:
        start_x, start_y: Počáteční pozice laseru
        angle_rad: Úhel laseru v radiánech
        screen_width, screen_height: Rozměry obrazovky
    
    Returns:
        Tuple (end_x, end_y) - pozice konce laseru na okraji
    """
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
