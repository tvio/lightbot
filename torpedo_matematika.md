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

#### Euklidovská vzdálenost - Základy

Euklidovská vzdálenost je **přímá vzdálenost** mezi dvěma body v rovině. Je to nejkratší cesta, jakou by urazil objekt letící přímo z jednoho bodu na druhý.

**Vzorec:**

```
dx = mine.x - torpedo.x
dy = mine.y - torpedo.y
distance = √(dx² + dy²)
```

#### Proč to funguje: Pythagorova věta

Euklidovská vzdálenost je založena na **Pythagorově větě**, která říká, že v pravoúhlém trojúhelníku platí:

```
a² + b² = c²
```

kde `c` je přepona (nejdelší strana).

**Vizualizace:**

```
        mina (x₂, y₂)
           *
          /|
         / |
        /  | dy = y₂ - y₁
       /   |
      /    |
     *_____|
torpédo    dx = x₂ - x₁
(x₁, y₁)

Vzdálenost = √(dx² + dy²) = přepona trojúhelníku
```

#### Konkrétní příklad výpočtu

**Příklad 1: Jednoduchý případ**

```
Torpédo: (0, 0)
Mina:    (3, 4)

dx = 3 - 0 = 3
dy = 4 - 0 = 4
distance = √(3² + 4²) = √(9 + 16) = √25 = 5
```

**Příklad 2: S desetinnými čísly**

```
Torpédo: (10.5, 20.3)
Mina:    (15.2, 25.8)

dx = 15.2 - 10.5 = 4.7
dy = 25.8 - 20.3 = 5.5
distance = √(4.7² + 5.5²) = √(22.09 + 30.25) = √52.34 ≈ 7.23
```

**Příklad 3: Porovnání více min**

```
Torpédo: (100, 100)

Mina A: (110, 100) → dx=10, dy=0 → distance = √(100 + 0) = 10.0
Mina B: (105, 105) → dx=5, dy=5  → distance = √(25 + 25) = 7.07
Mina C: (100, 110) → dx=0, dy=10 → distance = √(0 + 100) = 10.0

→ Nejblíže je Mina B (7.07)
```

#### Vlastnosti euklidovské vzdálenosti

1. **Symetrie:** Vzdálenost z A do B = vzdálenost z B do A
2. **Nejmenší možná:** Je to nejkratší cesta mezi body
3. **Rotace invariantní:** Nezávisí na orientaci souřadnicového systému
4. **Vždy nezáporná:** Vzdálenost ≥ 0 (rovná se 0 pouze pro stejné body)

#### Alternativní metriky (pro srovnání)

**Manhattan vzdálenost** (L1 norma):

```
distance = |dx| + |dy|
```

- Používá se v mřížkových hrách (šachy, šipky)
- Příklad: (0,0) → (3,4) = |3| + |4| = 7 (vs. euklidovská = 5)

**Chebyshev vzdálenost** (L∞ norma):

```
distance = max(|dx|, |dy|)
```

- Používá se pro pohyb krále v šachu
- Příklad: (0,0) → (3,4) = max(3, 4) = 4

**Proč používáme euklidovskou:**

- Nejrealističtější pro fyzikální pohyb
- Torpédo letí přímo, ne po mřížce
- Přirozené pro 2D/3D prostor

#### Implementační poznámky

**V Pythonu:**

```python
import math

def euclidean_distance(x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)

# Nebo pomocí math.hypot (optimalizovaná verze):
def euclidean_distance_optimized(x1, y1, x2, y2):
    return math.hypot(x2 - x1, y2 - y1)
```

**Optimalizace:** Pokud potřebujeme pouze **porovnávat** vzdálenosti (najít nejbližší), nemusíme počítat odmocninu:

```python
# Místo: distance = √(dx² + dy²)
# Použij: distance_squared = dx² + dy²

# Porovnání vzdáleností:
if distance_squared_A < distance_squared_B:
    # A je blíže
```

Odmocnina je pomalá operace, takže pro hledání minima je toto rychlejší!

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

### Základy trigonometrie: sin, cos, tan a jejich inverzní funkce

#### Jednotková kružnice a trigonometrické funkce

V jednotkové kružnici (poloměr = 1) jsou trigonometrické funkce definovány jako:

```
         y
         ↑
         |    P(x, y)
         |   /|
         |  / |
         | /  | y = sin(θ)
         |/θ  |
    -----+----+----→ x
        O|    | x = cos(θ)
         |    |
         |    |

sin(θ) = y (y-ová souřadnice bodu na kružnici)
cos(θ) = x (x-ová souřadnice bodu na kružnici)
tan(θ) = sin(θ) / cos(θ) = y / x
```

