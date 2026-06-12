# military.py
import pygame
import os
from constants import EQ_RIFLES, EQ_ARTILLERY, EQ_TRUCKS, EQ_TANKS, TERRAIN_URBAN


def load_commander_portrait(filename, fallback_color):
    """Пытается загрузить портрет из папки portraits/ или создает цветовую заглушку"""
    portraits_dir = "./portraits"
    if not os.path.exists(portraits_dir):
        os.makedirs(portraits_dir)

    path = os.path.join(portraits_dir, filename)
    if os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(img, (120, 150))
        except pygame.error:
            pass

    # Заглушка
    surf = pygame.Surface((120, 150))
    surf.fill(fallback_color)
    pygame.draw.rect(surf, (255, 255, 255), surf.get_rect(), 2)
    return surf


class Battalion:
    def __init__(self, name, b_type, soft_attack, hard_attack, defense, combat_width, manpower_req, eq_req):
        self.name = name
        self.b_type = b_type  # "infantry", "artillery", "tank"
        self.soft_attack = soft_attack
        self.hard_attack = hard_attack
        self.defense = defense
        self.combat_width = combat_width
        self.manpower_req = manpower_req
        self.eq_req = eq_req  # Словарь вида {EQ_RIFLES: 100}


class SupportCompany:
    def __init__(self, name, s_type, soft_attack, hard_attack, defense, manpower_req, eq_req, supply_bonus=0.0):
        self.name = name
        self.s_type = s_type  # "art_support", "engineer", "logistics"
        self.soft_attack = soft_attack
        self.hard_attack = hard_attack
        self.defense = defense
        self.manpower_req = manpower_req
        self.eq_req = eq_req
        self.supply_bonus = supply_bonus  # Процент снижения потребления припасов


class Commander:
    def __init__(self, name, rank, attack, defense, maneuver, logistics, portrait_file, traits=None):
        self.name = name
        self.rank = rank  # "Officer", "General", "FieldMarshal"
        self.attack = attack
        self.defense = defense
        self.maneuver = maneuver
        self.logistics = logistics
        self.portrait_file = portrait_file
        self.traits = traits if traits else []
        self.portrait_cache = None

    def get_portrait(self, fallback_color):
        if self.portrait_cache is None:
            self.portrait_cache = load_commander_portrait(self.portrait_file, fallback_color)
        return self.portrait_cache


class DivisionTemplate:
    def __init__(self, name):
        self.name = name
        self.battalions = []  # Список Battalion
        self.support_companies = []  # Список SupportCompany

    def add_battalion(self, battalion):
        if len(self.battalions) < 9:  # Максимум 9 батальонов в полках дивизии
            self.battalions.append(battalion)

    def remove_battalion(self, index):
        if 0 <= index < len(self.battalions):
            self.battalions.pop(index)

    def add_support(self, support):
        if len(self.support_companies) < 5:  # Максимум 5 рот поддержки
            self.support_companies.append(support)

    def remove_support(self, index):
        if 0 <= index < len(self.support_companies):
            self.support_companies.pop(index)

    def get_stats(self):
        """Возвращает агрегированные параметры шаблона"""
        stats = {
            "soft_attack": 0,
            "hard_attack": 0,
            "defense": 0,
            "width": 0,
            "manpower": 0,
            "equipment": {EQ_RIFLES: 0, EQ_ARTILLERY: 0, EQ_TRUCKS: 0, EQ_TANKS: 0},
            "supply_use": 1.0
        }
        for b in self.battalions:
            stats["soft_attack"] += b.soft_attack
            stats["hard_attack"] += b.hard_attack
            stats["defense"] += b.defense
            stats["width"] += b.combat_width
            stats["manpower"] += b.manpower_req
            for eq_type, amount in b.eq_req.items():
                stats["equipment"][eq_type] = stats["equipment"].get(eq_type, 0) + amount

        supply_reduction = 0.0
        for s in self.support_companies:
            stats["soft_attack"] += s.soft_attack
            stats["hard_attack"] += s.hard_attack
            stats["defense"] += s.defense
            stats["manpower"] += s.manpower_req
            supply_reduction += s.supply_bonus
            for eq_type, amount in s.eq_req.items():
                stats["equipment"][eq_type] = stats["equipment"].get(eq_type, 0) + amount

        stats["supply_use"] = max(0.1, (len(self.battalions) * 0.2 + 0.5) * (1.0 - supply_reduction))
        return stats


