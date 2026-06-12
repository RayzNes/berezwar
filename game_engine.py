# game_engine.py
import pygame
import os
import random
import json
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_RED, COLOR_BLUE, COLOR_GREEN, COLOR_ORANGE,
    EQ_RIFLES, EQ_ARTILLERY, EQ_TRUCKS, EQ_TANKS, MAX_PLANNING_BONUS,
    TERRAIN_URBAN, TERRAIN_FOREST, TERRAIN_WATER, PROD_NONE, PROD_RIFLES,
    PROD_ARTILLERY, PROD_TRUCKS, PROD_TANKS
)
from models import Province, Country, Leader
from military import Battalion, SupportCompany, DivisionTemplate, Division, Commander
from combat import Combat
from weather import WeatherManager


class GameEngine:
    def __init__(self):
        # 1. Загрузка карты
        self.map_original = None
        self.load_map_asset()

        # Инициализация менеджера погоды
        self.weather_mgr = WeatherManager()

        # Списки игровых объектов
        self.countries = []
        self.provinces = []

        # 2. Динамическая загрузка данных фракций и провинций из JSON
        self.load_factions_and_provinces()

        # 4. Базовые батальоны и роты поддержки
        self.infantry_b = Battalion("Пехота", "infantry", soft_attack=8, hard_attack=2, defense=15, combat_width=2,
                                    manpower_req=1000, eq_req={EQ_RIFLES: 100})
        self.artillery_b = Battalion("Арт. дивизион", "artillery", soft_attack=24, hard_attack=4, defense=4,
                                     combat_width=3, manpower_req=500, eq_req={EQ_ARTILLERY: 36})
        self.tank_b = Battalion("Бронеотряд", "tank", soft_attack=15, hard_attack=15, defense=10, combat_width=2,
                                manpower_req=500, eq_req={EQ_TANKS: 40})

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
        self.selected_division = None

        # Активные бои
        self.active_combats = []

    def load_map_asset(self):
        map_path = "./map.png"
        if os.path.exists(map_path):
            try:
                self.map_original = pygame.image.load(map_path).convert_alpha()
            except pygame.error:
                self.create_fallback_map()
        else:
            self.create_fallback_map()

    def create_fallback_map(self):
        self.map_original = pygame.Surface((1024, 1024))
        self.map_original.fill((70, 70, 80))
        for x in range(0, 1024, 64):
            pygame.draw.line(self.map_original, (100, 100, 110), (x, 0), (x, 1024), 1)
        for y in range(0, 1024, 64):
            pygame.draw.line(self.map_original, (100, 100, 110), (0, y), (1024, y), 1)

    def load_factions_and_provinces(self):
        """Загружает данные из JSON и назначает идеологии фракциям"""
        countries_by_id = {}

        # 1. Загрузка factions.json
        factions_path = "./factions.json"
        if os.path.exists(factions_path):
            try:
                with open(factions_path, "r", encoding="utf-8") as f:
                    factions_data = json.load(f)
            except Exception as e:
                print(f"Предупреждение: Не удалось прочесть factions.json ({e}). Применен стандартный пресет.")
                factions_data = self._get_default_factions()
        else:
            factions_data = self._get_default_factions()

        for f_data in factions_data:
            color = tuple(f_data["color"])
            l_data = f_data["leader"]
            leader = Leader(
                name=l_data["name"],
                title=l_data["title"],
                portrait_color=color,
                bio=l_data["bio"],
                portrait_file=l_data["portrait"]
            )
            country = Country(
                name=f_data["name"],
                color=color,
                leader=leader,
                description=f_data["description"]
            )

            # Присвоение фракционных идеологий
            if f_data["id"] == "miners":
                country.ideology = "Коммунизм"
            elif f_data["id"] == "admin":
                country.ideology = "Демократия"
            elif f_data["id"] == "makar":
                country.ideology = "Монархизм"
            elif f_data["id"] == "brotherhood":
                country.ideology = "Национализм"
            else:
                country.ideology = "Нейтралитет"

            countries_by_id[f_data["id"]] = country
            self.countries.append(country)

        # 2. Загрузка provinces.json
        provinces_path = "./provinces.json"
        if os.path.exists(provinces_path):
            try:
                with open(provinces_path, "r", encoding="utf-8") as f:
                    provinces_data = json.load(f)
            except Exception as e:
                print(f"Предупреждение: Не удалось прочесть provinces.json ({e}). Применен стандартный пресет.")
                provinces_data = self._get_default_provinces()
        else:
            provinces_data = self._get_default_provinces()

        for p_data in provinces_data:
            polygon = [tuple(pt) for pt in p_data["polygon"]]
            prov = Province(id_num=p_data["id"], name=p_data["name"], polygon=polygon)

            # Установка специфичных экономических полей
            prov.terrain = p_data.get("terrain", TERRAIN_URBAN)
            prov.has_mine = p_data.get("has_mine", False)
            prov.workshops = p_data.get("workshops", [PROD_RIFLES, PROD_NONE, PROD_NONE])

            # Связывание владельца провинции
            owner_id = p_data.get("starting_owner")
            if owner_id in countries_by_id:
                owner_country = countries_by_id[owner_id]
                prov.owner = owner_country
                owner_country.provinces.append(prov)

            self.provinces.append(prov)

    def init_military_for_countries(self):
        names_pool = {
            "Союз Горняков": ["Григорий Отбойник", "Дмитрий Сплав", "Артем Вагон"],
            "Администрация Округа": ["Полковник Серый", "Генерал Чиновник", "Секретарь Анна"],
            "Таёжное Братство": ["Староста Семен", "Капканщик Дед", "Следопыт Глеб"],
            "Макарляндия": ["ИИ Бот-1", "Макар Младший", "Святослав Воля"]
        }

        for idx, country in enumerate(self.countries):
            template = DivisionTemplate("Стандартная бригада")
            template.add_battalion(self.infantry_b)
            template.add_battalion(self.infantry_b)
            template.add_battalion(self.infantry_b)
            template.add_support(self.engineer_c)
            country.division_templates.append(template)

            c_names = names_pool.get(country.name, ["Офицер ИИ", "Лейтенант ИИ"])
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

            for p in country.provinces:
                comm = country.commanders[0] if country.commanders else None
                div_name = f"{len(country.divisions) + 1}-я Бригада ({country.name})"
                div = Division(div_name, template, p, comm)
                p.divisions.append(div)
                country.divisions.append(div)

    def select_player_faction(self, chosen_country_name):
        """Устанавливает фракцию игрока, сохраняя другие фракции ИИ на карте"""
        for country in self.countries:
            if country.name == chosen_country_name:
                self.player_country = country
                break

        if self.player_country and self.player_country.provinces:
            self.selected_province = self.player_country.provinces[0]
        else:
            self.selected_province = self.provinces[0]

        self.selected_division = None

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
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
        country = self.player_country
        if not country:
            return False

        stats = template.get_stats()
        if country.manpower < stats["manpower"]:
            return False

        for eq_type, amount in stats["equipment"].items():
            if country.equipment.get(eq_type, 0) < amount:
                return False

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
        for p in self.provinces:
            weight = p.get_current_supply_weight()
            if weight > p.supply_limit:
                penalty = max(0.2, p.supply_limit / weight)
                for d in p.divisions:
                    d.organization = max(10.0, d.organization * penalty)
                    d.strength = max(0.1, d.strength * penalty)
            else:
                for d in p.divisions:
                    d.organization = min(d.max_organization, d.organization + 15.0)
                    d.update_strength()

    def get_best_target(self, division):
        """Интеллектуальный поиск наилучшей цели для атаки ИИ дивизии"""
        if division.organization < 40.0:
            return None  # Слабые дивизии не атакуют, а только удерживают текущую позицию

        current_prov = division.province
        country = current_prov.owner
        if not country:
            return None

        # Поиск смежных провинций
        neighbors = []
        for other_prov in self.provinces:
            if other_prov == current_prov:
                continue

            # Проверка дистанции между границами полигонов
            is_neighbor = False
            for p_a in current_prov.polygon:
                for p_b in other_prov.polygon:
                    dist = ((p_a[0] - p_b[0]) ** 2 + (p_a[1] - p_b[1]) ** 2) ** 0.5
                    if dist <= 5.0:
                        is_neighbor = True
                        break
                if is_neighbor:
                    break

            if is_neighbor:
                neighbors.append(other_prov)

        if not neighbors:
            return None

        # Приоритет 1: Контратаковать свои провинции, если на них есть чужаки
        p1_targets = []
        for n in neighbors:
            if n.owner == country:
                enemies = [d for d in n.divisions if d.province.owner != country]
                if enemies:
                    p1_targets.append(n)
        if p1_targets:
            return min(p1_targets, key=lambda p: len(p.divisions))

        # Приоритет 2: Атаковать неприятельские провинции с ресурсами (has_mine)
        p2_targets = [n for n in neighbors if n.owner != country and n.has_mine]
        if p2_targets:
            return min(p2_targets, key=lambda p: len(p.divisions))

        # Приоритет 3 и 4: Сортировка неприятельских провинций
        # Сначала те, где меньше войск противника. При равенстве — провинции игрока.
        hostile_neighbors = [n for n in neighbors if n.owner != country]
        if not hostile_neighbors:
            return None

        def evaluation_score(prov):
            is_player = 1 if (self.player_country and prov.owner == self.player_country) else 0
            enemy_count = len(prov.divisions)
            return (enemy_count, -is_player)

        hostile_neighbors.sort(key=evaluation_score)
        return hostile_neighbors[0]

    def process_battle_plans(self):
        combats_to_start = {}

        # Проверка блокировки перемещения сильным снегопадом
        weather_blocks_movement = (self.weather_mgr.current_weather == "snowstorm")

        for country in self.countries:
            for div in country.divisions:
                if div.target_province:
                    # Пропуск при кулдауне или заблокированных из-за бури путях
                    if getattr(div, "movement_cooldown", 0) > 0 or weather_blocks_movement:
                        continue

                    if div.target_province.owner == country or div.target_province.owner is None:
                        div.province.divisions.remove(div)
                        div.target_province.divisions.append(div)
                        div.province = div.target_province
                        div.target_province = None
                        div.planning_bonus = 0.0

                        # Вешаем кулдаун на перемещение
                        div.movement_cooldown = 1
                        div.has_moved_this_turn = True
                    else:
                        if div.planning_bonus < MAX_PLANNING_BONUS:
                            div.planning_bonus = min(MAX_PLANNING_BONUS, div.planning_bonus + 0.10)

                        target_p = div.target_province
                        if target_p not in combats_to_start:
                            combats_to_start[target_p] = ([], list(target_p.divisions))

                        if div not in combats_to_start[target_p][0]:
                            combats_to_start[target_p][0].append(div)

        for target_p, (attackers, defenders) in combats_to_start.items():
            if attackers and defenders:
                existing_combat = None
                for c in self.active_combats:
                    if c.province == target_p:
                        existing_combat = c
                        break

                if existing_combat:
                    for att in attackers:
                        if att not in existing_combat.attackers:
                            existing_combat.attackers.append(att)
                else:
                    new_combat = Combat(target_p, attackers, defenders)
                    self.active_combats.append(new_combat)

    def run_ai_turns(self):
        """Интеллектуальная логика поведения ботов с учетом выбора целей"""
        for country in self.countries:
            if country == self.player_country:
                continue

            for div in country.divisions:
                if div.target_province is None:
                    target_prov = self.get_best_target(div)
                    if target_prov and target_prov != div.province:
                        div.target_province = target_prov

    def next_turn(self):
        """Переход к следующему ходу. Обработка боя, ресурсов, снабжения и погоды."""
        # 1. Сражения (передача погоды в метод расчета)
        combats_still_active = []
        for combat in self.active_combats:
            combat_is_active = combat.resolve_turn(self.weather_mgr)
            if combat_is_active:
                combats_still_active.append(combat)
            else:
                if combat.attackers and not combat.defenders:
                    old_owner = combat.province.owner
                    new_owner = combat.attackers[0].province.owner

                    if old_owner and combat.province in old_owner.provinces:
                        old_owner.provinces.remove(combat.province)

                    combat.province.owner = new_owner
                    if new_owner:
                        new_owner.provinces.append(combat.province)

                    for att in combat.attackers:
                        if att in att.province.divisions:
                            att.province.divisions.remove(att)
                        combat.province.divisions.append(att)
                        att.province = combat.province
                        att.target_province = None
                        att.planning_bonus = 0.0

                        # Вешаем кулдаун движения на захватчика провинции
                        att.movement_cooldown = 1
                        att.has_moved_this_turn = True

        self.active_combats = combats_still_active

        # 1.5 Вычисление шагов ИИ-фракций
        self.run_ai_turns()

        # 2. Обработка планов
        self.process_battle_plans()

        # 3. Прирост ресурсов страны
        for country in self.countries:
            prov_count = len(country.provinces)

            country.political_power += prov_count * 15
            country.money += prov_count * 50
            country.fuel += prov_count * 20.0

            for p in country.provinces:
                if p.has_mine:
                    country.manpower += 500
                    country.raw_materials += 50

            for p in country.provinces:
                for prod in p.workshops:
                    if prod != PROD_NONE:
                        if country.raw_materials >= 2:
                            country.raw_materials -= 2
                            if prod == PROD_RIFLES:
                                country.equipment[EQ_RIFLES] += 10
                            elif prod == PROD_ARTILLERY:
                                country.equipment[EQ_ARTILLERY] += 2
                            elif prod == PROD_TRUCKS:
                                country.equipment[EQ_TRUCKS] += 2
                            elif prod == PROD_TANKS:
                                country.equipment[EQ_TANKS] += 1

        # 4. Логистика и Снабжение
        self.calculate_logistics()

        # 5. Снижение кулдаунов действий в конце хода и обновление окопов
        for country in self.countries:
            for div in country.divisions:
                if getattr(div, "attack_cooldown", 0) > 0:
                    div.attack_cooldown -= 1
                if getattr(div, "movement_cooldown", 0) > 0:
                    div.movement_cooldown -= 1

                # Механика окопа у неактивных юнитов
                div.update_entrenchment()

        # 6. Обновление погодного цикла на новый ход
        self.weather_mgr.update()

        self.turn += 1

    def _get_default_factions(self):
        """Резервные данные фракций на случай отсутствия factions.json"""
        return [
            {
                "id": "miners",
                "name": "Союз Горняков",
                "color": [192, 57, 43],
                "leader": {
                    "name": "Алексей Шахтер",
                    "title": "Глава Союза Горняков",
                    "bio": "Суровый мужик с мозолистыми руками. Сторонник суровой дисциплины и работы.",
                    "portrait": "alex.png"
                },
                "description": "Рабочий класс, готовый отстаивать свои шахты."
            },
            {
                "id": "admin",
                "name": "Администрация Округа",
                "color": [41, 128, 185],
                "leader": {
                    "name": "Мэр Василий",
                    "title": "Мэр Администрации Округа",
                    "bio": "Обещает новые детские площадки и стабильность к 2045 году.",
                    "portrait": "vasiliy.png"
                },
                "description": "Официальные власти, пытающиеся удержать контроль."
            },
            {
                "id": "brotherhood",
                "name": "Таёжное Братство",
                "color": [39, 174, 96],
                "leader": {
                    "name": "Егерь Михалыч",
                    "title": "Лидер Таёжного Братства",
                    "bio": "Знает каждый куст в тайге. Не любит городских.",
                    "portrait": "mihalych.png"
                },
                "description": "Скрытные и опасные хозяева березовских лесов."
            }
        ]

    def _get_default_provinces(self):
        """Резервные данные провинций на случай отсутствия provinces.json"""
        return [
            {
                "id": 1,
                "name": "Шахтёрский район (Центр)",
                "polygon": [[300, 200], [450, 200], [400, 350], [250, 350]],
                "starting_owner": "miners",
                "terrain": "urban",
                "has_mine": False,
                "workshops": ["rifles", "none", "none"]
            },
            {
                "id": 2,
                "name": "Запрудный (ул. Королёва)",
                "polygon": [[450, 200], [600, 200], [650, 350], [400, 350]],
                "starting_owner": "admin",
                "terrain": "water",
                "has_mine": False,
                "workshops": ["rifles", "none", "none"]
            },
            {
                "id": 3,
                "name": "Западные холмы (ул. Матросова)",
                "polygon": [[250, 350], [400, 350], [350, 500], [200, 500]],
                "starting_owner": "miners",
                "terrain": "urban",
                "has_mine": True,
                "workshops": ["rifles", "none", "none"]
            },
            {
                "id": 4,
                "name": "Левобережный (ул. Леонова)",
                "polygon": [[400, 350], [650, 350], [600, 500], [350, 500]],
                "starting_owner": "brotherhood",
                "terrain": "forest",
                "has_mine": False,
                "workshops": ["rifles", "none", "none"]
            },
            {
                "id": 5,
                "name": "Восточные Дачи (ул. Гоголя)",
                "polygon": [[600, 200], [750, 250], [700, 450], [650, 350]],
                "starting_owner": "brotherhood",
                "terrain": "forest",
                "has_mine": False,
                "workshops": ["rifles", "none", "none"]
            }
        ]