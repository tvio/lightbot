# LightBot - Refaktoring Projektu

## Přehled změn

Projekt byl refaktorován z jednolitého souboru (`main.py`) na modulární strukturu s oddělením odpovědnosti a konfigurací v YAML.

## Nová struktura projektu

```
lightbot/
├── main.py                  # Hlavní game loop a Game class
├── player.py               # Player a Mine sprites
├── infrastruktura.py       # Sdílené funkce (animace, kolize, utility)
├── game_config.yaml        # Centrální YAML konfigurace
├── enemies/
│   ├── __init__.py         # Package init (exportuje Crab, Star)
│   ├── base_enemy.py       # Základní třída BaseEnemy
│   ├── crab.py             # Třída Crab (původní Enemy)
│   └── star.py             # Třída Star (nový nepřítel)
├── pict/
│   ├── crab-red.gif        # Animace kraba
│   └── animated_star_pingpong.gif  # Animace hvězdy
└── ... ostatní soubory ...
```

## Klíčové komponenty

### 1. **game_config.yaml** - Centrální konfigurace
Všechny herní konstanty se nyní načítají z YAML souboru:
- Rozměry obrazovky
- Vlastnosti hráče
- Nastavení zbraní
- Systém den/noc
- Konfigurace typů nepřátel (Crab, Star)

**Výhody:**
- Jednoduché měnění herních hodnot bez editace kódu
- Centralizované nastavení
- Snadné přidání nových nepřátel

### 2. **player.py** - Player a Mine sprites
Oddělené třídy z původního `main.py`:
- `Player` - robot v centru, reaguje na pohyb myši
- `Mine` - modrá kulatá mina s blikavým červeným středem

### 3. **infrastruktura.py** - Sdílené utility
Funkce používané v celém projektu:
- `load_enemy_animations(gif_path)` - Načítá GIF animace s cachováním
- `find_laser_collision_with_enemies()` - Detekce kolizí laseru s nepřáteli
- `calculate_laser_end()` - Výpočet konce laseru na okraji obrazovky

### 4. **enemies/base_enemy.py** - Základní třída nepřítele
Abstraktní třída pro všechny typy nepřátel:
- Sdílené logiky (animace, pohyb, výbuchy)
- Třídní proměnné pro konfiguraci
- Podporuje dva typy pohybu:
  - `"sideway"` - postranní chůze s oblouky (Crab)
  - `"direct"` - přímý pohyb (Star)

**Cachování animací:**
- Každý typ nepřítele cachuje svou animaci
- Všechny instance stejného typu sdílí textury
- Optimalizace výkonu

### 5. **enemies/crab.py** - Třída Crab
Konkrétní implementace nepřítele:
- Jméno: "crab"
- Animace: `pict/crab-red.gif`
- Pohyb: postranní (`sideway`) s náhodným obloukem
- Eigenschaften: radius=15, speed=1

### 6. **enemies/star.py** - Třída Star (NOVÁ)
Nový typ nepřítele:
- Jméno: "star" (hvězda)
- Animace: `pict/animated_star_pingpong.gif`
- Pohyb: přímý (`direct`)
- Vlastnosti: radius=12, speed=1.5 (rychlejší než krab)

## Jak přidat nového nepřítele

### Krok 1: Připravit soubor obrázku
Umístěte GIF animaci do `pict/` složky.
Příklad: `pict/enemy-name.gif`

### Krok 2: Vytvořit Python soubor
Vytvořte soubor `enemies/enemy_name.py`:

```python
from .base_enemy import BaseEnemy

class EnemyName(BaseEnemy):
    """Popis nepřítele"""
    
    ENEMY_TYPE_NAME = "enemy_name"
    GIF_PATH = "pict/enemy-name.gif"
    RADIUS = 14
    SPEED = 1.2
    ANIMATION_FRAME_DURATION = 0.12
    SCALE_MULTIPLIER = 1.8
    MOVEMENT_TYPE = "sideway"  # nebo "direct"
    DIRECTION_CHANGE_TIME_RANGE = [4, 10]
```

### Krok 3: Přidat do enemies/__init__.py

```python
from .enemy_name import EnemyName
__all__ = ['Crab', 'Star', 'EnemyName']
```

### Krok 4: Přidat konfiguraci do game_config.yaml

```yaml
enemies_config:
  # ... ostatní nepřátelé ...
  enemy_name:
    radius: 14
    speed: 1.2
    animation_path: "pict/enemy-name.gif"
    animation_frame_duration: 0.12
    scale_multiplier: 1.8
    movement_direction_change_time: [4, 10]
    movement_type: "sideway"
```

### Krok 5: Přidat do main.py (v ENEMY_TYPES)

```python
from enemies import Crab, Star, EnemyName

ENEMY_TYPES = {
    'crab': Crab,
    'star': Star,
    'enemy_name': EnemyName,
}
```

## Vlastnosti BaseEnemy

### Třídní proměnné pro přizpůsobení

- `ENEMY_TYPE_NAME` - Identifikátor typu
- `GIF_PATH` - Cesta k GIF animaci
- `RADIUS` - Poloměr nepřítele
- `SPEED` - Základní rychlost pohybu
- `ANIMATION_FRAME_DURATION` - Doba mezi framy animace
- `SCALE_MULTIPLIER` - Jak velký má být vůči textuře
- `MOVEMENT_TYPE` - Typ pohybu: `"sideway"` nebo `"direct"`
- `DIRECTION_CHANGE_TIME_RANGE` - [min, max] sekund před změnou směru

### Automatické chování

- **Animace**: Automaticky se přehrávají z GIF, s cachováním
- **Výbuch**: Automatické blikání červeně při zničení
- **Wraparound**: Automatické zabalení na druhé straně obrazovky
- **Spawn logika**: Optimální pohyb směrem ke středu

## Migrace z původního kódu

### Co se změnilo:
1. `Enemy` třída → `BaseEnemy` (abstraktní) + `Crab`, `Star` (konkrétní)
2. Konstanty v `main.py` → `game_config.yaml`
3. Globální cache → Třídní cache v `BaseEnemy`
4. Třídy `Player`, `Mine` → Oddělený modul `player.py`
5. Utility funkce → `infrastruktura.py`

### Co zůstalo stejné:
- Game loop v `Game` třídě
- Logika kolizí
- Systém den/noc
- Ovládání (WSAD, myš)

## Výhody nové struktury

✅ **Modularita** - Snadnější přidávání nových funkcí  
✅ **Scalability** - Lze snadno přidat nové typy nepřátel  
✅ **Konfigurace** - Změny bez editace kódu  
✅ **Kód reuse** - Sdílená logika v `BaseEnemy`  
✅ **Testovatelnost** - Jednotlivé moduly lze testovat izolovaně  
✅ **Čitelnost** - Menší soubory, jasná odpovědnost  

## Budoucí vylepšení

- [ ] Přidat více typů nepřátel
- [ ] Powery/Power-ups
- [ ] Různé levely
- [ ] AI logika pro nepřátele
- [ ] Multiplayer režim