**Důležité:** Tyto funkce berou **úhel jako vstup** a vracejí **hodnotu** (souřadnici nebo poměr).

#### Proč se NEPOUŽÍVÁ sin nebo cos pro výpočet úhlu?

**Problém 1: Nejsou to inverzní funkce**

Sin a cos jsou **funkce**, ne **inverzní funkce**. Potřebujeme opak - máme souřadnice a chceme úhel!

```
❌ ŠPATNĚ:
  Máme: x = 0.707, y = 0.707
  Chceme: úhel θ = ?
  sin(θ) = 0.707 → ale jaký je θ? Musíme použít arcsin!

✓ SPRÁVNĚ:
  Máme: x = 0.707, y = 0.707
  Použijeme: θ = atan2(y, x) = 45°
```

**Problém 2: Arcsin a arccos mají vážné omezení**

I když použijeme **inverzní funkce** (arcsin, arccos), mají problémy:

**Arcsin (inverzní sin):**

```
θ = arcsin(y)
```

- Funguje jen pro **2 kvadranty** (90° až -90°)
- Vyžaduje, aby bod ležel na jednotkové kružnici (x² + y² = 1)
- Nemůže rozlišit úhly v levé polovině kruhu

**Arccos (inverzní cos):**

```
θ = arccos(x)
```

- Funguje jen pro **2 kvadranty** (0° až 180°)
- Vyžaduje, aby bod ležel na jednotkové kružnici
- Nemůže rozlišit úhly v dolní polovině kruhu

**Příklad problému:**

```
Bod A: (0.707, 0.707)  → úhel 45°
Bod B: (-0.707, -0.707) → úhel 225°

arcsin(0.707) = 45° ✓
arcsin(-0.707) = -45° ✗ (mělo by být 225° nebo -135°)

arccos(0.707) = 45° ✓
arccos(-0.707) = 135° ✗ (pro bod B by mělo být 225°)
```

**Problém 3: Vyžadují normalizaci na jednotkovou kružnici**

Sin a cos pracují s body na jednotkové kružnici. Pokud máme bod mimo kružnici, musíme ho nejdřív normalizovat:

```
Bod: (3, 4) - leží mimo jednotkovou kružnici
Vzdálenost: √(3² + 4²) = 5

Normalizace:
  x_norm = 3/5 = 0.6
  y_norm = 4/5 = 0.8

Pak: θ = arcsin(0.8) = 53.13°
```

To je zbytečně složité, když můžeme použít `atan2(4, 3)` přímo!

#### Proč tangens funguje i mimo jednotkovou kružnici?

**Klíčová vlastnost tangens:** Je to **poměr**, ne souřadnice!

```
tan(θ) = sin(θ) / cos(θ) = y / x
```

**Důležité:** Tangens závisí pouze na **poměru** y/x, ne na absolutní vzdálenosti od počátku!

**Vizualizace:**

```
         y
         ↑
         |    P₁(3, 4)
         |   /|
         |  / |
         | /  | 4
         |/θ  |
    -----+----+----→ x
        O|    | 3
         |    |
         |    |
         |    P₂(6, 8)
         |   /|
         |  / |
         | /  | 8
         |/θ  |
    -----+----+----→ x
        O|    | 6

tan(θ) = 4/3 = 8/6 = 1.333...
```

Oba body (3,4) a (6,8) mají **stejný úhel**, protože mají stejný poměr y/x!

**Jak to funguje v praxi:**

```
Máme bod: (100, 200) - libovolné souřadnice, ne na jednotkové kružnici

dx = 100
dy = 200

tan(θ) = dy/dx = 200/100 = 2
θ = atan(2) = 63.43°

Nebo přímo:
θ = atan2(200, 100) = 63.43°
```

**Není potřeba normalizace!** Tangens funguje s libovolnými souřadnicemi.

#### Cotangens (kotangens)

Cotangens je **převrácená hodnota** tangens:

```
cot(θ) = 1 / tan(θ) = cos(θ) / sin(θ) = x / y
```

**Můžeme použít i cotangens:**

```
θ = acot(x / y) = acot(dx / dy)
```

**Problém:** Stejný jako u atan - funguje jen pro 2 kvadranty. Proto se používá `atan2`, ne `acot2`.

#### Jak zjistit směr pomocí tan/cotan bez souřadnic?

**Otázka:** "Jak zjistit směr, když konec trojúhelníku leží mimo jednotkovou kružnici, resp. nemám souřadnice?"

**Odpověď:** Pokud nemáte souřadnice, nemůžete použít žádnou trigonometrickou funkci! Všechny potřebují nějaké vstupní údaje.

**Co potřebujete pro výpočet úhlu:**

