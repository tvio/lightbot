"""
LightBot - Infrastrukturní funkce
Sdílené funkce pro manipulaci s animacemi, kolizemi a jinými utility
"""
import arcade
import math
from typing import Tuple, Optional, Dict, List


def load_sprite_sheet(png_path: str, sprite_width: int, sprite_height: int, 
                     columns: int, rows: int, margin: int = 0) -> Tuple[Optional[List], Optional[int]]:
    """
    Načte animační textury z PNG sprite sheetu pomocí vestavěné funkce Arcade.
    
    Používá arcade.SpriteSheet a get_texture_grid() - oficiální API Arcade 3.x pro načítání sprite sheetů.
    Dokumentace: https://api.arcade.academy/en/stable/api_docs/api/texture.html#arcade.SpriteSheet
    
    Args:
        png_path: Cesta k PNG souboru (např. "pict/prudicV2.png")
        sprite_width: Šířka jednoho sprite v pixelech (0 = automaticky z obrázku)
        sprite_height: Výška jednoho sprite v pixelech (0 = automaticky z obrázku)
        columns: Počet sloupců v sprite sheetu
        rows: Počet řádků v sprite sheetu
        margin: Margin na okrajích obrázku (v pixelech) - použije se pro všechny okraje (left, right, bottom, top)
    
    Returns:
        Tuple (textures_list, base_texture_size) nebo (None, None) pokud se nepodaří
    """
    try:
        import os
        from PIL import Image
        
        # Zkontroluj, jestli soubor existuje
        if not os.path.exists(png_path):
            print(f"CHYBA: Sprite sheet soubor neexistuje: {png_path}")
            return None, None
        
        # Načti obrázek pro výpočet velikosti
        img = Image.open(png_path)
        img_width, img_height = img.size
        
        # Pokud není zadána velikost spritů, automaticky ji vypočítej z velikosti obrázku
        # S ohledem na margin: celková šířka = 2*margin + columns*sprite_width + (columns-1)*margin
        # Zjednodušeně: sprite_width = (img_width - 2*margin - (columns-1)*margin) / columns
        # = (img_width - margin*(columns+1)) / columns
        if sprite_width == 0 or sprite_height == 0:
            print(f"DEBUG: Velikost obrázku: {img_width}x{img_height} px, columns={columns}, rows={rows}, margin={margin}")
            
            if sprite_width == 0:
                sprite_width = (img_width - margin * (columns + 1)) // columns
            if sprite_height == 0:
                sprite_height = (img_height - margin * (rows + 1)) // rows
            print(f"Automaticky vypočítaná velikost spritů: {sprite_width}x{sprite_height} px (z obrázku {img_width}x{img_height} px)")
        
        # Ověř, že velikost spritů je větší než 0
        if sprite_width <= 0 or sprite_height <= 0:
            raise ValueError(f"Neplatná velikost spritů: {sprite_width}x{sprite_height} px")
        
        # Vypočítej celkový počet spritů
        count = columns * rows
        
        print(f"DEBUG: Načítám sprite sheet s parametry: size=({sprite_width}, {sprite_height}), columns={columns}, count={count}, margin={margin}")
        
        # V Arcade 3.x: Načti sprite sheet a použij get_texture_grid()
        # Margin tuple: (left, right, bottom, top) - všechny hodnoty se vztahují k okrajům obrázku
        sprite_sheet = arcade.SpriteSheet(png_path)
        
        textures = sprite_sheet.get_texture_grid(
            size=(sprite_width, sprite_height),
            columns=columns,
            count=count,
            margin=(margin, margin, margin, margin)  # (left, right, bottom, top) - stejný margin pro všechny okraje
        )
        
        if textures and len(textures) > 0:
            print(f"Úspěšně načteno {len(textures)} textur ze sprite sheetu: {png_path}")
            # Zjisti základní velikost (použijeme pro škálování)
            test_texture = textures[0]
            print(f"DEBUG: Velikost první textury: {test_texture.width}x{test_texture.height} px")
            base_size = max(test_texture.width, test_texture.height)
            if base_size == 0:
                print(f"VAROVÁNÍ: Textury mají nulovou velikost!")
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
    Najde nejbližší kolizi laseru s nepřáteli pomocí matematického výpočtu průsečíku přímky s kruhem.
    
    Args:
        laser_start_x, laser_start_y: Začátek laseru
        laser_end_x, laser_end_y: Konec laseru
        enemy_list: SpriteList s nepřáteli
        enemy_radius: Poloměr nepřítele (fallback)
        debug: Pokud True, vypisuj debug informace
    
    Returns:
        Tuple (hit, collision_x, collision_y, enemy_sprite) nebo (False, 0, 0, None)
    """
    # Směrový vektor laseru
    dx = laser_end_x - laser_start_x
    dy = laser_end_y - laser_start_y
    laser_length = math.sqrt(dx * dx + dy * dy)
    
    if laser_length < 1:
        return False, 0, 0, None
    
    # Normalizovaný směrový vektor
    dir_x = dx / laser_length
    dir_y = dy / laser_length
    
    closest_hit = None
    closest_t = laser_length  # Parametr t pro nejbližší průsečík
    
    for enemy in enemy_list:
        if hasattr(enemy, 'exploding') and enemy.exploding:
            continue
        
        # Vizuální poloměr nepřítele (RADIUS * SCALE_MULTIPLIER)
        base_radius = getattr(enemy, 'RADIUS', enemy_radius)
        scale_multiplier = getattr(enemy, 'SCALE_MULTIPLIER', 1)
        visual_radius = base_radius * scale_multiplier
        
        # Vektor od začátku laseru k středu nepřítele
        to_enemy_x = enemy.center_x - laser_start_x
        to_enemy_y = enemy.center_y - laser_start_y
        
        # Projekce na směr laseru (nejbližší bod na přímce k nepříteli)
        t_closest = to_enemy_x * dir_x + to_enemy_y * dir_y
        
        # Nejbližší bod na přímce laseru
        closest_x = laser_start_x + t_closest * dir_x
        closest_y = laser_start_y + t_closest * dir_y
        
        # Vzdálenost od nejbližšího bodu k středu nepřítele
        dist_to_center = math.sqrt(
            (closest_x - enemy.center_x) ** 2 + 
            (closest_y - enemy.center_y) ** 2
        )
        
        # Pokud je vzdálenost menší než poloměr, laser protíná kruh
        if dist_to_center <= visual_radius:
            # Vypočítej přesný bod průsečíku (vstupní bod do kruhu)
            # Použijeme Pythagorovu větu: half_chord = sqrt(r² - d²)
            half_chord = math.sqrt(visual_radius ** 2 - dist_to_center ** 2)
            
            # Bod vstupu laseru do kruhu (bližší průsečík)
            t_hit = t_closest - half_chord
            
            # Kontrola, že průsečík je na úsečce laseru (t >= 0 a t <= laser_length)
            if t_hit >= 0 and t_hit <= laser_length:
                if t_hit < closest_t:
                    closest_t = t_hit
                    collision_x = laser_start_x + t_hit * dir_x
                    collision_y = laser_start_y + t_hit * dir_y
                    closest_hit = (collision_x, collision_y, enemy)
                    
                    if debug:
                        print(f"[DEBUG] Hit {enemy.ENEMY_TYPE_NAME} at ({collision_x:.1f}, {collision_y:.1f}), t={t_hit:.1f}, visual_radius={visual_radius}")
    
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
