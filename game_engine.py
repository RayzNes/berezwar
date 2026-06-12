# game_engine.py
import pygame
import os
import random
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_RED, COLOR_BLUE, COLOR_GREEN, COLOR_ORANGE,
    EQ_RIFLES, EQ_ARTILLERY, EQ_TRUCKS, EQ_TANKS, MAX_PLANNING_BONUS
)
from models import Province, Country, Leader
from military import Battalion, SupportCompany, DivisionTemplate, Division, Commander
from combat import Combat


class GameEngine:
    def __init__(self):
        # 1. Загрузка карты
        self.map_original = None
        self.load_map_asset()  # Now this method exists

        # 2. Инициализация фракций и лидеров
        self.leader_1 = Leader(
            "Алексей Шахтер",
            "Глава Союза Горняков",
            COLOR_RED,
            "Суровый мужик с мозолистыми руками. Сторонник суровой дисциплины и работы.",
            "alex.png"
        )
        self.leader_2 = Leader(
            "Мэр Василий",
            "Мэр Администрации Округа",
            COLOR_BLUE,
            "Обещает новые детские площадки и стабильность к 2045 году.",
            "vasiliy.png"
        )
        self.leader_3 = Leader(
            "Егерь Михалыч",
            "Лидер Таёжного Братства",
            COLOR_GREEN,
            "Живёт глубоко в лесу, презирает налоги, сотовую связь и любые законы.",
            "eger.png"
        )
        self.leader_4 = Leader(
            "Макар Лысенко",
            "Основатель Макарляндии",
            COLOR_ORANGE,
            "Лидер националистов, монарх Макарляндии.",
            "makar.png"
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

        # 3. Инициализация провинций
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

        # Распределение провинций фракциям
        self.provinces[0].owner = self.countries[0]
        self.provinces[2].owner = self.countries[0]
        self.provinces[1].owner = self.countries[1]
        self.provinces[4].owner = self.countries[2]
        self.provinces[3].owner = self.countries[3]

        for p in self.provinces:
            if p.owner:
                p.owner.provinces.append(p)

        # 4. Базовые батальоны
        self.infantry_b = Battalion("Пехота", "infantry", soft_attack=8, hard_attack=2, defense=15, combat_width=2,
                                    manpower_req=1000, eq_req={EQ_RIFLES: 100})
        self.artillery_b = Battalion("Арт. дивизион", "artillery", soft_attack=24, hard_attack=4, defense=4,
                                     combat_width=3, manpower_req=500, eq_req={EQ_ARTILLERY: 36})
        self.tank_b = Battalion("Бронеотряд", "tank", soft_attack=15, hard_attack=15, defense=10, combat_width=2,
                                manpower_req=500, eq_req={EQ_TANKS: 40})

        # Базовые роты поддержки
        self.engineer_c = SupportCompany("Инженеры", "engineer", soft_attack=2, hard_attack=0, defense=10,
                                         manpower_req=200, eq_req={EQ_RIFLES: 20})
        self.logistics_c = SupportCompany("Служба снабжения", "logistics", soft_attack=0, hard_attack=0, defense=2,
                                          manpower_req=100, eq_req={EQ_TRUCKS: 15}, supply_bonus=0.25)

        # 5. Инициализация военных систем для всех фракций
        self.init_military_for_countries()

        # Камера
        self.zoom = 0.8
        self.pan_x = 50
        self.pan_y = -100
        self.is_dragging = False
        self.drag_start = (0, 0)

        # Игровые переменные
        self.turn = 1
        self.player_country = None
        self.selected_province = None
        self.selected_division = None  # Выбранная в данный момент дивизия игрока

        # Активные бои
        self.active_combats = []

    def load_map_asset(self):
        """Загружает карту из файла или создает заглушку"""
        map_path = "./map.png"
        if os.path.exists(map_path):
            try:
                self.map_original = pygame.image.load(map_path).convert_alpha()
            except pygame.error:
                self.create_fallback_map()
        else:
            self.create_fallback_map()

    def create_fallback_map(self):
        """Создает карту-заглушку, если файл не найден"""
        self.map_original = pygame.Surface((1024, 1024))
        self.map_original.fill((70, 70, 80))
        # Рисуем простую сетку для ориентации
        for x in range(0, 1024, 64):
            pygame.draw.line(self.map_original, (100, 100, 110), (x, 0), (x, 1024), 1)
        for y in range(0, 1024, 64):
            pygame.draw.line(self.map_original, (100, 100, 110), (0, y), (1024, y), 1)

    def init_military_for_countries(self):
        """Создает стартовые шаблоны, генералов и дивизии для всех сторон"""
        names_pool = {
            "Союз Горняков": ["Григорий Отбойник", "Дмитрий Сплав", "Артем Вагон"],
            "Администрация Округа": ["Полковник Серый", "Генерал Чиновник", "Секретарь Анна"],
            "Таёжное Братство": ["Староста Семен", "Капканщик Дед", "Следопыт Глеб"],
            "Фурманово — Макарляндия": ["ИИ Бот-1", "Макар Младший", "Святослав Воля"]
        }

        for idx, country in enumerate(self.countries):
            # Шаблоны по умолчанию
            template = DivisionTemplate("Стандартная бригада")
            template.add_battalion(self.infantry_b)
            template.add_battalion(self.infantry_b)
            template.add_battalion(self.infantry_b)
            template.add_support(self.engineer_c)
            country.division_templates.append(template)

            # Создание генералов
            c_names = names_pool.get(country.name, ["Офицер"])
            for n_idx, name in enumerate(c_names):
                gen = Commander(
                    name=name,
                    rank="General",
                    attack=random.randint(2, 5),
                    defense=random.randint(2, 5),
                    maneuver=random.randint(1, 4),
                    logistics=random.randint(1, 4),
                    portrait_file=f"comm_{idx}_{n_idx}.png",
                    traits=["Патриот Кузбасса"]
                )
                country.commanders.append(gen)

            # Создание стартовых дивизий в провинциях
            for p in country.provinces:
                comm = country.commanders[0] if country.commanders else None
                div_name = f"{len(country.divisions) + 1}-я Бригада ({country.name})"
                div = Division(div_name, template, p, comm)

                p.divisions.append(div)
                country.divisions.append(div)

    def select_player_faction(self, chosen_country_name):
        """Устанавливает фракцию игрока и нейтрализует другие провинции"""
        for country in self.countries:
            if country.name == chosen_country_name:
                self.player_country = country
                break

        # Все не принадлежащие игроку провинции становятся нейтральными
        for p in self.provinces:
            if p.owner != self.player_country:
                if p.owner:
                    if p in p.owner.provinces:
                        p.owner.provinces.remove(p)
                p.owner = None

        if self.player_country and self.player_country.provinces:
            self.selected_province = self.player_country.provinces[0]
        else:
            self.selected_province = self.provinces[0]

        self.selected_division = None

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # ЛКМ
                clicked_province = False
                for prov in self.provinces:
                    if prov.is_hovered(event.pos, self.zoom, self.pan_x, self.pan_y):
                        self.selected_province = prov
                        clicked_province = True
                        break

                if not clicked_province and event.pos[0] < SCREEN_WIDTH - 300:
                    self.is_dragging = True
                    self.drag_start = event.pos

            elif event.button == 2:
                self.is_dragging = True
                self.drag_start = event.pos

            elif event.button == 4:
                self.zoom = min(self.zoom + 0.05, 2.0)
            elif event.button == 5:
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

    def recruit_division(self, template, province):
        """Пытается рекрутировать новую дивизию за счет людских ресурсов и снаряжения"""
        country = self.player_country
        if not country:
            return False

        stats = template.get_stats()
        # Проверяем людские ресурсы
        if country.manpower < stats["manpower"]:
            return False

        # Проверяем снаряжение
        for eq_type, amount in stats["equipment"].items():
            if country.equipment.get(eq_type, 0) < amount:
                return False

        # Оплата и рекрутинг
        country.manpower -= stats["manpower"]
        for eq_type, amount in stats["equipment"].items():
            country.equipment[eq_type] -= amount

        div_name = f"{len(country.divisions) + 1}-я Нар. Бригада"
        commander = random.choice(country.commanders) if country.commanders else None

        new_div = Division(div_name, template, province, commander)
        province.divisions.append(new_div)
        country.divisions.append(new_div)
        return True

    def calculate_logistics(self):
        """Снабжение дивизий на основе лимитов снабжения провинций"""
        for p in self.provinces:
            weight = p.get_current_supply_weight()
            if weight > p.supply_limit:
                # Штраф снабжения дивизиям в провинции
                penalty = max(0.2, p.supply_limit / weight)
                for d in p.divisions:
                    # Понижаем организацию и боевую силу
                    d.organization = max(10.0, d.organization * penalty)
                    d.strength = max(0.1, d.strength * penalty)
            else:
                # Восстановление снабжения/организации
                for d in p.divisions:
                    d.organization = min(d.max_organization, d.organization + 15.0)
                    d.update_strength()

    def process_battle_plans(self):
        """Обрабатывает активные планы наступления во время окончания хода"""
        combats_to_start = {}  # {Province: (attackers_list, defenders_list)}

        for country in self.countries:
            for div in country.divisions:
                if div.target_province:
                    # Если провинция принадлежит игроку или союзникам, просто двигаемся
                    if div.target_province.owner == country or div.target_province.owner is None:
                        # Движение
                        div.province.divisions.remove(div)
                        div.target_province.divisions.append(div)
                        div.province = div.target_province
                        div.target_province = None
                        div.planning_bonus = 0.0
                    else:
                        # Накопление бонуса планирования и подготовка к атаке
                        if div.planning_bonus < MAX_PLANNING_BONUS:
                            div.planning_bonus = min(MAX_PLANNING_BONUS, div.planning_bonus + 0.10)

                        # Планируем атаку на вражескую провинцию
                        target_p = div.target_province
                        if target_p not in combats_to_start:
                            combats_to_start[target_p] = ([], list(target_p.divisions))

                        if div not in combats_to_start[target_p][0]:
                            combats_to_start[target_p][0].append(div)

        # Запускаем новые сражения
        for target_p, (attackers, defenders) in combats_to_start.items():
            if attackers and defenders:
                # Ищем, не идет ли уже бой в этой провинции
                existing_combat = None
                for c in self.active_combats:
                    if c.province == target_p:
                        existing_combat = c
                        break

                if existing_combat:
                    # Добавляем новых атакующих к текущему бою
                    for att in attackers:
                        if att not in existing_combat.attackers:
                            existing_combat.attackers.append(att)
                else:
                    new_combat = Combat(target_p, attackers, defenders)
                    self.active_combats.append(new_combat)

    def next_turn(self):
        """Переход к следующему ходу. Обработка боя, ресурсов и снабжения."""
        # 1. Сражения
        combats_still_active = []
        for combat in self.active_combats:
            combat_is_active = combat.resolve_turn()
            if combat_is_active:
                combats_still_active.append(combat)
            else:
                # Если битва выиграна атакующими, они продвигаются в провинцию
                if combat.attackers and not combat.defenders:
                    # Провинция меняет владельца
                    old_owner = combat.province.owner
                    new_owner = combat.attackers[0].province.owner

                    if old_owner and combat.province in old_owner.provinces:
                        old_owner.provinces.remove(combat.province)

                    combat.province.owner = new_owner
                    if new_owner:
                        new_owner.provinces.append(combat.province)

                    # Продвигаем выжившие атакующие дивизии
                    for att in combat.attackers:
                        if att in att.province.divisions:
                            att.province.divisions.remove(att)
                        combat.province.divisions.append(att)
                        att.province = combat.province
                        att.target_province = None
                        att.planning_bonus = 0.0

        self.active_combats = combats_still_active

        # 2. Обработка планов
        self.process_battle_plans()

        # 3. Прирост ресурсов страны
        for country in self.countries:
            # Базовый прирост за контролируемые провинции
            prov_count = len(country.provinces)
            country.manpower += prov_count * 100
            country.political_power += 15
            country.money += prov_count * 50
            country.fuel += 20.0

            # Автоматическая выработка базового снаряжения
            country.equipment[EQ_RIFLES] += prov_count * 10
            country.equipment[EQ_ARTILLERY] += prov_count * 1
            country.equipment[EQ_TRUCKS] += max(1, prov_count // 2)

        # 4. Логистика и Снабжение
        self.calculate_logistics()

        self.turn += 1