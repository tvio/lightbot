# KOMENTOVANÝ KÓD - POHYB KRABA

## 1. INICIALIZACE (při spawnu) - řádky 157-184

```python
# ========================================
# NASTAVENÍ ROTACE OBRAZKU (kam krab kouká)
# ========================================
# Náhodný úhel 0-360° - kam bude krab koukat
random_angle = random.uniform(0, 360)
self.angle = random_angle  # Tohle je rotace OBRAZKU v Arcade (0° = vpravo)

# ========================================
# NASTAVENÍ SMĚRU POHYBU (bokem)
# ========================================
# Urči, který bok se použije: -1 = levý bok (-90°), +1 = pravý bok (+90°)
self.side_direction = random.choice([-1, 1])

# Úhel pohybu = úhel rotace ± 90° (bokem = kolmo na to, kam kouká)
# Příklad: Pokud kouká 45°, chodí pod úhlem 135° nebo -45° (což je 315°)
movement_angle_degrees = random_angle + (self.side_direction * 90)

# Normalizuj na 0-360°
if movement_angle_degrees < 0:
    movement_angle_degrees += 360
elif movement_angle_degrees >= 360:
    movement_angle_degrees -= 360

# Převod na radiány (math.cos/sin používají radiány)
movement_angle_rad = math.radians(movement_angle_degrees)

# Nastav rychlost pohybu (vektor change_x, change_y)
self.change_x = math.cos(movement_angle_rad) * ENEMY_SPEED
self.change_y = math.sin(movement_angle_rad) * ENEMY_SPEED
```

## 2. UPDATE (každý frame) - řádky 186-275

```python
def update(self, delta_time=1/60):
    # ========================================
    # ANIMACE (přepínání framů GIFu)
    # ========================================
    if self.animation_textures and len(self.animation_textures) > 1 and not self.exploding:
        self.animation_timer += delta_time
        if self.animation_timer >= self.frame_duration:
            self.animation_timer = 0
            self.current_frame = (self.current_frame + 1) % len(self.animation_textures)
            self.texture = self.animation_textures[self.current_frame]

    # ========================================
    # VÝBUCH (pokud je zasažen)
    # ========================================
    if self.exploding:
        self.explode_timer -= delta_time
        self.update_explosion()
        if self.explode_timer <= 0:
            self.remove_from_sprite_lists()
            return
        if self.exploding:
            return  # Nehýbej se, když vybuchuje

    # ========================================
    # POHYB POZICE (přesunutí podle change_x, change_y)
    # ========================================
    self.center_x += self.change_x
    self.center_y += self.change_y

    # Wraparound (objeví se na druhé straně obrazovky)
    if self.center_x < -ENEMY_RADIUS:
        self.center_x = SCREEN_WIDTH + ENEMY_RADIUS
    elif self.center_x > SCREEN_WIDTH + ENEMY_RADIUS:
        self.center_x = -ENEMY_RADIUS
    if self.center_y < -ENEMY_RADIUS:
        self.center_y = SCREEN_HEIGHT + ENEMY_RADIUS
    elif self.center_y > SCREEN_HEIGHT + ENEMY_RADIUS:
        self.center_y = -ENEMY_RADIUS

    # ========================================
    # PŘEPOČET SMĚRU POHYBU (aby byl vždy bokem)
    # ========================================
    self.movement_timer += delta_time

    # Vždy přepočítej směr pohybu z rotace ± 90°
    # self.angle zůstává STEJNÁ (ne mění se)
    movement_angle_degrees = self.angle + (self.side_direction * 90)

    # Normalizuj na 0-360°
    if movement_angle_degrees < 0:
        movement_angle_degrees += 360
    elif movement_angle_degrees >= 360:
        movement_angle_degrees -= 360

    # Převod na radiány
    movement_angle_rad = math.radians(movement_angle_degrees)

    # ========================================
    # OBLOUKY (malé odchylky od přímého směru)
    # ========================================
    if random.random() < 0.3:  # 30% šance
        # Přidej malou náhodnou odchylku (oblouky)
        current_movement_angle = movement_angle_rad + random.uniform(-0.02, 0.02)
        self.change_x = math.cos(current_movement_angle) * ENEMY_SPEED
        self.change_y = math.sin(current_movement_angle) * ENEMY_SPEED
    else:
        # Přímý pohyb bokem
        self.change_x = math.cos(movement_angle_rad) * ENEMY_SPEED
        self.change_y = math.sin(movement_angle_rad) * ENEMY_SPEED

    # ========================================
    # ZMĚNA SMĚRU (otočení na opačný bok)
    # ========================================
    if self.movement_timer >= self.direction_change_time:
        self.movement_timer = 0
        self.direction_change_time = random.uniform(5, 12)

        # Změň side_direction (-1 ↔ +1)
        self.side_direction *= -1

        # Přepočítej směr pohybu
        movement_angle_degrees = self.angle + (self.side_direction * 90)
        if movement_angle_degrees < 0:
            movement_angle_degrees += 360
        elif movement_angle_degrees >= 360:
            movement_angle_degrees -= 360
        movement_angle_rad = math.radians(movement_angle_degrees)

        # Aktualizuj rychlost
        self.change_x = math.cos(movement_angle_rad) * ENEMY_SPEED
        self.change_y = math.sin(movement_angle_rad) * ENEMY_SPEED

    # DŮLEŽITÉ: self.angle se NEMĚNÍ - rotace zůstává stejná!
```