1. **Dvě souřadnice** (x₁, y₁) a (x₂, y₂):

   ```
   dx = x₂ - x₁
   dy = y₂ - y₁
   θ = atan2(dy, dx)
   ```

2. **Vzdálenosti a poměr:**

   ```
   Pokud znáte: dx a dy (i když jsou velké)
   Pak: θ = atan2(dy, dx) funguje vždy!
   ```

3. **Pouze poměr:**
   ```
   Pokud znáte pouze: dy/dx (poměr)
   Pak: θ = atan(dy/dx) - ale funguje jen pro 2 kvadranty
   ```

**Příklad s velkými souřadnicemi:**

```
Torpédo: (1000, 2000)
Cíl:     (5000, 8000)

dx = 5000 - 1000 = 4000
dy = 8000 - 2000 = 6000


Vzdálenost: √(4000² + 6000²) = √(16,000,000 + 36,000,000) = √52,000,000 ≈ 7211

Poměr: dy/dx = 6000/4000 = 1.5

θ = atan2(6000, 4000) = atan2(1.5) = 56.31°
```

**Není potřeba normalizovat na jednotkovou kružnici!** `atan2` funguje s libovolnými hodnotami.

#### Srovnání přístupů

**Přístup 1: Sin/Cos (špatně)**

```
❌ Vyžaduje normalizaci na jednotkovou kružnici
❌ arcsin/arccos fungují jen pro 2 kvadranty
❌ Složitější výpočet
```

**Přístup 2: Tan (dobře, ale ne ideálně)**

```
✓ Funguje s libovolnými souřadnicemi
✓ Nevyžaduje normalizaci
✗ atan funguje jen pro 2 kvadranty
```

**Přístup 3: atan2 (nejlepší)**

```
✓ Funguje s libovolnými souřadnicemi
✓ Nevyžaduje normalizaci
✓ Funguje pro všech 360°
✓ Správně zachází se znaménky
```

### Jak funguje `atan` a `atan2`

#### Základní princip: Tangens a arctangens

Tangens úhlu je poměr protilehlé a přilehlé odvěsny:

```
tan(θ) = dy / dx
```

**Arctangens** je **inverzní funkce** k tangens - vrací úhel, jehož tangens je daný poměr:

```
θ = atan(dy / dx)
```

**Důležité:** `atan2` je lepší varianta, která bere obě složky zvlášť a funguje pro celý kruh!

#### Problém s `atan`: Funguje jen pro 2 kvadranty

**Příklad problému:**

```
Případ 1: dx = 1, dy = 1
  tan(θ) = 1/1 = 1
  atan(1) = 45° ✓ (správně)

Případ 2: dx = -1, dy = -1
  tan(θ) = (-1)/(-1) = 1
  atan(1) = 45° ✗ (špatně! Mělo by být 225°)
```

**Proč to selže:**

- `atan` vrací úhel v rozsahu **[-90°, +90°]** (2 kvadranty)
- Nemůže rozlišit úhly v levé polovině kruhu (180°-360°)
- Všechny úhly s opačnými znaménky dávají stejný tangens

**Vizualizace:**

```
        90°
         |
         |
180°-----+-----0°
         |
         |
       270°

atan funguje:  -90° až +90° (pravá polovina)
atan NEFUNGUJE: 90° až 270° (levá polovina)
```

#### Řešení: `atan2(dy, dx)` - funguje pro všech 360°

`atan2` bere **dva parametry** (dy a dx) místo jednoho poměru, takže zná znaménka obou složek:

```python
angle = atan2(dy, dx)  # Vrací úhel v rozsahu [-π, π]
```

**Jak `atan2` funguje:**

```
atan2(dy, dx) = {
  atan(dy/dx)           pokud dx > 0
  atan(dy/dx) + π       pokud dx < 0 a dy ≥ 0
  atan(dy/dx) - π       pokud dx < 0 a dy < 0
  +π/2                  pokud dx = 0 a dy > 0
  -π/2                  pokud dx = 0 a dy < 0
  nedefinováno          pokud dx = 0 a dy = 0
}
```

**Příklady:**

```
dx =  1, dy =  1 → atan2( 1,  1) =  45° (0.785 rad)  ✓
dx = -1, dy =  1 → atan2( 1, -1) = 135° (2.356 rad)  ✓
dx = -1, dy = -1 → atan2(-1, -1) = -135° (-2.356 rad) = 225° ✓
dx =  1, dy = -1 → atan2(-1,  1) = -45° (-0.785 rad) = 315° ✓
dx =  0, dy =  1 → atan2( 1,  0) =  90° (1.571 rad)  ✓
dx =  1, dy =  0 → atan2( 0,  1) =   0° (0.000 rad)  ✓
```

