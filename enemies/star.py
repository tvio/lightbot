"""
LightBot - Star Enemy
Nepřítel hvěždy - přímý pohyb
"""
from .base_enemy import BaseEnemy


class Star(BaseEnemy):
    """Hvězda - nepřítel letící přímo"""
    
    # Konfigurace hvěždy
    ENEMY_TYPE_NAME = "star"
    GIF_PATH = "pict/animated_star_pingpong.gif"
    RADIUS = 12
    SPEED = 1.5  # Hvězda je rychlejší
    ANIMATION_FRAME_DURATION = 0.1  # Hvězda se otáčí rychleji
    SCALE_MULTIPLIER = 1.5
    MOVEMENT_TYPE = "direct"  # Hvězda letí přímo
    DIRECTION_CHANGE_TIME_RANGE = [3, 8]  # Hvězda se otáčí rychleji
