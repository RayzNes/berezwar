# main.py
import sys
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, COLOR_PANEL,
    COLOR_TEXT_LIGHT, COLOR_TEXT_DARK, COLOR_ACCENT, COLOR_NEUTRAL
)
from game_engine import GameEngine
from ui_elements import Button


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("BerezovskyMats")
        self.clock = pygame.time.Clock()

        # Шрифты
        self.font_title = pygame.font.SysFont("Arial", 36, bold=True)
        self.font_main = pygame.font.SysFont("Arial", 18)
        self.font_ui = pygame.font.SysFont("Arial", 15)
        self.font_small = pygame.font.SysFont("Arial", 13)

        # Состояния игры: MAIN_MENU, FACTION_SELECT, GAME, SETTINGS, CREDITS
        self.state = "MAIN_MENU"

        # Движок игры
        self.game = None

        # Кнопки меню
        self.menu_buttons = [
            Button(362, 200, 300, 50, "Новая игра", self.font_main),
            Button(362, 270, 300, 50, "Загрузить игру", self.font_main),
            Button(362, 340, 300, 50, "Настройки", self.font_main),
            Button(362, 410, 300, 50, "Авторы", self.font_main),
            Button(362, 480, 300, 50, "Выйти", self.font_main)
        ]

        # Кнопки Настроек и Авторов
        self.back_button = Button(362, 600, 300, 50, "Назад в меню", self.font_main)

        # Кнопки выбора фракции
        self.faction_buttons = []

        # Кнопки игрового процесса
        self.game_ui_buttons = []

    def open_faction_select(self):
        """Инициализирует игровой движок и переводит игру в состояние выбора фракции"""
        self.game = GameEngine()
        self.state = "FACTION_SELECT"

        # Генерируем кнопки выбора для каждой фракции
        self.faction_buttons = []
        card_width = 210
        gap = 35
        start_x = 35

        for idx, country in enumerate(self.game.countries):
            btn_x = start_x + idx * (card_width + gap)
            btn = Button(btn_x + 15, 590, 180, 45, f"Выбрать", self.font_main, bg_color=country.color)
            # Прикрепим ссылку на страну прямо к кнопке для упрощения
            btn.target_country = country
            self.faction_buttons.append(btn)

    def draw_text_wrap(self, text, rect, font, color):
        """Позволяет рисовать текст с автоматическим переносом строк внутри области Rect"""
        words = text.split(' ')
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] < rect.width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        lines.append(' '.join(current_line))

        y = rect.top
        for line in lines:
            if y + font.get_linesize() > rect.bottom:
                break
            line_surf = font.render(line, True, color)
            self.screen.blit(line_surf, (rect.left, y))
            y += font.get_linesize() + 2

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

                # Менеджер экранов
                if self.state == "MAIN_MENU":
                    for idx, btn in enumerate(self.menu_buttons):
                        if btn.handle_event(event):
                            if idx == 0:  # Новая игра -> выбор фракции
                                self.open_faction_select()
                            elif idx == 1:  # Загрузить (заглушка)
                                pass
                            elif idx == 2:  # Настройки
                                self.state = "SETTINGS"
                            elif idx == 3:  # Авторы
                                self.state = "CREDITS"
                            elif idx == 4:  # Выйти
                                running = False

                elif self.state == "FACTION_SELECT":
                    if self.back_button.handle_event(event):
                        self.state = "MAIN_MENU"
                    for btn in self.faction_buttons:
                        if btn.handle_event(event):
                            # Игрок выбрал фракцию
                            self.game.select_player_faction(btn.target_country.name)
                            # Инициализируем кнопку пропуска хода
                            self.game_ui_buttons = [
                                Button(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 80, 260, 50, "Пропустить ход",
                                       self.font_main,
                                       bg_color=COLOR_ACCENT)
                            ]
                            self.state = "GAME"

                elif self.state in ("SETTINGS", "CREDITS"):
                    if self.back_button.handle_event(event):
                        self.state = "MAIN_MENU"

                elif self.state == "GAME":
                    self.game.handle_input(event)
                    for btn in self.game_ui_buttons:
                        if btn.handle_event(event):
                            if btn.text == "Пропустить ход":
                                self.game.next_turn()

            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def draw(self):
        self.screen.fill(COLOR_BG)

        if self.state == "MAIN_MENU":
            title_surf = self.font_title.render("Березовские войны", True, COLOR_TEXT_DARK)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(title_surf, title_rect)

            for btn in self.menu_buttons:
                btn.draw(self.screen)

        elif self.state == "FACTION_SELECT":
            self.draw_faction_select_screen()

        elif self.state == "SETTINGS":
            title_surf = self.font_title.render("Настройки игры", True, COLOR_TEXT_DARK)
            self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))

            text = self.font_main.render("Звук: Выкл (Заглушка)", True, COLOR_TEXT_DARK)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 250))
            self.back_button.draw(self.screen)

        elif self.state == "CREDITS":
            title_surf = self.font_title.render("Авторы проекта", True, COLOR_TEXT_DARK)
            self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))

            text_1 = self.font_main.render("Разработчик: Mats Game", True, COLOR_TEXT_DARK)
            text_2 = self.font_main.render("Карта: Пос. Шахты «Берёзовская»", True, COLOR_TEXT_DARK)
            self.screen.blit(text_1, (SCREEN_WIDTH // 2 - text_1.get_width() // 2, 250))
            self.screen.blit(text_2, (SCREEN_WIDTH // 2 - text_2.get_width() // 2, 300))
            self.back_button.draw(self.screen)

        elif self.state == "GAME":
            self.draw_game_screen()

        pygame.display.flip()

    def draw_faction_select_screen(self):
        """Отрисовка экрана выбора фракции с карточками"""
        title_surf = self.font_title.render("Выберите свою фракцию", True, COLOR_TEXT_DARK)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title_surf, title_rect)

        card_width = 210
        card_height = 480
        gap = 35
        start_x = 35
        y = 100

        for idx, country in enumerate(self.game.countries):
            x = start_x + idx * (card_width + gap)
            card_rect = pygame.Rect(x, y, card_width, card_height)

            # Фоновая подложка карточки
            pygame.draw.rect(self.screen, COLOR_PANEL, card_rect, border_radius=8)
            pygame.draw.rect(self.screen, country.color, card_rect, width=3, border_radius=8)

            # Название фракции
            name_rect = pygame.Rect(x + 10, y + 15, card_width - 20, 50)
            self.draw_text_wrap(country.name, name_rect, self.font_main, COLOR_TEXT_LIGHT)

            # Портрет лидера (заглушка)
            portrait_rect = pygame.Rect(x + 45, y + 70, 120, 130)
            pygame.draw.rect(self.screen, country.leader.portrait_color, portrait_rect, border_radius=4)
            pygame.draw.rect(self.screen, COLOR_TEXT_LIGHT, portrait_rect, width=2, border_radius=4)

            # Отрисовка инициалов лидера по центру заглушки
            init_surf = self.font_title.render(country.leader.name[0], True, COLOR_TEXT_LIGHT)
            init_rect = init_surf.get_rect(center=portrait_rect.center)
            self.screen.blit(init_surf, init_rect)

            # Имя Лидера
            leader_name_rect = pygame.Rect(x + 10, y + 210, card_width - 20, 45)
            self.draw_text_wrap(country.leader.name, leader_name_rect, self.font_ui, COLOR_ACCENT)

            # Описание фракции
            desc_rect = pygame.Rect(x + 10, y + 260, card_width - 20, 150)
            self.draw_text_wrap(country.description, desc_rect, self.font_small, COLOR_TEXT_LIGHT)

            # Кнопка Выбора
            self.faction_buttons[idx].draw(self.screen)

        # Кнопка возврата в меню
        self.back_button.rect.y = 620
        self.back_button.draw(self.screen)

    def draw_game_screen(self):
        # 1. Отрисовка карты с учетом масштабирования и смещения
        m_width = int(self.game.map_original.get_width() * self.game.zoom)
        m_height = int(self.game.map_original.get_height() * self.game.zoom)

        scaled_map = pygame.transform.scale(self.game.map_original, (m_width, m_height))
        self.screen.blit(scaled_map, (self.game.pan_x, self.game.pan_y))

        # 2. Отрисовка полупрозрачных полигонов провинций
        for prov in self.game.provinces:
            # Превращаем оригинальные вершины полигона в экранные координаты
            screen_poly = []
            for px, py in prov.polygon:
                sx = int(px * self.game.zoom + self.game.pan_x)
                sy = int(py * self.game.zoom + self.game.pan_y)
                screen_poly.append((sx, sy))

            color = prov.owner.color if prov.owner else COLOR_NEUTRAL

            # Нахождение границ полигона для локального буфера (Pygame требует буфер для RGBA)
            xs = [p[0] for p in screen_poly]
            ys = [p[1] for p in screen_poly]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            w, h = max_x - min_x + 2, max_y - min_y + 2

            if w > 0 and h > 0:
                temp_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                local_poly = [(p[0] - min_x, p[1] - min_y) for p in screen_poly]

                # Рисуем полупрозрачную заливку
                alpha_color = (color[0], color[1], color[2], 110)  # Альфа = 110
                pygame.draw.polygon(temp_surf, alpha_color, local_poly)
                self.screen.blit(temp_surf, (min_x, min_y))

                # Проверка наведения курсора для изменения стиля границы
                is_hovered = prov.is_hovered(pygame.mouse.get_pos(), self.game.zoom, self.game.pan_x, self.game.pan_y)

                # Определение цвета и толщины границы
                if self.game.selected_province == prov:
                    outline_color = (241, 196, 15)  # Выбранная: Золотой
                    width = 3
                elif is_hovered:
                    outline_color = (253, 150, 68)  # Наведение: Оранжевый акцент
                    width = 2
                else:
                    outline_color = (255, 255, 255)  # Обычный: Белый
                    width = 1

                pygame.draw.polygon(self.screen, outline_color, screen_poly, width)

        # 3. Боковая информационная панель (справа)
        panel_rect = pygame.Rect(SCREEN_WIDTH - 300, 0, 300, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect)
        pygame.draw.line(self.screen, (0, 0, 0), (SCREEN_WIDTH - 300, 0), (SCREEN_WIDTH - 300, SCREEN_HEIGHT), 2)

        # Текущий ход
        turn_text = self.font_title.render(f"Ход: {self.game.turn}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(turn_text, (SCREEN_WIDTH - 280, 20))

        # Выбранная провинция
        prov = self.game.selected_province
        if prov:
            prov_title = self.font_main.render(prov.name, True, COLOR_ACCENT)
            self.screen.blit(prov_title, (SCREEN_WIDTH - 280, 80))

            owner_name = prov.owner.name if prov.owner else "Нейтральная территория"
            owner_text = self.font_ui.render(f"Владелец: {owner_name}", True, COLOR_TEXT_LIGHT)
            self.screen.blit(owner_text, (SCREEN_WIDTH - 280, 120))

            if prov.owner:
                leader = prov.owner.leader
                leader_title = self.font_ui.render(f"Лидер: {leader.name}", True, COLOR_TEXT_LIGHT)
                leader_role = self.font_ui.render(f"({leader.title})", True, (180, 189, 196))

                self.screen.blit(leader_title, (SCREEN_WIDTH - 280, 155))
                self.screen.blit(leader_role, (SCREEN_WIDTH - 280, 175))

                # Портрет лидера
                portrait_rect = pygame.Rect(SCREEN_WIDTH - 280, 210, 120, 150)
                pygame.draw.rect(self.screen, leader.portrait_color, portrait_rect)
                pygame.draw.rect(self.screen, COLOR_TEXT_LIGHT, portrait_rect, 2)

                # Инициал лидера на портрете
                initials = self.font_title.render(leader.name[0], True, COLOR_TEXT_LIGHT)
                initials_rect = initials.get_rect(center=portrait_rect.center)
                self.screen.blit(initials, initials_rect)

                # Краткое описание лидера на панели
                bio_rect = pygame.Rect(SCREEN_WIDTH - 280, 380, 260, 150)
                self.draw_text_wrap(leader.bio, bio_rect, self.font_small, COLOR_TEXT_LIGHT)

        # Рисуем игровые кнопки (например, Пропустить ход)
        for btn in self.game_ui_buttons:
            btn.draw(self.screen)


if __name__ == "__main__":
    app = App()
    app.run()