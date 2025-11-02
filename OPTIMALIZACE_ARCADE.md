# Možnosti optimalizace v Arcade pro plynulejší pohyb

## Implementované optimalizace:

### ✅ **Texture Caching (Hlavní optimalizace)**

- GIF animace se načítají JEN JEDNOU do globálního cache
- Všichni nepřátelé sdílejí stejné textury (místo kopírování)
- **Významné zlepšení:** Místo načítání N×textur → jen 1× načtení

```python
# Před: Každý Enemy načítal GIF znovu = pomalé
# Po: Globální cache, všechny Enemy sdílejí textury = rychlé
_enemy_animation_cache = None  # Globální cache
```

### ✅ **Pomalejší animace**

- FPS animace sníženo z 10 na ~6.7 (150ms místo 100ms)
- Méně přepínání textur = lepší výkon

### ✅ **Vypnutý spatial hashing pro dynamické objekty**

- Spatial hashing se aktualizuje při každém pohybu
- Pro dynamické objekty (nepřátelé, hráč) je to kontraproduktivní
- Batch rendering v SpriteList.draw() je už optimalizovaný

## Implementované optimalizace (původní):

### 1. **VSync** ✅

```python
self.set_vsync(True)
```

- Synchronizuje vykreslování s obnovovací frekvencí monitoru
- Redukuje trhání obrazu (screen tearing)
- Omezí FPS na refresh rate monitoru (obvykle 60 Hz)

### 2. **Spatial Hashing pro SpriteListy** ✅

```python
self.player_list = arcade.SpriteList(use_spatial_hash=True)
self.mine_list = arcade.SpriteList(use_spatial_hash=True)
self.enemy_list = arcade.SpriteList(use_spatial_hash=True)
```

- Zrychluje kolizní detekci
- Objekty jsou organizovány v prostorové mřížce
- Kolize se kontrolují jen s objekty v blízkosti

### 3. **Optimalizace textu** ✅

```python
# Místo arcade.draw_text() použij arcade.Text
self.fps_text = arcade.Text("", 10, SCREEN_HEIGHT - 30, arcade.color.WHITE, 16)
self.fps_text.text = f"FPS: {fps:.1f}"
self.fps_text.draw()
```

- `arcade.Text` je efektivnější než `arcade.draw_text()`
- Text se renderuje jen jednou, jen se mění obsah

## Další možnosti optimalizace:

### 4. **Omezit počet kontrolních bodů při kolizní detekci laseru**

```python
# V find_laser_collision_with_enemies:
check_spacing = 10  # Zkus zvýšit na 15-20 pro méně kontrolních bodů
```

### 5. **Omezit počet nepřátel současně na obrazovce**

```python
MAX_ENEMIES = 20  # Přidej limit
if len(self.enemy_list) < MAX_ENEMIES:
    self.spawn_enemy()
```

### 6. **Optimalizovat GIF animace**

- Snížit FPS animace (current_frame se může aktualizovat méně často)
- Použít menší rozlišení GIFů

### 7. **Batch rendering pro tvary**

- Místo `arcade.draw_circle_outline()` použít `ShapeElementList`
- Vykreslit více tvarů najednou

### 8. **Nastavit cílový FPS**

```python
self.set_update_rate(1/60)  # Cíl 60 FPS
```

### 9. **Optimalizovat kolizní detekci**

- Použít jednodušší hitboxy (čtverce místo kruhů)
- Kontrolovat kolize méně často (každý N-tý frame)

### 10. **Použít SpriteList pro vykreslování tvarů**

- Převést kruhy a čáry na sprites pokud je jich hodně

## Diagnostika:

### Problém: FPS ~55, trhání při pohybu myší

**Možné příčiny:**

1. Vysoké rozlišení (1600x1000) - hodně pixelů na vykreslení
2. GIF animace nepřátel - každý frame se přepočítává
3. Kolizní detekce - kontroluje se každý frame
4. Vykreslování tvarů (`draw_circle_outline`, `draw_line`) - není batch rendering

**Doporučení:**

- Zapnout VSync (✅ hotovo)
- Přidat spatial hashing (✅ hotovo)
- Pokud problém přetrvává, zkus:
  - Snížit rozlišení na 1280x800
  - Omezit počet nepřátel
  - Snížit FPS animace nepřátel
