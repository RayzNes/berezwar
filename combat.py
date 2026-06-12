# combat.py
import random
from constants import BASE_COMBAT_WIDTH, TERRAIN_URBAN, TERRAIN_FOREST, TERRAIN_WATER


class Combat:
    def __init__(self, province, attackers, defenders):
        self.province = province  # Провинция, в которой идет бой
        self.attackers = list(attackers)  # Список атакующих Division
        self.defenders = list(defenders)  # Список обороняющихся Division
        self.combat_width = BASE_COMBAT_WIDTH
        self.log = []

    def _apply_damage(self, target, org_damage, str_damage):
        """Применяет урон к дивизии. Возвращает True, если дивизия была разгромлена (организация упала до 0)"""
        old_org = target.organization

        # Урон по организации
        target.organization = max(0.0, target.organization - org_damage)

        # Урон по живой силе
        manpower_loss = str_damage * 10
        target.manpower = max(0, target.manpower - manpower_loss)

        # Урон по снаряжению - пропорционально потерям людей
        if target.max_manpower > 0:
            loss_ratio = manpower_loss / target.max_manpower
            for eq_type in list(target.equipment.keys()):
                if target.max_equipment.get(eq_type, 0) > 0:
                    equipment_loss = int(target.max_equipment[eq_type] * loss_ratio)
                    target.equipment[eq_type] = max(0, target.equipment.get(eq_type, 0) - equipment_loss)

        target.update_strength()
        return old_org > 0 and target.organization <= 0

    def resolve_turn(self, weather_mgr=None):
        """Проводит одну фазу сражения (за один ход)"""
        if not self.attackers or not self.defenders:
            return False  # Битва закончена

        self.log.append(f"--- Битва за {self.province.name} ---")

        # Получаем погодные штрафы
        weather_penalty = {"attack": 1.0, "defense": 1.0}
        if weather_mgr:
            weather_penalty = weather_mgr.get_combat_penalty(self.province)

        # Проверим ширину фронта атакующих и отсеем дивизии на перезарядке
        current_width = 0
        active_attackers = []
        for att in self.attackers:
            if getattr(att, "attack_cooldown", 0) > 0:
                self.log.append(f"Дивизия {att.name} восстанавливает силы и не может наступать.")
                continue

            stats = att.get_combat_stats()
            if current_width + stats["width"] <= self.combat_width:
                active_attackers.append(att)
                current_width += stats["width"]
            else:
                self.log.append(f"Дивизия {att.name} осталась в резерве из-за ширины фронта.")

        if not active_attackers and self.attackers:
            # Если все на кулдауне, то воюет первая (с получением штрафа)
            active_attackers = [self.attackers[0]]

        # Атакующие наносят урон
        for att in active_attackers:
            stats_att = att.get_combat_stats()
            target = random.choice(self.defenders)

            # Получаем показатель защиты обороняющейся дивизии с учетом погодной видимости
            target_defense = target.get_combat_stats()["defense"] * weather_penalty["defense"]
            if self.province.terrain == TERRAIN_URBAN:
                target_defense *= 1.3

            # Урон по организации и прочности (применяется погода)
            damage_org = max(1,
                             int((stats_att["soft_attack"] * 0.15 - target_defense * 0.05) * weather_penalty["attack"]))
            damage_str = max(1, int((stats_att["hard_attack"] * 0.05) * weather_penalty["attack"]))

            # Штраф танков на 50% в Лесу или Городе
            has_tanks = any(b.b_type == "tank" for b in att.template.battalions)
            if self.province.terrain in (TERRAIN_FOREST, TERRAIN_URBAN) and has_tanks:
                damage_org = max(1, int(damage_org * 0.5))
                damage_str = max(1, int(damage_str * 0.5))

            # Применение урона и начисление опыта
            is_destroyed = self._apply_damage(target, damage_org, damage_str)

            # Атакующему: +5 exp за урон, +50 за разгром
            xp_gained = (damage_org + damage_str) * 5
            if is_destroyed:
                xp_gained += 50
                self.log.append(f"{att.name} разгромила вражеские позиции (+50 опыта)!")
            att.experience = min(1000, att.experience + xp_gained)

            # Защитнику: +3 exp за выживание
            target_xp = (damage_org + damage_str) * 3
            target.experience = min(1000, target.experience + target_xp)

            # Установка кулдаунов и флагов активности
            att.attack_cooldown = 2
            att.has_attacked_this_turn = True

            self._apply_damage(target, damage_org, damage_str)
            self.log.append(
                f"{att.name} наносит урон по {target.name}. Урон Орг: -{damage_org}, Сила: -{damage_str * 10} человек.")

        # Обороняющиеся наносят урон (контратакуют)
        for df in self.defenders:
            df.attack_cooldown = 2  # Оборона также изнуряет дивизию
            stats_df = df.get_combat_stats()
            target = random.choice(active_attackers)

            # Базовые параметры защиты у нападающего в полевых условиях атаки
            target_defense = target.get_combat_stats()["defense"] * weather_penalty["defense"]

            damage_org = max(1,
                             int((stats_df["soft_attack"] * 0.15 - target_defense * 0.05) * weather_penalty["attack"]))
            damage_str = max(1, int((stats_df["hard_attack"] * 0.05) * weather_penalty["attack"]))

            # Штраф обороняющихся танков на 50% при плотном городском бое или в лесном массиве
            has_tanks = any(b.b_type == "tank" for b in df.template.battalions)
            if self.province.terrain in (TERRAIN_FOREST, TERRAIN_URBAN) and has_tanks:
                damage_org = max(1, int(damage_org * 0.5))
                damage_str = max(1, int(damage_str * 0.5))

            is_destroyed = self._apply_damage(target, damage_org, damage_str)

            # Начисление опыта контр-атакующему защитнику
            xp_gained = (damage_org + damage_str) * 5
            if is_destroyed:
                xp_gained += 50
                self.log.append(f"{df.name} успешно остановила наступление врага (+50 опыта)!")
            df.experience = min(1000, df.experience + xp_gained)

            # Опыт цели (атакующей) за выживание в бою
            target_xp = (damage_org + damage_str) * 3
            target.experience = min(1000, target.experience + target_xp)

            self._apply_damage(target, damage_org, damage_str)
            self.log.append(
                f"{df.name} отбивается и наносит урон по {target.name}. Урон Орг: -{damage_org}, Сила: -{damage_str * 10} человек.")

        # Проверяем отступающие дивизии с 0 организации
        for att in list(self.attackers):
            if att.organization <= 0:
                self.log.append(f"Дивизия атаки {att.name} потеряла организацию и отступила.")
                self.attackers.remove(att)
                att.target_province = None
                att.planning_bonus = 0.0

        for df in list(self.defenders):
            if df.organization <= 0:
                self.log.append(f"Дивизия обороны {df.name} разгромлена/отступила.")
                self.defenders.remove(df)
                self.province.divisions.remove(df)

                friendly_provinces = [p for p in self.province.owner.provinces if
                                      p != self.province] if self.province.owner else []
                if friendly_provinces:
                    target_retreat = friendly_provinces[0]
                    target_retreat.divisions.append(df)
                    df.province = target_retreat
                    df.organization = 20.0
                    for eq_type in list(df.equipment.keys()):
                        df.equipment[eq_type] = int(df.equipment.get(eq_type, 0) * 0.8)
                    df.update_strength()
                else:
                    self.log.append(f"Дивизия {df.name} не нашла путей к отступлению и была уничтожена.")
                    if df in df.province.divisions:
                        df.province.divisions.remove(df)
                    owner = df.province.owner
                    if owner and df in owner.divisions:
                        owner.divisions.remove(df)

        return len(self.attackers) > 0 and len(self.defenders) > 0