class Division:
    def __init__(self, name, template, province, commander=None):
        self.name = name
        self.template = template
        self.province = province  # Ссылка на Province, где расквартирована дивизия
        self.commander = commander  # Commander

        # Текущее состояние
        stats = self.template.get_stats()
        self.manpower = stats["manpower"]
        self.max_manpower = stats["manpower"]

        self.organization = 100.0
        self.max_organization = 100.0
        self.strength = 1.0  # Коэффициент боеспособности (от 0.0 до 1.0) на основе наличия снаряжения

        # Накопленное снаряжение дивизии
        self.equipment = dict(stats["equipment"])
        self.max_equipment = dict(stats["equipment"])

        # Battle Plans параметры
        self.target_province = None  # Цель наступления
        self.planning_bonus = 0.0  # Накапливаемый бонус планирования

        # Опыт и уровни ветеранства
        self.experience = 0

        # Кулдауны на атаки и движения
        self.attack_cooldown = 0
        self.movement_cooldown = 0

        # Окопавшиеся (укрепления)
        self.entrenchment_level = 0
        self.entrenchment = 0.0
        self.turns_idle = 0

        # Флаги активности в рамках одного хода
        self.has_moved_this_turn = False
        self.has_attacked_this_turn = False

    @property
    def veterancy_level(self):
        if self.experience >= 1000:
            return "Элитные"
        elif self.experience >= 600:
            return "Ветераны"
        elif self.experience >= 300:
            return "Опытные"
        return "Новички"

    @property
    def veterancy_bonus(self):
        if self.experience >= 1000:
            return 1.50
        elif self.experience >= 600:
            return 1.30
        elif self.experience >= 300:
            return 1.15
        return 1.0

    def update_entrenchment(self):
        """Увеличивает уровень окопов, если дивизия не совершала маневров и не атаковала"""
        if self.has_moved_this_turn or self.has_attacked_this_turn:
            self.turns_idle = 0
            self.entrenchment_level = 0
        else:
            self.turns_idle += 1
            if self.turns_idle >= 2:
                self.entrenchment_level = min(5, self.entrenchment_level + 1)

        self.entrenchment = self.entrenchment_level * 0.1

        # Сброс флагов хода
        self.has_moved_this_turn = False
        self.has_attacked_this_turn = False

    def update_strength(self):
        """Обновляет силу дивизии на основе укомплектованности снаряжением и людьми"""
        total_required_eq = sum(self.max_equipment.values())
        total_current_eq = sum(self.equipment.values())

        eq_ratio = total_current_eq / total_required_eq if total_required_eq > 0 else 1.0
        mp_ratio = self.manpower / self.max_manpower if self.max_manpower > 0 else 1.0

        self.strength = min(eq_ratio, mp_ratio)

    def get_combat_stats(self):
        """Возвращает текущие боевые параметры с учётом укомплектованности, бонусов и окопов"""
        base_stats = self.template.get_stats()
        multiplier = self.strength

        # Влияние командира
        comm_attack_bonus = 1.0 + (self.commander.attack * 0.05) if self.commander else 1.0
        comm_def_bonus = 1.0 + (self.commander.defense * 0.05) if self.commander else 1.0

        # Влияние планирования
        plan_bonus = 1.0 + self.planning_bonus

        # Влияние опыта (ветеранства) на силу атаки
        vet_bonus = self.veterancy_bonus

        # Расчет бонуса за укрепления (удваивается в городе)
        entrench_mult = 0.2 if (self.province and self.province.terrain == TERRAIN_URBAN) else 0.1
        defense_bonus = 1.0 + self.entrenchment_level * entrench_mult

        return {
            "soft_attack": base_stats["soft_attack"] * multiplier * comm_attack_bonus * plan_bonus * vet_bonus,
            "hard_attack": base_stats["hard_attack"] * multiplier * comm_attack_bonus * plan_bonus * vet_bonus,
            "defense": base_stats["defense"] * multiplier * comm_def_bonus * defense_bonus,
            "width": base_stats["width"],
            "supply_use": base_stats["supply_use"]
        }


class Army:
    def __init__(self, name, general=None):
        self.name = name
        self.general = general  # Commander (General)
        self.divisions = []

    def assign_division(self, division):
        if division not in self.divisions:
            self.divisions.append(division)


class ArmyGroup:
    def __init__(self, name, field_marshal=None):
        self.name = name
        self.field_marshal = field_marshal  # Commander (FieldMarshal)
        self.armies = []