**Koordinátní systém:**

```
         +y (90°, π/2)
          |
          |
-x (180°, π) ---+--- +x (0°, 0)
          |
          |
         -y (-90°, -π/2)

atan2 pokrývá celý kruh: [-π, π] = [-180°, 180°]
```

### Proč počítáme úhel k cíli, když už máme aktuální směr?

**Důležitá otázka:** "Mám `current_angle` (aktuální směr pohybu), proč musím počítat `target_angle` znovu?"

#### Odpověď: Cíl se mění!

**Dva různé úhly:**

1. **`current_angle`** = směr, kterým torpédo **právě letí**
2. **`target_angle`** = směr, kterým torpédo **má letět** (k aktuálnímu cíli)

**Proč se cíl mění:**

1. **Miny se pohybují** - torpédo musí sledovat pohybující se minu
2. **Hráč se pohybuje** - když není mina, torpédo sleduje hráče
3. **Najde se bližší mina** - každých 0.5s se přehodnocuje, která mina je nejblíž
4. **Mina zmizí** - když torpédo minu zničí, musí přepnout na jiný cíl

**Příklad situace:**

```
Frame 0:
  Torpédo: (100, 100), letí směrem 45° (severovýchod)
  Mina A: (150, 150) - vzdálenost 70.7
  Mina B: (200, 100) - vzdálenost 100.0
  → Cíl: Mina A
  → target_angle = atan2(150-100, 150-100) = 45°
  → current_angle = 45° (už letí správně)

Frame 30 (0.5s později):
  Torpédo: (130, 130), stále letí směrem 45°
  Mina A: (150, 150) - vzdálenost 28.3 (blíž!)
  Mina B: (200, 100) - vzdálenost 72.1 (teď blíž než A!)
  → Cíl se změnil na Mina B!
  → target_angle = atan2(100-130, 200-130) = atan2(-30, 70) ≈ -23°
  → current_angle = 45° (stále letí starým směrem)
  → Musí se otočit z 45° na -23° (rozdíl 68°)
```

**Vizualizace:**

```
Frame 0:                    Frame 30:

    Mina A (150,150)           Mina A (150,150)
         *                           *
         |                           |
         | 45°                       |
    Torpédo (100,100)          Torpédo (130,130)
         |                           |
         |                           | -23°
         |                           |
                            Mina B (200,100)
                                 *

Cíl: Mina A                  Cíl: Mina B (změnil se!)
```

#### Proč si neuložit předchozí hodnotu?

**Můžeme si uložit `target_angle` z předchozího framu, ALE:**

1. **Cíl se mění** - každých 0.5s se přehodnocuje, která mina je nejblíž
2. **Cíl se pohybuje** - i když cíl zůstane stejný, jeho pozice se mění
3. **Pozice torpéda se mění** - i když cíl stojí, torpédo se pohybuje, takže úhel se mění

**Příklad, kdy by uložení pomohlo, ale nestačí:**

```
Frame 0:
  Torpédo: (100, 100)
  Cíl: (200, 100)
  target_angle = atan2(0, 100) = 0° (doprava)
  → Uložíme: last_target_angle = 0°

Frame 1:
  Torpédo: (101, 100) - posunulo se doprava
  Cíl: (200, 100) - stále na stejném místě
  → Můžeme použít last_target_angle = 0°?
  → ANO, ale jen pokud cíl nezměnil pozici!

Frame 1 (realita):
  Torpédo: (101, 100)
  Cíl: (200, 100) - stále stejný
  target_angle = atan2(0, 99) = 0° (stejné)
  → Úhel se nezměnil, ale museli jsme to zkontrolovat!
```

**Kdy uložení NEPOMŮŽE:**

```
Frame 0:
  Torpédo: (100, 100)
  Cíl: (200, 100)
  target_angle = 0°

Frame 1:
  Torpédo: (101, 100)
  Cíl: (201, 100) - cíl se také posunul!
  → last_target_angle = 0° je stále správný
  → ALE: co když cíl zrychlil nebo změnil směr?

Frame 1 (realita):
  Torpédo: (101, 100)
  Cíl: (201, 100) - posunul se doprava
  target_angle = atan2(0, 100) = 0° (stejné)
  → Musíme přepočítat, abychom to ověřili!
```

**Závěr:** I když bychom mohli optimalizovat a ukládat předchozí hodnotu, je **bezpečnější a jednodušší** počítat úhel znovu, protože:

- Výpočet `atan2` je rychlý
- Zajišťuje přesnost i když se cíl pohybuje
- Kód je jednodušší a méně náchylný k chybám

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
