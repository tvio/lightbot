"""
LightBot - Star Enemy
Nepřítel hvěždy - přímý pohyb
"""
from .base_enemy import BaseEnemy


class Star(BaseEnemy):
    """Hvězda - nepřítel letící přímo"""
    
    # Konfigurace hvěždy
    ENEMY_TYPE_NAME = "star"
    GIF_PATH = None  # Načte se z game_config.yaml
    RADIUS = 12
    SPEED = 1  # Hvězda je rychlejší
    ANIMATION_FRAME_DURATION = 0.15  # Hvězda se otáčí pomaleji (50% pomalejší)
    SCALE_MULTIPLIER = 2.25  # Hvězda je větší (50% větší)
    MOVEMENT_TYPE = "direct"  # Hvězda letí přímo
    DIRECTION_CHANGE_TIME_RANGE = [3, 8]  # Hvězda se otáčí rychleji
