"""
Skript pro vytvoření animovaného GIFu s rotací obrázku
Rotuje obrázek o 360 stupňů za 3 sekundy
"""
from PIL import Image, ImageFilter
import os


def detect_and_remove_grid(img, grid_color_tolerance=30):
    """
    Detekuje a odstraní mřížku z obrázku (pokud má specifickou barvu)
    
    Args:
        img: PIL Image objekt
        grid_color_tolerance: Tolerance pro detekci barvy mřížky
    
    Returns:
        PIL Image objekt bez mřížky
    """
    width, height = img.size
    pixels = img.load()
    
    # Zjisti barvu pozadí z rohů
    corner_pixels = [
        pixels[0, 0],
        pixels[width-1, 0],
        pixels[0, height-1],
        pixels[width-1, height-1]
    ]
    
    if img.mode == 'RGB':
        bg_color = tuple(int(sum(corner[i] for corner in corner_pixels) / len(corner_pixels)) 
                        for i in range(3))
    else:
        bg_color = (0, 0, 0)
    
    print(f"Detekce mrizky - barva pozadi: {bg_color}")
    
    # Vytvoř kopii obrázku
    result = img.copy()
    result_pixels = result.load()
    
    # Projdi obrázek a najdi pixely, které vypadají jako mřížka
    # Mřížka obvykle má podobnou barvu jako pozadí, ale může být trochu jiná
    # nebo může mít opakující se vzor
    
    removed_count = 0
    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            
            # Pokud je pixel podobný barvě pozadí (mřížka), nahraď ho barvou pozadí
            if img.mode == 'RGB':
                diff = sum(abs(pixel[i] - bg_color[i]) for i in range(3))
                if diff < grid_color_tolerance:
                    # Možná je to mřížka - zkontroluj, jestli je to opakující se vzor
                    # (např. každý N-tý pixel)
                    if x % 10 == 0 or y % 10 == 0 or (x + y) % 10 == 0:
                        result_pixels[x, y] = bg_color
                        removed_count += 1
    
    if removed_count > 0:
        print(f"Odstraneno {removed_count} pixelu mrizky")
        # Použij lehké rozmazání pro vyhlazení
        result = result.filter(ImageFilter.GaussianBlur(radius=0.5))
    else:
        print("Mrizka nebyla detekovana")
    
    return result


