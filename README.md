# LightBot

Hra vytvořená pomocí Python Arcade frameworku.

📖 **Příručka hry:** Viz [PRIRUCKA.md](PRIRUCKA.md) pro kompletní popis hry, nepřátel, bonusů a strategie.

## Požadavky

- Python 3.13 nebo vyšší
- `uv` package manager
- Arcade 3.3.3 nebo vyšší
- PyYAML 6.0.3 nebo vyšší

## Instalace

### Windows

1. **Nainstaluj Python 3.13+**
   - Stáhni z [python.org](https://www.python.org/downloads/)
   - Při instalaci zaškrtni "Add Python to PATH"

2. **Nainstaluj uv**
   ```powershell
   # Pomocí PowerShell (spusť jako administrátor)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Nebo pomocí pip
   pip install uv
   ```

3. **Naklonuj nebo stáhni projekt**
   ```powershell
   git clone <repository-url>
   cd lightbot
   ```

4. **Nainstaluj závislosti**
   ```powershell
   uv sync
   ```

5. **Spusť hru**
   ```powershell
   uv run python main.py
   ```

### Linux

1. **Nainstaluj Python 3.13+**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3.13 python3.13-venv python3-pip
   
   # Fedora
   sudo dnf install python3.13 python3-pip
   
   # Arch Linux
   sudo pacman -S python python-pip
   ```

2. **Nainstaluj uv**
   ```bash
   # Pomocí curl
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Nebo pomocí pip
   pip install uv
   ```

3. **Naklonuj nebo stáhni projekt**
   ```bash
   git clone <repository-url>
   cd lightbot
   ```

4. **Nainstaluj závislosti**
   ```bash
   uv sync
   ```

5. **Spusť hru**
   ```bash
   uv run python main.py
   ```

### macOS

1. **Nainstaluj Python 3.13+**
   ```bash
   # Pomocí Homebrew (doporučeno)
   brew install python@3.13
   
   # Nebo stáhni z python.org
   ```

2. **Nainstaluj uv**
   ```bash
   # Pomocí curl
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Nebo pomocí pip
   pip install uv
   ```

3. **Naklonuj nebo stáhni projekt**
   ```bash
   git clone <repository-url>
   cd lightbot
   ```

4. **Nainstaluj závislosti**
   ```bash
   uv sync
   ```

5. **Spusť hru**
   ```bash
   uv run python main.py
   ```



## Struktura projektu

- `main.py` - hlavní vstupní bod hry
- `player.py` - třídy hráče, min a bonusů
- `enemies/` - třídy nepřátel (BaseEnemy, Crab, Star, Torpedo, Prudic)
- `pict/` - sprite sheety a obrázky
- `music/` - hudební soubory
- `game_config.yaml` - konfigurace hry
- `infrastruktura.py` - sdílené utility funkce

## Ovládání

- **A+D** nebo **Šipky doleva doprava** - otáčení děla
- **Q** nebo **Enter** - aktivace světelné bomby
- **Pravé tlačítko myši** - položení miny
- **Levé tlačítko myši** - výstřel laserem ve dne, v noci shockwave


