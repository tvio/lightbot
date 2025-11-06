# Matematika torpéda - Dokumentace algoritmu

## Přehled

Torpédo je inteligentní nepřítel, který:

1. Vyhledává nejbližší minu
2. Pokud není mina, směřuje na hráče
3. Otáčí se plynule (ne okamžitě o 180°)

## 1. Hledání nejbližší miny

### Algoritmus

```
Pro každou minu v seznamu:
    1. Vypočítej vzdálenost k torpédu
    2. Zapamatuj si nejbližší
```

### Matematika

Euklidovská vzdálenost mezi dvěma body:

```
dx = mine.x - torpedo.x
dy = mine.y - torpedo.y
distance = √(dx² + dy²)
```

**Proč to funguje:**

- `dx` a `dy` jsou složky vektoru od torpéda k mině
- Pythagorova věta dává přímou vzdálenost

**Implementace:** `find_closest_mine()`

---

## 2. Výpočet úhlu k cíli

### Algoritmus

```
1. Vypočítaj vektor k cíli (dx, dy)
2. Použij arctangens pro získání úhlu
```

### Matematika

```
dx = target.x - torpedo.x
dy = target.y - torpedo.y
angle = atan2(dy, dx)
```

**Proč `atan2` a ne `atan`:**

- `atan(dy/dx)` funguje pouze pro 2 kvadranty (-90° až +90°)
- `atan2(dy, dx)` funguje pro všech 360° a správně zachází se znaménky
- Vrací úhel v radiánech v rozsahu [-π, π]

**Koordinátní systém:**

```
         +y (90°, π/2)
          |
          |
-x (180°, π) ---+--- +x (0°, 0)
          |
          |
         -y (-90°, -π/2)
```

**Implementace:** `calculate_angle_to_target()`

---

## 3. Plynulé otáčení (nejdůležitější část!)

### Problém

Pokud torpédo letí doprava (0°) a cíl je nalevo (180°), nechceme okamžitou změnu směru. To by vypadalo nerealisticky.

### Řešení: Postupné otáčení s omezenou rychlostí

### Krok 1: Vypočítej rozdíl úhlů

```
angle_diff = target_angle - current_angle
```

**Příklad:**

- Aktuální úhel: 45° (severovýchod)
- Cílový úhel: 135° (severozápad)
- Rozdíl: 135° - 45° = 90°

### Krok 2: Normalizuj do rozsahu [-π, π]

**Proč:** Úhly jsou cyklické! Rozdíl 270° by měl být -90° (kratší cesta).

```python
while angle_diff > π:
    angle_diff -= 2π
while angle_diff < -π:
    angle_diff += 2π
```

**Příklady:**

```
Příklad 1:
- Současný: 10° (0.174 rad)
- Cílový: 350° (6.109 rad)
- Rozdíl: 340° (5.934 rad)
- Po normalizaci: -20° (-0.349 rad)  ← kratší cesta!

Příklad 2:
- Současný: 350° (6.109 rad)
- Cílový: 10° (0.174 rad)
- Rozdíl: -340° (-5.934 rad)
- Po normalizaci: 20° (0.349 rad)  ← kratší cesta!
```

**Vizualizace:**

```
     90°
      |
      |
180°--+--0°/360°
      |
      |
    270°

Z 350° na 10°:
- Po směru hodin: 20° ✓ (kratší)
- Proti směru: 340° ✗ (delší)
```

### Krok 3: Omez maximální rychlost otáčení

```python
max_rotation = MAX_ROTATION_SPEED * delta_time

if abs(angle_diff) <= max_rotation:
    # Jsme blízko → otoč se přímo
    new_angle = target_angle
else:
    # Daleko → otoč se jen o max_rotation
    if angle_diff > 0:
        new_angle = current_angle + max_rotation
    else:
        new_angle = current_angle - max_rotation
```

**Parametry:**

- `MAX_ROTATION_SPEED = 120°/s` (2 radiány/s)
- Při 60 FPS: `delta_time = 1/60 ≈ 0.0167s`
- Max otočení za frame: `120° * 0.0167 = 2°`

**Příklad s postupným otáčením:**

```
Frame 0: current = 0°,   target = 90°,  diff = 90°
         → otoč o 2° → new = 2°

Frame 1: current = 2°,   target = 90°,  diff = 88°
         → otoč o 2° → new = 4°

Frame 2: current = 4°,   target = 90°,  diff = 86°
         → otoč o 2° → new = 6°

...

Frame 44: current = 88°, target = 90°,  diff = 2°
          → otoč o 2° → new = 90° ✓
```

Celkem: ~45 framů při 60 FPS = **0.75 sekundy** pro otočení o 90°.

**Implementace:** `smooth_rotate_towards()`

---

## 4. Aktualizace rychlosti pohybu

Po výpočtu nového úhlu pohybu aktualizujeme rychlostní složky:

```python
change_x = cos(movement_angle) * SPEED
change_y = sin(movement_angle) * SPEED
```

**Matematika:**

- `movement_angle` je úhel v radiánech
- `cos(angle)` dává x-ovou složku jednotkového vektoru
- `sin(angle)` dává y-ovou složku jednotkového vektoru
- Vynásobením rychlostí (`SPEED`) získáme výsledný vektor rychlosti

**Vizualizace:**

```
         y
         ↑
         |    / (change_x, change_y)
         |   /
         |  / speed
         | /θ
         |/___________→ x
        O

change_x = speed * cos(θ)
change_y = speed * sin(θ)

√(change_x² + change_y²) = speed
```

---

## 5. Kompletní update cyklus

### Každý frame (1/60 sekundy):

```
1. Aktualizuj timer pro přehodnocení cíle (každých 0.5s)

2. Najdi cíl:
   a) Hledej nejbližší minu
   b) Pokud není, cílový je hráč

3. Vypočítej úhel k cíli
   angle_to_target = atan2(target_y - my_y, target_x - my_x)

4. Plynule otoč směrem k cíli
   movement_angle = smooth_rotate_towards(angle_to_target, delta_time)

5. Aktualizuj rychlost
   change_x = cos(movement_angle) * SPEED
   change_y = sin(movement_angle) * SPEED

6. Pohni se
   x += change_x
   y += change_y

7. Aktualizuj vizuální rotaci sprite
   sprite_angle = -degrees(movement_angle)
   (záporné protože Arcade používá opačnou konvenci)
```

---

## Parametry pro ladění

### Rychlost otáčení (`MAX_ROTATION_SPEED`)

```
60°/s  → Pomalé, plynulé (1.5s pro 90°)
120°/s → Výchozí (0.75s pro 90°) ✓
240°/s → Rychlé, agilní (0.375s pro 90°)
480°/s → Velmi rychlé (0.1875s pro 90°)
```

### Frekvence přehodnocení cíle (`DIRECTION_CHANGE_TIME_RANGE`)

```
0.1s → Velmi responsivní, může se zdát nervózní
0.5s → Výchozí, dobrá rovnováha ✓
1.0s → Pomalé reakce, torpédo se zdá "líné"
```

### Rychlost pohybu (`SPEED`)

```
0.8  → Pomalé
1.2  → Výchozí ✓
1.5  → Rychlé
2.0  → Velmi rychlé (těžko zasáhnout)
```

---

## Debugging tipy

### Když torpédo osciluje kolem cíle:

- Zvětši `MAX_ROTATION_SPEED` (může se otočit rychleji)
- Zmenši `SPEED` (menší překmit)

### Když torpédo reaguje příliš pomalu:

- Zmenši `DIRECTION_CHANGE_TIME_RANGE` (častější přehodnocení)
- Zvětši `MAX_ROTATION_SPEED` (rychlejší otáčení)

### Když torpédo dělá náhlé pohyby:

- Zmenši `MAX_ROTATION_SPEED` (plynulejší otáčení)
- Zkontroluj normalizaci úhlů (měla by vybrat nejkratší cestu)

### Vizualizace pro debugging:

```python
# Přidej do on_draw() v main.py:
for torpedo in torpedos:
    if torpedo.current_target:
        # Nakresli čáru k cíli
        arcade.draw_line(
            torpedo.center_x, torpedo.center_y,
            torpedo.current_target.center_x,
            torpedo.current_target.center_y,
            arcade.color.RED, 2
        )
```

---

## Rozšíření (budoucí možnosti)

### Predikce pohybu cíle

Místo cílení na aktuální pozici hráče můžeme předpovědět, kde bude:

```python
predicted_x = player.center_x + player.change_x * prediction_time
predicted_y = player.center_y + player.change_y * prediction_time
```

### Vyhýbání se překážkám

Přidat kontrolu kolizí a mírné vychýlení trajektorie.

### Variabilní rychlost

Torpédo by mohlo zrychlovat směrem k cíli:

```python
distance_to_target = ...
speed = base_speed + (max_speed - base_speed) * min(1.0, distance_to_target / activation_range)
```

---

## Souhrn klíčových vzorců

```python
# Vzdálenost
distance = √((x₂ - x₁)² + (y₂ - y₁)²)

# Úhel k cíli
angle = atan2(Δy, Δx)

# Normalizace úhlu do [-π, π]
while angle > π:  angle -= 2π
while angle < -π: angle += 2π

# Omezení rychlosti otáčení
rotation_change = clamp(angle_diff, -max_rot, max_rot)

# Vektor rychlosti z úhlu
vₓ = speed × cos(angle)
vᵧ = speed × sin(angle)
```

---

**Autor:** LightBot AI  
**Verze:** 1.0  
**Datum:** 2025-11-05