## 3. VYKRESLENÍ - řádek 478

```python
# V on_draw():
self.enemy_list.draw()  # Arcade automaticky použije self.angle pro rotaci
```

## PROBLÉM - MOŽNÉ PŘÍČINY:

1. **Orientace obrázku:** Možná obrázek kraba v GIFu není orientovaný správně (0° = vpravo).

   - Řešení: Zkus přičíst/odečíst 90° k `self.angle` při inicializaci.

2. **Arcade rotace:** V Arcade 0° = vpravo, 90° = nahoru, 180° = vlevo, 270° = dolů.

   - Zkontroluj, jestli to odpovídá orientaci obrázku kraba.

3. **Normalizace úhlu:** Možná problém s přepočtem úhlů při změně směru.

4. **Oblouky:** Možná oblouky způsobují, že se směr odchýlí od "bokem".

## PŘÍKLADY S HODNOTAMI

### Příklad 1: Krab kouká 45° a jde DOLEVA

```
self.angle = 45°
self.side_direction = -1  (levý bok = -1)
ENEMY_SPEED = 1

# Výpočet:
movement_angle_degrees = 45 + (-1 * 90)
                       = 45 - 90
                       = -45°

# Normalizace na 0-360°:
movement_angle_degrees = -45 + 360 = 315°

# Převod na radiány:
movement_angle_rad = math.radians(315)
                   ≈ 5.498 radians

# Výpočet pohybu:
change_x = math.cos(5.498) * 1
         ≈ 0.707 * 1
         ≈ +0.707  (pohyb DOPRAVA)

change_y = math.sin(5.498) * 1
         ≈ -0.707 * 1
         ≈ -0.707  (pohyb NAHORU - matematicky)

VÝSLEDEK: Krab kouká 45° a pohybuje se pod úhlem 315° (dolů-doprava)
```

### Příklad 2: Krab kouká 0° (doprava) a jde doleva

```
self.angle = 0°
self.side_direction = -1  (levý bok)
ENEMY_SPEED = 2

# Výpočet:
movement_angle_degrees = 0 + (-1 * 90)
                       = -90°

# Normalizace:
movement_angle_degrees = -90 + 360 = 270°

# Převod na radiány:
movement_angle_rad = math.radians(270)
                   ≈ 4.712 radians

# Výpočet pohybu:
change_x = math.cos(4.712) * 2
         ≈ 0 * 2
         = 0  (bez pohybu v X)

change_y = math.sin(4.712) * 2
         ≈ -1 * 2
         = -2  (pohyb NAHORU - matematicky, nebo DOLŮ - Arcade?)

VÝSLEDEK: Krab kouká vpravo (0°) a jde NAHORU pod úhlem 270°
```

### Příklad 3: Krab kouká 90° (nahoru) a jde DOPRAVA

```
self.angle = 90°
self.side_direction = +1  (pravý bok)
ENEMY_SPEED = 1.5

# Výpočet:
movement_angle_degrees = 90 + (1 * 90)
                       = 90 + 90
                       = 180°

# Normalizace: 180° < 360°, takže OK

# Převod na radiány:
movement_angle_rad = math.radians(180)
                   = π ≈ 3.142 radians

# Výpočet pohybu:
change_x = math.cos(3.142) * 1.5
         ≈ -1 * 1.5
         = -1.5  (pohyb DOLEVA)

change_y = math.sin(3.142) * 1.5
         ≈ 0 * 1.5
         = 0  (bez pohybu v Y)

VÝSLEDEK: Krab kouká nahoru (90°) a jde pod úhlem 180° (DOLEVA)
```

### Příklad 4: Krab kouká 225° a jde DOPRAVA

```
self.angle = 225°
self.side_direction = +1  (pravý bok)
ENEMY_SPEED = 1

# Výpočet:
movement_angle_degrees = 225 + (1 * 90)
                       = 225 + 90
                       = 315°

# Převod na radiány:
movement_angle_rad = math.radians(315)
                   ≈ 5.498 radians

# Výpočet pohybu:
change_x = math.cos(5.498) * 1
         ≈ 0.707  (pohyb DOPRAVA)

change_y = math.sin(5.498) * 1
         ≈ -0.707  (pohyb NAHORU - matematicky)

VÝSLEDEK: Krab kouká 225° a jde pod úhlem 315° (dolů-doprava)
```

## ORIENTACE ÚHLŮ V ARCADE:

V Arcade (a matematice):

- **0°** = vpravo → (cos=1, sin=0)
- **90°** = nahoru ↑ (cos=0, sin=1) _mathematicky; v Arcade Y roste dolů!_
- **180°** = vlevo ← (cos=-1, sin=0)
- **270°** = dolů ↓ (cos=0, sin=-1) _mathematicky; v Arcade Y roste dolů!_

**DŮLEŽITÉ:** V Arcade Y-osa roste DOLŮ (0 je nahoře, SCREEN_HEIGHT je dole).

- Negativní `change_y` = pohyb NAHORU
- Pozitivní `change_y` = pohyb DOLŮ

Pokud se krab pohybuje "špatně", zkus přičíst offset:

- `self.angle = random_angle + 90` (otočit o 90°)
- Nebo: `change_y = -math.sin(...)` (obrátit Y)