def create_rotating_gif(input_path: str, output_path: str, 
                       duration_seconds: float = 3.0, 
                       frames_per_second: int = 30):
    """
    Vytvoří animovaný GIF s rotujícím obrázkem
    
    Args:
        input_path: Cesta k vstupnímu obrázku
        output_path: Cesta k výstupnímu GIF souboru
        duration_seconds: Délka animace v sekundách
        frames_per_second: Počet framů za sekundu
    """
    if not os.path.exists(input_path):
        print(f"CHYBA: Vstupni soubor neexistuje: {input_path}")
        return False
    
    # Načti obrázek
    print(f"Nacitam obrazek: {input_path}")
    img = Image.open(input_path)
    
    width, height = img.size
    print(f"Velikost obrazku: {width}x{height} px")
    print(f"Format obrazku: {img.mode}")
    
    # Zjisti barvu pozadí z rohů obrázku (pro vyplnění prázdných rohů při rotaci)
    pixels = img.load()
    corner_pixels = [
        pixels[0, 0],  # Levý horní roh
        pixels[width-1, 0],  # Pravý horní roh
        pixels[0, height-1],  # Levý dolní roh
        pixels[width-1, height-1]  # Pravý dolní roh
    ]
    
    # Pokud je obrázek RGB, použij průměrnou barvu rohů
    if img.mode == 'RGB':
        bg_color = tuple(int(sum(corner[i] for corner in corner_pixels) / len(corner_pixels)) 
                        for i in range(3))
        print(f"Detekovana barva pozadi z rohu: RGB{bg_color}")
    elif img.mode == 'RGBA':
        bg_color = tuple(int(sum(corner[i] for corner in corner_pixels) / len(corner_pixels)) 
                        for i in range(4))
        print(f"Detekovana barva pozadi z rohu: RGBA{bg_color}")
    else:
        # Pro jiné formáty použij černou
        bg_color = (0, 0, 0) if img.mode != 'RGBA' else (0, 0, 0, 255)
        print(f"Pouzivam cernou barvu pozadi: {bg_color}")
    
    # Zkus detekovat a odstranit mřížku (pokud existuje)
    print("\nPokus o detekci a odstraneni mrizky...")
    img = detect_and_remove_grid(img, grid_color_tolerance=30)
    
    # Konvertuj na RGBA pro práci s rotací
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Vypočítej počet framů
    total_frames = int(duration_seconds * frames_per_second)
    frame_duration_ms = int(1000 / frames_per_second)  # Délka jednoho framu v ms
    
    print(f"Vytvarim {total_frames} framu")
    print(f"Délka jednoho framu: {frame_duration_ms}ms")
    print(f"Celkova delka animace: {duration_seconds}s")
    
    # Vypočítej úhel rotace pro každý fram
    degrees_per_frame = 360.0 / total_frames
    
    # Vytvoř framy
    frames = []
    center_x = width // 2
    center_y = height // 2
    
    print("\nGenerovani framu s rotaci...")
    for i in range(total_frames):
        # Vypočítej úhel rotace
        angle = i * degrees_per_frame
        
        # Rotuj obrázek
        # expand=True zajistí, že se obrázek nezkrátí při rotaci
        # fillcolor vyplní prázdné rohy barvou pozadí
        if len(bg_color) == 4:
            fill_color = bg_color  # RGBA
        else:
            fill_color = bg_color + (255,)  # RGB -> RGBA
        
        rotated = img.rotate(-angle, expand=True, resample=Image.BICUBIC, fillcolor=fill_color)
        
        # Pokud má rotovaný obrázek jinou velikost, vycentruj ho
        # (pro zachování stejné velikosti všech framů)
        rot_width, rot_height = rotated.size
        
        # Vytvoř nový obrázek s původní velikostí (nebo větší, pokud je potřeba)
        # Použijeme maximální velikost, aby se vešel celý rotovaný obrázek
        if i == 0:
            # První fram - zjisti maximální velikost
            max_size = max(rot_width, rot_height, width, height)
            # Zaokrouhli na sudé číslo (pro lepší kompresi)
            max_size = (max_size + 1) // 2 * 2
        
        # Vytvoř nový obrázek s maximální velikostí a barvou pozadí
        new_frame = Image.new('RGBA', (max_size, max_size), fill_color)
        
        # Vypočítej pozici pro centrování
        x_offset = (max_size - rot_width) // 2
        y_offset = (max_size - rot_height) // 2
        
        # Vlož rotovaný obrázek do středu
        # Protože rotovaný obrázek už má vyplněné pozadí, můžeme ho vložit přímo
        new_frame.paste(rotated, (x_offset, y_offset), rotated)
        
        # Konvertuj na 'P' mode (paleta) pro GIF
        # Nejdřív na RGB (GIF nepodporuje RGBA přímo)
        # Použijeme barvu pozadí pro konverzi
        rgb_bg = bg_color[:3] if len(bg_color) >= 3 else (0, 0, 0)
        rgb_frame = Image.new('RGB', new_frame.size, rgb_bg)
        rgb_frame.paste(new_frame, mask=new_frame.split()[3] if new_frame.mode == 'RGBA' else None)
        gif_frame = rgb_frame.convert('P', palette=Image.ADAPTIVE)
        
        frames.append(gif_frame)
        
        if (i + 1) % 10 == 0 or i == 0:
            print(f"  Vytvoren fram {i+1}/{total_frames} (uhel: {angle:.1f}°)")
    
    # Ulož jako animovaný GIF
    print(f"\nUkladam animovany GIF: {output_path}")
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration_ms,
        loop=0,  # Nekonečná smyčka
        optimize=True
    )
    
    print(f"OK: Vytvoren animovany GIF")
    print(f"  Pocet framu: {len(frames)}")
    print(f"  Velikost framu: {max_size}x{max_size} px")
    print(f"  Delka framu: {frame_duration_ms}ms")
    print(f"  Celkova delka: {duration_seconds}s")
    
    return True


def main():
    """Hlavní funkce"""
    print("=" * 60)
    print("Vytvareni animovaneho GIFu s rotaci")
    print("=" * 60)
    
    input_path = "pict/prudicV3.jpeg"
    output_path = "pict/prudicV3_rotating.gif"
    
    # Vytvoř animovaný GIF s rotací 360° za 3 sekundy
    success = create_rotating_gif(
        input_path=input_path,
        output_path=output_path,
        duration_seconds=3.0,
        frames_per_second=30  # 30 fps pro plynulou animaci
    )
    
    if success:
        print("\n" + "=" * 60)
        print("Hotovo!")
        print("=" * 60)
        print(f"\nVytvoreny soubor: {output_path}")
    else:
        print("\nCHYBA: Nepodarilo se vytvorit GIF!")


if __name__ == "__main__":
    main()

