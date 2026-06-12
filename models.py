import pygame
from constants import (
    COLOR_NEUTRAL, EQ_RIFLES, EQ_ARTILLERY, EQ_TRUCKS, EQ_TANKS, BASE_SUPPLY_LIMIT,
    TERRAIN_URBAN, PROD_RIFLES, PROD_NONE
)


class Leader:
    def __init__(self, name, title, portrait_color, bio="", portrait_file=None):
        self.name = name
        self.title = title
        self.portrait_color = portrait_color
        self.bio = bio
        self.portrait_file = portrait_file  # Добавить поле
        self.portrait_cache = None

    def get_portrait(self):
        if self.portrait_cache is None and self.portrait_file:
            from military import load_commander_portrait
            self.portrait_cache = load_commander_portrait(self.portrait_file, self.portrait_color)
        return self.portrait_cache


class Country:
    def __init__(self, name, color, leader, description=""):
        self.name = name
        self.color = color
        self.leader = leader
        self.description = description
        self.provinces = []

        # ХоИ4-ресурсы страны
        self.manpower = 5000
        self.political_power = 150
        self.fuel = 200.0
        self.money = 1000
        self.raw_materials = 100  # Добавлен новый атрибут ресурсов сырья
        self.equipment = {
            EQ_RIFLES: 1000,
            EQ_ARTILLERY: 100,
            EQ_TRUCKS: 50,
            EQ_TANKS: 10
        }

        # Списки воинских структур
        self.divisions = []
        self.division_templates = []
        self.armies = []
        self.commanders = []  # Пул генералов

class Province:
    def __init__(self, id_num, name, polygon):
        self.id = id_num
        self.name = name
        self.polygon = polygon  # Вершины на исходной карте
        self.owner = None  # Ссылка на Country

        # Военные поля
        self.divisions = []  # Войска в провинции
        self.supply_limit = BASE_SUPPLY_LIMIT

        # Добавленные поля Terrain и Экономики
        self.terrain = TERRAIN_URBAN
        self.has_mine = False
        self.workshops = [PROD_RIFLES, PROD_NONE, PROD_NONE]  # На старте 1 активная мастерская и 2 слота пусты

    def get_screen_pos(self, zoom, pan_x, pan_y):
        """Находит приблизительный центр полигона для вывода иконок и текста"""
        xs = [p[0] for p in self.polygon]
        ys = [p[1] for p in self.polygon]
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)
        screen_x = int(center_x * zoom + pan_x)
        screen_y = int(center_y * zoom + pan_y)
        return screen_x, screen_y

    def get_current_supply_weight(self):
        """Суммирует потребление снабжения всеми дивизиями в этой провинции"""
        total = 0.0
        for d in self.divisions:
            stats = d.get_combat_stats()
            total += stats["supply_use"]
        return total

    def is_hovered(self, mouse_pos, zoom, pan_x, pan_y):
        """Проверяет, находится ли курсор внутри полигона провинции (Ray Casting)"""
        mx, my = mouse_pos
        map_x = (mx - pan_x) / zoom
        map_y = (my - pan_y) / zoom

        n = len(self.polygon)
        inside = False
        p1x, p1y = self.polygon[0]
        for i in range(n + 1):
            p2x, p2y = self.polygon[i % n]
            if map_y > min(p1y, p2y):
                if map_y <= max(p1y, p2y):
                    if map_x <= max(p1x, p2x):
                        if p1y != p2y:
                            xints = (map_y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or map_x <= xints:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside