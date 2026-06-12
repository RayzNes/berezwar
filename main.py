# main.py
import sys
import pygame
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, COLOR_BG, COLOR_PANEL,
    COLOR_TEXT_LIGHT, COLOR_TEXT_DARK, COLOR_ACCENT, COLOR_NEUTRAL,
    EQ_RIFLES, EQ_ARTILLERY, EQ_TRUCKS, EQ_TANKS, EQUIPMENT_NAMES
)
from game_engine import GameEngine
from ui_elements import Button


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("BerezovskyWars")
        self.clock = pygame.time.Clock()

        # Шрифты
        self.font_title = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_main = pygame.font.SysFont("Arial", 16)
        self.font_ui = pygame.font.SysFont("Arial", 14)
        self.font_small = pygame.font.SysFont("Arial", 12)

        # Состояния: MAIN_MENU, FACTION_SELECT, GAME, DESIGNER, SETTINGS, CREDITS, CHEAT_MENU
        self.state = "MAIN_MENU"
        self.previous_state = "GAME"  # Для возврата из чит-меню

        # Движок игры
        self.game = None

        # Кнопки главного меню
        self.menu_buttons = [
            Button(362, 200, 300, 50, "Новая игра", self.font_main),
            Button(362, 270, 300, 50, "Загрузить игру", self.font_main),
            Button(362, 340, 300, 50, "Настройки", self.font_main),
            Button(362, 410, 300, 50, "Авторы", self.font_main),
            Button(362, 480, 300, 50, "Выйти", self.font_main)
        ]

        self.back_button = Button(362, 650, 300, 45, "Назад в меню", self.font_main)

        # Переменные конструктора шаблонов (DESIGNER)
        self.designer_buttons = []

        # Чит-меню кнопки
        self.cheat_buttons = []

        # Настройки модального окна наций (ПКМ)
        self.country_modal_active = False
        self.selected_modal_country = None
        self.country_modal_rect = None
        self.modal_close_btn = None
        self.modal_war_btn = None

    def open_faction_select(self):
        self.game = GameEngine()
        self.state = "FACTION_SELECT"

        self.faction_buttons = []
        card_width = 210
        gap = 35
        start_x = 35

        for idx, country in enumerate(self.game.countries):
            btn_x = start_x + idx * (card_width + gap)
            btn = Button(btn_x + 15, 590, 180, 45, "Выбрать", self.font_main, bg_color=country.color)
            btn.target_country = country
            self.faction_buttons.append(btn)

    def draw_text_wrap(self, text, rect, font, color):
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

    def init_designer_screen(self):
        self.state = "DESIGNER"
        # Генерируем кнопки для редактора шаблона дивизии
        self.designer_buttons = [
            Button(50, 600, 250, 45, "Добавить Пехоту (-100 Рифл)", self.font_ui),
            Button(310, 600, 250, 45, "Добавить Артиллерию (-36 Арт)", self.font_ui),
            Button(570, 600, 250, 45, "Добавить Бронеотряд (-40 Танк)", self.font_ui),
            Button(50, 660, 250, 45, "Очистить шаблон", self.font_ui),
            Button(720, 660, 250, 45, "Назад в игру", self.font_main)
        ]

    def init_cheat_menu(self):
        self.previous_state = self.state
        self.state = "CHEAT_MENU"
        self.cheat_buttons = [
            Button(362, 180, 300, 45, "+10000 Людей (Manpower)", self.font_main),
            Button(362, 240, 300, 45, "+500 Полит. Власти", self.font_main),
            Button(362, 300, 300, 45, "Захватить все провинции", self.font_main),
            Button(362, 360, 300, 45, "Супер-Оружие (+10k снабж.)", self.font_main),
            Button(362, 420, 300, 45, "Вылечить армию (100% Орг)", self.font_main),
            Button(362, 500, 300, 45, "Закрыть чит-меню", self.font_main)
        ]

    def execute_cheat(self, text):
        if not self.game or not self.game.player_country:
            return

        country = self.game.player_country
        if "Manpower" in text:
            country.manpower += 10000
        elif "Полит." in text:
            country.political_power += 500
        elif "Захватить" in text:
            for p in self.game.provinces:
                if p.owner and p.owner != country:
                    p.owner.provinces.remove(p)
                p.owner = country
                if p not in country.provinces:
                    country.provinces.append(p)
            self.game.selected_province = self.game.provinces[0]
        elif "Супер-Оружие" in text:
            country.equipment[EQ_RIFLES] += 10000
            country.equipment[EQ_ARTILLERY] += 10000
            country.equipment[EQ_TRUCKS] += 10000
            country.equipment[EQ_TANKS] += 10000
        elif "Вылечить" in text:
            for d in country.divisions:
                d.organization = d.max_organization
                d.manpower = d.max_manpower
                d.strength = 1.0

    def open_country_info_modal(self, country):
        """Инициализирует и открывает модальное окно наций"""
        self.country_modal_active = True
        self.selected_modal_country = country

        modal_w, modal_h = 550, 450
        modal_x = (SCREEN_WIDTH - modal_w) // 2
        modal_y = (SCREEN_HEIGHT - modal_h) // 2
        self.country_modal_rect = pygame.Rect(modal_x, modal_y, modal_w, modal_h)

        self.modal_close_btn = Button(
            modal_x + modal_w - 120, modal_y + modal_h - 55, 100, 35, "Закрыть", self.font_ui, bg_color=(192, 57, 43)
        )

        if country != self.game.player_country:
            self.modal_war_btn = Button(
                modal_x + 20, modal_y + modal_h - 55, 180, 35, "Объявить войну", self.font_ui, bg_color=(211, 84, 0)
            )
        else:
            self.modal_war_btn = None

    def declare_war_on_country(self, country):
        """Выполняет декларацию агрессии в сторону другой нации"""
        print(f"[ДИПЛОМАТИЯ]: Объявлена война стране {country.name}!")
        self.country_modal_active = False

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.KEYDOWN:
                    # Нажатие на тильду ~ (ё) вызывает чит-меню
                    if event.key in (pygame.K_BACKQUOTE, 167):
                        if self.state != "CHEAT_MENU":
                            self.init_cheat_menu()
                        else:
                            self.state = self.previous_state

                # Главное меню
                if self.state == "MAIN_MENU":
                    for idx, btn in enumerate(self.menu_buttons):
                        if btn.handle_event(event):
                            if idx == 0:
                                self.open_faction_select()
                            elif idx == 2:
                                self.state = "SETTINGS"
                            elif idx == 3:
                                self.state = "CREDITS"
                            elif idx == 4:
                                running = False

                # Выбор фракции
                elif self.state == "FACTION_SELECT":
                    if self.back_button.handle_event(event):
                        self.state = "MAIN_MENU"
                    for btn in self.faction_buttons:
                        if btn.handle_event(event):
                            self.game.select_player_faction(btn.target_country.name)
                            self.game_ui_buttons = [
                                Button(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 70, 260, 45, "Пропустить ход",
                                       self.font_main, bg_color=COLOR_ACCENT),
                                Button(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 125, 260, 45, "Конструктор дивизий",
                                       self.font_main),
                                Button(SCREEN_WIDTH - 280, SCREEN_HEIGHT - 180, 260, 45, "Нанять див. (-Template)",
                                       self.font_main)
                            ]
                            self.state = "GAME"

                elif self.state in ("SETTINGS", "CREDITS"):
                    if self.back_button.handle_event(event):
                        self.state = "MAIN_MENU"

                # Чит меню
                elif self.state == "CHEAT_MENU":
                    for btn in self.cheat_buttons:
                        if btn.handle_event(event):
                            if "Закрыть" in btn.text:
                                self.state = self.previous_state
                            else:
                                self.execute_cheat(btn.text)

                # Редактор дивизий
                elif self.state == "DESIGNER":
                    country = self.game.player_country
                    template = country.division_templates[0] if country else None
                    for btn in self.designer_buttons:
                        if btn.handle_event(event):
                            if "Пехоту" in btn.text and template:
                                template.add_battalion(self.game.infantry_b)
                            elif "Артиллерию" in btn.text and template:
                                template.add_battalion(self.game.artillery_b)
                            elif "Бронеотряд" in btn.text and template:
                                template.add_battalion(self.game.tank_b)
                            elif "Очистить" in btn.text and template:
                                template.battalions = []
                            elif "Назад" in btn.text:
                                self.state = "GAME"

                # Игровой процесс
                elif self.state == "GAME":
                    if self.country_modal_active:
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            # Проверяем клик вне границ модального окна
                            if not self.country_modal_rect.collidepoint(event.pos):
                                self.country_modal_active = False
                            else:
                                if self.modal_close_btn.handle_event(event):
                                    self.country_modal_active = False
                                elif self.modal_war_btn and self.modal_war_btn.handle_event(event):
                                    self.declare_war_on_country(self.selected_modal_country)
                        continue  # Блокируем остальные игровые действия, пока открыта карточка нации

                    # Обычный инпут в игре
                    self.game.handle_input(event)

                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if event.button == 3:  # ПКМ (Правый клик)
                            clicked_prov = None
                            for prov in self.game.provinces:
                                if prov.is_hovered(event.pos, self.game.zoom, self.game.pan_x, self.game.pan_y):
                                    clicked_prov = prov
                                    break

                            if clicked_prov:
                                # Если у игрока выделена дивизия и целевая провинция не совпадает с текущей -> начертить план
                                if self.game.selected_division and clicked_prov != self.game.selected_division.province:
                                    self.game.selected_division.target_province = clicked_prov
                                else:
                                    # Иначе открыть карточку страны-владельца
                                    if clicked_prov.owner:
                                        self.open_country_info_modal(clicked_prov.owner)

                    # Проверка нажатия игровых кнопок на правой панели
                    for btn in self.game_ui_buttons:
                        if btn.handle_event(event):
                            if "Пропустить" in btn.text:
                                self.game.next_turn()
                                self.game.selected_division = None
                            elif "Конструктор" in btn.text:
                                self.init_designer_screen()
                            elif "Нанять" in btn.text:
                                if self.game.selected_province and self.game.selected_province.owner == self.game.player_country:
                                    template = self.game.player_country.division_templates[0]
                                    self.game.recruit_division(template, self.game.selected_province)

            self.draw()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def draw(self):
        self.screen.fill(COLOR_BG)

        if self.state == "MAIN_MENU":
            title_surf = self.font_title.render("БЕРЕЗОВСКИЕ ВОЙНЫ", True, COLOR_TEXT_DARK)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100))
            self.screen.blit(title_surf, title_rect)
            for btn in self.menu_buttons:
                btn.draw(self.screen)

        elif self.state == "FACTION_SELECT":
            self.draw_faction_select_screen()

        elif self.state == "SETTINGS":
            title_surf = self.font_title.render("Настройки", True, COLOR_TEXT_DARK)
            self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))
            self.back_button.rect.y = 600
            self.back_button.draw(self.screen)

        elif self.state == "CREDITS":
            title_surf = self.font_title.render("Авторы проекта", True, COLOR_TEXT_DARK)
            self.screen.blit(title_surf, (SCREEN_WIDTH // 2 - title_surf.get_width() // 2, 100))
            text_1 = self.font_main.render("Создатель: Mats Game", True, COLOR_TEXT_DARK)
            self.screen.blit(text_1, (SCREEN_WIDTH // 2 - text_1.get_width() // 2, 250))
            self.back_button.rect.y = 600
            self.back_button.draw(self.screen)

        elif self.state == "DESIGNER":
            self.draw_designer_screen()

        elif self.state == "CHEAT_MENU":
            self.draw_cheat_menu_screen()

        elif self.state == "GAME":
            self.draw_game_screen()

        pygame.display.flip()

    def draw_faction_select_screen(self):
        title_surf = self.font_title.render("Выберите сторону конфликта", True, COLOR_TEXT_DARK)
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

            pygame.draw.rect(self.screen, COLOR_PANEL, card_rect, border_radius=8)
            pygame.draw.rect(self.screen, country.color, card_rect, width=3, border_radius=8)

            name_rect = pygame.Rect(x + 10, y + 15, card_width - 20, 50)
            self.draw_text_wrap(country.name, name_rect, self.font_main, COLOR_TEXT_LIGHT)

            portrait_rect = pygame.Rect(x + 45, y + 70, 120, 130)
            pygame.draw.rect(self.screen, country.leader.portrait_color, portrait_rect, border_radius=4)
            pygame.draw.rect(self.screen, COLOR_TEXT_LIGHT, portrait_rect, width=2, border_radius=4)

            portrait = country.leader.get_portrait()
            if portrait:
                self.screen.blit(portrait, (x + 45, y + 70))
            else:
                # fallback - первая буква
                init_surf = self.font_title.render(country.leader.name[0], True, COLOR_TEXT_LIGHT)
                init_rect = init_surf.get_rect(center=portrait_rect.center)
                self.screen.blit(init_surf, init_rect)

            leader_name_rect = pygame.Rect(x + 10, y + 210, card_width - 20, 45)
            self.draw_text_wrap(country.leader.name, leader_name_rect, self.font_ui, COLOR_ACCENT)

            desc_rect = pygame.Rect(x + 10, y + 260, card_width - 20, 150)
            self.draw_text_wrap(country.description, desc_rect, self.font_small, COLOR_TEXT_LIGHT)

            self.faction_buttons[idx].draw(self.screen)

        self.back_button.rect.y = 620
        self.back_button.draw(self.screen)

    def draw_designer_screen(self):
        self.screen.fill(COLOR_PANEL)
        title_surf = self.font_title.render("Конструктор Шаблонов Дивизий", True, COLOR_TEXT_LIGHT)
        self.screen.blit(title_surf, (50, 30))

        country = self.game.player_country
        if not country:
            return

        template = country.division_templates[0]
        stats = template.get_stats()

        # Полки/Слоты дивизии
        pygame.draw.rect(self.screen, (30, 39, 46), (50, 100, 500, 450), border_radius=10)

        # Нарисуем сетку 3x3 для батальонов
        for col in range(3):
            for row in range(3):
                idx = col * 3 + row
                box_rect = pygame.Rect(80 + col * 150, 130 + row * 130, 120, 100)
                pygame.draw.rect(self.screen, (47, 53, 66), box_rect, border_radius=8)

                if idx < len(template.battalions):
                    bat = template.battalions[idx]
                    bat_text = self.font_main.render(bat.name, True, COLOR_TEXT_LIGHT)
                    self.screen.blit(bat_text, (box_rect.x + 10, box_rect.y + 15))

                    # Маленькая иконка типа батальона
                    sub_text = self.font_small.render(f"Ширина: {bat.combat_width}", True, COLOR_ACCENT)
                    self.screen.blit(sub_text, (box_rect.x + 10, box_rect.y + 60))
                else:
                    empty_text = self.font_small.render("[ Пусто ]", True, COLOR_NEUTRAL)
                    self.screen.blit(empty_text, (box_rect.x + 30, box_rect.y + 40))

        # Статистика шаблона справа
        stats_rect = pygame.Rect(600, 100, 370, 450)
        pygame.draw.rect(self.screen, (45, 52, 54), stats_rect, border_radius=10)

        t_name = self.font_title.render(template.name, True, COLOR_ACCENT)
        self.screen.blit(t_name, (630, 130))

        stat_lines = [
            f"Противопехотная атака: {stats['soft_attack']}",
            f"Противотанковая атака: {stats['hard_attack']}",
            f"Защита дивизии: {stats['defense']}",
            f"Ширина фронта: {stats['width']}",
            f"Людские ресурсы: {stats['manpower']} чел.",
            "Требуемое снаряжение:"
        ]

        y_offset = 180
        for line in stat_lines:
            text_surf = self.font_main.render(line, True, COLOR_TEXT_LIGHT)
            self.screen.blit(text_surf, (630, y_offset))
            y_offset += 25

        # Перечень снаряжения
        for eq_type, amount in stats["equipment"].items():
            if amount > 0:
                eq_text = self.font_small.render(f" - {EQUIPMENT_NAMES[eq_type]}: {amount} ед.", True, COLOR_ACCENT)
                self.screen.blit(eq_text, (650, y_offset))
                y_offset += 20

        # Снабжение
        sup_text = self.font_main.render(f"Потребление снабжения: {stats['supply_use']:.2f}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(sup_text, (630, y_offset + 10))

        # Отрисовка кнопок
        for btn in self.designer_buttons:
            btn.draw(self.screen)

    def draw_cheat_menu_screen(self):
        self.screen.fill((30, 39, 46))
        title_surf = self.font_title.render("ЧИТ-ПАНЕЛЬ СТРАНЫ", True, COLOR_ACCENT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title_surf, title_rect)

        sub_surf = self.font_small.render("Используйте с умом для тестирования игровой логики", True, COLOR_TEXT_LIGHT)
        self.screen.blit(sub_surf, (SCREEN_WIDTH // 2 - sub_surf.get_width() // 2, 120))

        for btn in self.cheat_buttons:
            btn.draw(self.screen)

    def draw_province_info_panel(self, prov):
        """Метод вывода детальной сводки по провинции на боковой панели"""
        x_start = SCREEN_WIDTH - 280

        prov_title = self.font_main.render(prov.name, True, COLOR_ACCENT)
        self.screen.blit(prov_title, (x_start, 70))

        owner_name = prov.owner.name if prov.owner else "Нейтральная территория"
        owner_text = self.font_ui.render(f"Контроль: {owner_name}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(owner_text, (x_start, 95))

        # Перевод ландшафта
        terrain_dict = {"urban": "Город", "forest": "Тайга/Лес", "water": "Водный сектор"}
        terrain_rus = terrain_dict.get(prov.terrain, prov.terrain)
        terrain_text = self.font_ui.render(f"Ландшафт: {terrain_rus}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(terrain_text, (x_start, 115))

        mine_status = "Имеется (Добыча угля/ресурсов)" if prov.has_mine else "Отсутствует"
        mine_text = self.font_ui.render(f"Шахта: {mine_status}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(mine_text, (x_start, 135))

        # Перевод производств
        prod_names = {"none": "Пусто", "rifles": "Винтовки", "artillery": "Орудия", "trucks": "Грузовики",
                      "tanks": "Тракторы"}
        workshop_strings = [prod_names.get(w, w) for w in prov.workshops]
        workshops_text = self.font_small.render(f"Мастерские: {', '.join(workshop_strings)}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(workshops_text, (x_start, 155))

        supply_text = self.font_small.render(
            f"Снабжение: {prov.get_current_supply_weight():.1f} / {prov.supply_limit} ед.", True, COLOR_TEXT_LIGHT)
        self.screen.blit(supply_text, (x_start, 175))

        # Список дивизий в провинции
        div_list_y = 200
        div_title = self.font_ui.render("Дивизии в провинции:", True, COLOR_ACCENT)
        self.screen.blit(div_title, (x_start, div_list_y))
        div_list_y += 20

        for d in prov.divisions:
            is_selected = (d == self.game.selected_division)
            text_color = (241, 196, 15) if is_selected else COLOR_TEXT_LIGHT

            d_info = f"- {d.name} (Орг: {int(d.organization)}%)"
            d_surf = self.font_small.render(d_info, True, text_color)
            self.screen.blit(d_surf, (x_start + 10, div_list_y))

            # Обработка клика ЛКМ для выбора дивизии игрока
            d_rect = pygame.Rect(x_start, div_list_y, 260, 16)
            if d_rect.collidepoint(pygame.mouse.get_pos()) and pygame.mouse.get_pressed()[0]:
                if prov.owner == self.game.player_country:
                    self.game.selected_division = d

            div_list_y += 18

        # Подробные тактические данные о выделенной дивизии игрока
        if self.game.selected_division and self.game.selected_division.province == prov:
            sel_div = self.game.selected_division
            pygame.draw.rect(self.screen, (47, 53, 66), (x_start, div_list_y + 10, 260, 230),
                             border_radius=6)

            title_sd = self.font_ui.render(f"Выбрана: {sel_div.name}", True, (241, 196, 15))
            self.screen.blit(title_sd, (x_start + 10, div_list_y + 15))

            stats = sel_div.get_combat_stats()
            stat_texts = [
                f"Прочность: {int(sel_div.strength * 100)}%",
                f"Пехотная атака: {int(stats['soft_attack'])}",
                f"Бронебойная атака: {int(stats['hard_attack'])}",
                f"Защита: {int(stats['defense'])}",
                f"Опыт: {sel_div.experience}/1000 ({sel_div.veterancy_level})",
                f"Окопы: ур. {getattr(sel_div, 'entrenchment_level', 0)} (+{int(getattr(sel_div, 'entrenchment_level', 0) * 10)}% к защите)",
                f"Кулдаун атаки: {getattr(sel_div, 'attack_cooldown', 0)} ходов",
            ]

            sy = div_list_y + 35
            for st in stat_texts:
                st_surf = self.font_small.render(st, True, COLOR_TEXT_LIGHT)
                self.screen.blit(st_surf, (x_start + 10, sy))
                sy += 16

            if sel_div.commander:
                gen_text = self.font_small.render(f"Генерал: {sel_div.commander.name}", True, COLOR_ACCENT)
                self.screen.blit(gen_text, (x_start + 10, sy + 5))
                sy += 16

            plan_help = self.font_small.render("ПКМ на соседнюю пров. - План", True, (46, 204, 113))
            self.screen.blit(plan_help, (x_start + 10, sy + 12))

            if sel_div.target_province:
                target_txt = self.font_small.render(f"Цель наступления: {sel_div.target_province.name}", True,
                                                    (241, 196, 15))
                self.screen.blit(target_txt, (x_start + 10, sy + 25))

    def draw_country_info_panel(self, country):
        """Отрисовывает детальную панель государства поверх карты (модальное окно)"""
        # Затемнение карты под окном
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 160))
        self.screen.blit(dim_surf, (0, 0))

        # Окно модалки
        pygame.draw.rect(self.screen, COLOR_PANEL, self.country_modal_rect, border_radius=10)
        pygame.draw.rect(self.screen, country.color, self.country_modal_rect, width=3, border_radius=10)

        x = self.country_modal_rect.x
        y = self.country_modal_rect.y
        w = self.country_modal_rect.width

        # Заголовки
        title_surf = self.font_title.render(country.name, True, COLOR_TEXT_LIGHT)
        self.screen.blit(title_surf, (x + 20, y + 20))

        ideology_text = self.font_main.render(f"Идеология: {getattr(country, 'ideology', 'Нейтралитет')}", True,
                                              COLOR_ACCENT)
        self.screen.blit(ideology_text, (x + 20, y + 55))

        # Портрет лидера фракции
        port_rect = pygame.Rect(x + 20, y + 90, 120, 150)
        pygame.draw.rect(self.screen, country.leader.portrait_color, port_rect, border_radius=4)
        pygame.draw.rect(self.screen, COLOR_TEXT_LIGHT, port_rect, width=2, border_radius=4)

        portrait = country.leader.get_portrait()
        if portrait:
            self.screen.blit(portrait, (x + 20, y + 90))
        else:
            init_surf = self.font_title.render(country.leader.name[0], True, COLOR_TEXT_LIGHT)
            init_rect = init_surf.get_rect(center=port_rect.center)
            self.screen.blit(init_surf, init_rect)

        # Биография лидера фракции
        l_name_surf = self.font_main.render(f"{country.leader.title}: {country.leader.name}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(l_name_surf, (x + 160, y + 90))

        bio_rect = pygame.Rect(x + 160, y + 115, w - 180, 125)
        self.draw_text_wrap(country.leader.bio or "История нации покрыта тайной Березовских лесов.", bio_rect,
                            self.font_small, COLOR_TEXT_LIGHT)

        # Сбор сводной статистики по нации
        stats_y = y + 260
        stats_title = self.font_main.render("Сводные данные фракции:", True, COLOR_ACCENT)
        self.screen.blit(stats_title, (x + 20, stats_y))

        total_divisions = len(country.divisions)
        total_manpower = sum(d.manpower for d in country.divisions) + country.manpower
        rifles = country.equipment.get("rifles", 0)
        artillery = country.equipment.get("artillery", 0)
        tanks = country.equipment.get("tanks", 0)

        stat_lines_col1 = [
            f"Контролируемые провинции: {len(country.provinces)}",
            f"Численность армии: {total_divisions} див. ({total_manpower} чел.)",
        ]
        stat_lines_col2 = [
            f"Винтовки на складах: {rifles} шт.",
            f"Орудия на складах: {artillery} шт.",
            f"Танки на складах: {tanks} шт."
        ]

        sy = stats_y + 25
        for line in stat_lines_col1:
            st_surf = self.font_small.render(line, True, COLOR_TEXT_LIGHT)
            self.screen.blit(st_surf, (x + 20, sy))
            sy += 20

        sy = stats_y + 25
        for line in stat_lines_col2:
            st_surf = self.font_small.render(line, True, COLOR_TEXT_LIGHT)
            self.screen.blit(st_surf, (x + 280, sy))
            sy += 20

        # Кнопки взаимодействия внизу
        self.modal_close_btn.draw(self.screen)
        if self.modal_war_btn:
            self.modal_war_btn.draw(self.screen)

    def draw_game_screen(self):
        m_width = int(self.game.map_original.get_width() * self.game.zoom)
        m_height = int(self.game.map_original.get_height() * self.game.zoom)

        scaled_map = pygame.transform.scale(self.game.map_original, (m_width, m_height))
        self.screen.blit(scaled_map, (self.game.pan_x, self.game.pan_y))

        # Рисуем линии и стрелки планирования
        for country in self.game.countries:
            for div in country.divisions:
                if div.target_province:
                    start_pos = div.province.get_screen_pos(self.game.zoom, self.game.pan_x, self.game.pan_y)
                    end_pos = div.target_province.get_screen_pos(self.game.zoom, self.game.pan_x, self.game.pan_y)

                    # Рисуем пунктирную линию наступления
                    pygame.draw.line(self.screen, (241, 196, 15), start_pos, end_pos, 3)
                    pygame.draw.circle(self.screen, (241, 196, 15), end_pos, 8)

        # Отрисовка провинций
        for prov in self.game.provinces:
            screen_poly = []
            for px, py in prov.polygon:
                sx = int(px * self.game.zoom + self.game.pan_x)
                sy = int(py * self.game.zoom + self.game.pan_y)
                screen_poly.append((sx, sy))

            color = prov.owner.color if prov.owner else COLOR_NEUTRAL

            xs = [p[0] for p in screen_poly]
            ys = [p[1] for p in screen_poly]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            w, h = max_x - min_x + 2, max_y - min_y + 2

            if w > 0 and h > 0:
                temp_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                local_poly = [(p[0] - min_x, p[1] - min_y) for p in screen_poly]

                alpha_color = (color[0], color[1], color[2], 90)
                pygame.draw.polygon(temp_surf, alpha_color, local_poly)
                self.screen.blit(temp_surf, (min_x, min_y))

                is_hovered = prov.is_hovered(pygame.mouse.get_pos(), self.game.zoom, self.game.pan_x, self.game.pan_y)

                if self.game.selected_province == prov:
                    outline_color = (241, 196, 15)
                    width = 3
                elif is_hovered:
                    outline_color = (253, 150, 68)
                    width = 2
                else:
                    outline_color = (255, 255, 255)
                    width = 1

                pygame.draw.polygon(self.screen, outline_color, screen_poly, width)

            # Нарисуем дивизии внутри провинции
            if prov.divisions:
                cx, cy = prov.get_screen_pos(self.game.zoom, self.game.pan_x, self.game.pan_y)

                # Компактный прямоугольник со счетчиком дивизий
                d_rect = pygame.Rect(cx - 30, cy - 20, 60, 24)
                pygame.draw.rect(self.screen, COLOR_PANEL, d_rect, border_radius=4)
                pygame.draw.rect(self.screen, color, d_rect, width=2, border_radius=4)

                count_surf = self.font_small.render(f"Div: {len(prov.divisions)}", True, COLOR_TEXT_LIGHT)
                self.screen.blit(count_surf, (cx - 20, cy - 15))

                # Если дивизия игрока выбрана
                for d in prov.divisions:
                    if d == self.game.selected_division:
                        pygame.draw.rect(self.screen, (241, 196, 15), d_rect.inflate(6, 6), width=2, border_radius=6)

        # Рисуем индикаторы битв (скрещенные мечи)
        for combat in self.game.active_combats:
            cx, cy = combat.province.get_screen_pos(self.game.zoom, self.game.pan_x, self.game.pan_y)
            # Рисуем яркую метку боя
            combat_rect = pygame.Rect(cx - 20, cy - 50, 40, 25)
            pygame.draw.rect(self.screen, (192, 57, 43), combat_rect, border_radius=4)
            text_b = self.font_small.render("БОЙ!", True, (255, 255, 255))
            self.screen.blit(text_b, (cx - 15, cy - 46))

        # 3. Верхняя строка ресурсов страны (в стиле HoI4) c интеграцией Погоды
        top_bar_rect = pygame.Rect(0, 0, SCREEN_WIDTH - 300, 35)
        pygame.draw.rect(self.screen, COLOR_PANEL, top_bar_rect)
        pygame.draw.line(self.screen, (0, 0, 0), (0, 35), (SCREEN_WIDTH - 300, 35), 2)

        player_c = self.game.player_country
        if player_c:
            # Названия погоды и сезона
            weather_names = {"clear": "Ясно", "rain": "Дождь", "snowstorm": "Снегопад", "blizzard": "Метель"}
            season_names = {"spring": "Весна", "summer": "Лето", "autumn": "Осень", "winter": "Зима"}

            cur_weather = weather_names.get(self.game.weather_mgr.current_weather,
                                            self.game.weather_mgr.current_weather)
            cur_season = season_names.get(self.game.weather_mgr.season, self.game.weather_mgr.season)

            res_str = (
                f"Людские ресурсы: {player_c.manpower} | "
                f"Полит. власть: {player_c.political_power} | "
                f"Топливо: {int(player_c.fuel)}л | "
                f"Винтовки: {player_c.equipment[EQ_RIFLES]} | "
                f"Погода: {cur_season} ({cur_weather})"
            )
            res_surf = self.font_ui.render(res_str, True, COLOR_TEXT_LIGHT)
            self.screen.blit(res_surf, (15, 8))

        # 4. Боковая информационная панель (справа)
        panel_rect = pygame.Rect(SCREEN_WIDTH - 300, 0, 300, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, COLOR_PANEL, panel_rect)
        pygame.draw.line(self.screen, (0, 0, 0), (SCREEN_WIDTH - 300, 0), (SCREEN_WIDTH - 300, SCREEN_HEIGHT), 2)

        # Текущий ход
        turn_text = self.font_title.render(f"Ход: {self.game.turn}", True, COLOR_TEXT_LIGHT)
        self.screen.blit(turn_text, (SCREEN_WIDTH - 280, 20))

        # Вызов переработанного рендеринга информации о провинции
        prov = self.game.selected_province
        if prov:
            self.draw_province_info_panel(prov)

        # Рисуем кнопки игрового процесса
        for btn in self.game_ui_buttons:
            btn.draw(self.screen)

        # Рисуем модальную карточку фракции, если она активна (ПКМ)
        if self.country_modal_active and self.selected_modal_country:
            self.draw_country_info_panel(self.selected_modal_country)


if __name__ == "__main__":
    app = App()
    app.run()