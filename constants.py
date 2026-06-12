# constants.py
import pygame

# Размеры окна
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

# FPS
FPS = 60

# Цветовая палитра
COLOR_BG = (240, 240, 240)
COLOR_PANEL = (45, 52, 54)
COLOR_PANEL_LIGHT = (99, 110, 114)
COLOR_TEXT_LIGHT = (223, 230, 233)
COLOR_TEXT_DARK = (45, 52, 54)
COLOR_ACCENT = (225, 112, 85)
COLOR_ACCENT_HOVER = (253, 150, 68)

# Цвета фракций
COLOR_RED = (192, 57, 43)        # Союз Горняков
COLOR_BLUE = (41, 128, 185)       # Администрация
COLOR_GREEN = (39, 174, 96)       # Таёжное Братство
COLOR_ORANGE = (211, 84, 0)       # Фурманово — Макарляндия
COLOR_NEUTRAL = (127, 140, 141)   # Нейтралы

# Военные параметры
BASE_COMBAT_WIDTH = 80
BASE_SUPPLY_LIMIT = 10
MAX_PLANNING_BONUS = 0.30  # +30% к атаке при полной подготовке

# Типы снаряжения
EQ_RIFLES = "rifles"
EQ_ARTILLERY = "artillery"
EQ_TRUCKS = "trucks"
EQ_TANKS = "tanks"

EQUIPMENT_NAMES = {
    EQ_RIFLES: "Винтовки",
    EQ_ARTILLERY: "Орудия",
    EQ_TRUCKS: "Грузовики",
    EQ_TANKS: "Танки/Тракторы"
}

# Типы ландшафта
TERRAIN_URBAN = "urban"
TERRAIN_FOREST = "forest"
TERRAIN_WATER = "water"

# Типы производства для мастерских
PROD_NONE = "none"
PROD_RIFLES = "rifles"
PROD_ARTILLERY = "artillery"
PROD_TRUCKS = "trucks"
PROD_TANKS = "tanks"