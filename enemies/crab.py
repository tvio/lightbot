"""
LightBot - Crab Enemy
Nepřítel kraba - chůze bokem
"""
from .base_enemy import BaseEnemy


class Crab(BaseEnemy):
    """Krab - nepřítel chůzující bokem s animací"""
    
    # Konfigurace kraba
    ENEMY_TYPE_NAME = "crab"
    GIF_PATH = None  # Načte se z game_config.yaml
    RADIUS = 15
    SPEED = 1
    ANIMATION_FRAME_DURATION = 0.15
    SCALE_MULTIPLIER = 2
    MOVEMENT_TYPE = "sideway"  # Krab chodí bokem
    DIRECTION_CHANGE_TIME_RANGE = [5, 12]  # Náhodně 5-12 sekund
