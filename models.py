# models.py
import pygame
from constants import COLOR_NEUTRAL


class Leader:
    def __init__(self, name, title, portrait_color, bio=""):
        self.name = name
        self.title = title
        self.portrait_color = portrait_color  # Цвет для заглушки портрета
        self.bio = bio


class Country:
    def __init__(self, name, color, leader, description=""):
        self.name = name
        self.color = color
        self.leader = leader
        self.description = description
        self.provinces = []


class Province:
    def __init__(self, id_num, name, polygon):
        self.id = id_num
        self.name = name
        self.polygon = polygon  # Список кортежей [(x1, y1), (x2, y2), ...] на исходной карте
        self.owner = None       # Объект класса Country

    def is_hovered(self, mouse_pos, zoom, pan_x, pan_y):
        """Проверяет, находится ли курсор мыши внутри полигона провинции (Ray Casting)"""
        mx, my = mouse_pos
        # Обратное преобразование координат экрана в координаты карты
        map_x = (mx - pan_x) / zoom
        map_y = (my - pan_y) / zoom

        # Алгоритм Ray Casting
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