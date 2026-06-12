# game_engine.py
import pygame
import os
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_RED, COLOR_BLUE, COLOR_GREEN, COLOR_ORANGE
)
from models import Province, Country, Leader


class GameEngine:
    def __init__(self):
        # 1. Загрузка карты
        self.map_original = None
        self.load_map_asset()

        # 2. Инициализация фракций и лидеров
        self.leader_1 = Leader(
            "Алексей Шахтер",
            "Глава Союза Горняков",
            COLOR_RED,
            "Суровый мужик с мозолистыми руками. Сторонник суровой дисциплины и работы."
        )
        self.leader_2 = Leader(
            "Мэр Василий",
            "Мэр Администрации Округа",
            COLOR_BLUE,
            "Обещает новые детские площадки и стабильность к 2045 году."
        )
        self.leader_3 = Leader(
            "Егерь Михалыч",
            "Лидер Таёжного Братства",
            COLOR_GREEN,
            "Живёт глубоко в лесу, презирает налоги, сотовую связь и любые законы."
        )
        self.leader_4 = Leader(
            "Макар Лысенко",
            "Основатель Макарляндии",
            COLOR_ORANGE,
            "Лидер националистов, монарх Макарляндии"
        )

        self.countries = [
            Country(
                "Союз Горняков",
                COLOR_RED,
                self.leader_1,
                "Пролетариат разрезов и подземных шахт. Склонны решать проблемы кувалдой."
            ),
            Country(
                "Администрация Округа",
                COLOR_BLUE,
                self.leader_2,
                "Профессиональные бюрократы. Мастера написания отчётов о проделанной работе."
            ),
            Country(
                "Таёжное Братство",
                COLOR_GREEN,
                self.leader_3,
                "Самогонщики, охотники и выживальщики. Продают шишки, игнорируют власть."
            ),
            Country(
                "Фурманово — Макарляндия",
                COLOR_ORANGE,
                self.leader_4,
                "Свободное государство. Основывается на национальном монархизме."
            )
        ]

        # 3. Инициализация провинций (полигоны по ориентирам карты 776х1004)
        self.provinces = [
            Province(
                1,
                "Шахтёрский район (Центр)",
                [(300, 420), (460, 410), (490, 520), (370, 590), (280, 520)]
            ),
            Province(
                2,
                "Запрудный (ул. Королёва)",
                [(320, 150), (480, 150), (510, 260), (420, 320), (300, 240)]
            ),
            Province(
                3,
                "Западные холмы (ул. Матросова)",
                [(70, 750), (280, 680), (340, 820), (220, 950), (80, 920)]
            ),
            Province(
                4,
                "Левобережный (ул. Леонова)",
                [(490, 580), (680, 540), (750, 680), (600, 750), (450, 660)]
            ),
            Province(
                5,
                "Восточные Дачи (ул. Гоголя)",
                [(480, 270), (660, 270), (710, 430), (580, 470), (440, 400)]
            )
        ]

        # Первичное распределение стартовых провинций
        self.provinces[0].owner = self.countries[0]  # Шахтерский район -> Горняки
        self.provinces[2].owner = self.countries[0]  # Западные холмы -> Горняки
        self.provinces[1].owner = self.countries[1]  # Запрудный -> Администрация
        self.provinces[4].owner = self.countries[2]  # Восточные Дачи -> Таёжники
        self.provinces[3].owner = self.countries[3]  # Левобережный -> Макарляндия

        for p in self.provinces:
            if p.owner:
                p.owner.provinces.append(p)

        # 4. Состояние камеры (Масштаб и Смещение)
        self.zoom = 0.8
        self.pan_x = 50
        self.pan_y = -100
        self.is_dragging = False
        self.drag_start = (0, 0)

        # 5. Игровой процесс
        self.turn = 1
        self.player_country = None
        self.selected_province = None

    def load_map_asset(self):
        """Пытается загрузить map.png или создает красивую заглушку, если файла нет"""
        if os.path.exists("map.png"):
            self.map_original = pygame.image.load("map.png").convert_alpha()
        else:
            self.map_original = pygame.Surface((800, 1000))
            self.map_original.fill((210, 218, 226))
            pygame.draw.rect(self.map_original, (116, 185, 255), (0, 200, 800, 150))
            font = pygame.font.SysFont("Arial", 24)
            text = font.render("[Сохраните вашу карту как map.png]", True, (45, 52, 54))
            self.map_original.blit(text, (200, 450))

    def select_player_faction(self, chosen_country_name):
        """Устанавливает игроку выбранную страну, остальные провинции нейтрализует"""
        for country in self.countries:
            if country.name == chosen_country_name:
                self.player_country = country
                break

        # Все провинции, не принадлежащие фракции игрока, становятся нейтральными
        for p in self.provinces:
            if p.owner != self.player_country:
                if p.owner:
                    # Убираем провинцию из списка прежней страны
                    if p in p.owner.provinces:
                        p.owner.provinces.remove(p)
                p.owner = None

        # Выбираем первую провинцию игрока по умолчанию
        if self.player_country and self.player_country.provinces:
            self.selected_province = self.player_country.provinces[0]
        else:
            self.selected_province = self.provinces[0]

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                clicked_province = False
                for prov in self.provinces:
                    if prov.is_hovered(event.pos, self.zoom, self.pan_x, self.pan_y):
                        self.selected_province = prov
                        clicked_province = True
                        break

                # Если кликнули мимо провинций и не по интерфейсу, тащим карту
                if not clicked_province and event.pos[0] < SCREEN_WIDTH - 300:
                    self.is_dragging = True
                    self.drag_start = event.pos

            elif event.button == 2:  # Колесико мыши (клик)
                self.is_dragging = True
                self.drag_start = event.pos

            elif event.button == 4:  # Колесико вверх
                self.zoom = min(self.zoom + 0.05, 2.0)
            elif event.button == 5:  # Колесико вниз
                self.zoom = max(self.zoom - 0.05, 0.4)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 2):
                self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                dx = event.pos[0] - self.drag_start[0]
                dy = event.pos[1] - self.drag_start[1]
                self.pan_x += dx
                self.pan_y += dy
                self.drag_start = event.pos

    def next_turn(self):
        self.turn += 1