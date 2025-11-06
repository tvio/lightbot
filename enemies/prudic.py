"""
LightBot - Prudic Enemy
Nepřítel Prudic - těžký nepřítel, který jde přímo na hráče a vydrží 5 hitů
"""
from .base_enemy import BaseEnemy


class Prudic(BaseEnemy):
    """Prudic - těžký nepřítel s 5 životy"""
    
    # Konfigurace Prudice
    ENEMY_TYPE_NAME = "prudic"
    GIF_PATH = "pict/prudic.gif"
    RADIUS = 20
    SPEED = 0.8  # Pomalejší než ostatní
    ANIMATION_FRAME_DURATION = 0.15
    SCALE_MULTIPLIER = 2
    MOVEMENT_TYPE = "player_seeking"  # Jde přímo na hráče
    DIRECTION_CHANGE_TIME_RANGE = [1, 2]  # Často aktualizuje směr k hráči
    MAX_HEALTH = 5  # Vydrží 5 hitů

