# combat.py
import random
from constants import BASE_COMBAT_WIDTH


class Combat:
    def __init__(self, province, attackers, defenders):
        self.province = province  # Провинция, в которой идет бой
        self.attackers = list(attackers)  # Список атакующих Division
        self.defenders = list(defenders)  # Список обороняющихся Division
        self.combat_width = BASE_COMBAT_WIDTH
        self.log = []

    def _apply_damage(self, target, org_damage, str_damage):
        """Применяет урон к дивизии, включая потери снаряжения"""
        # Урон по организации
        target.organization = max(0.0, target.organization - org_damage)

        # Урон по живой силе
        manpower_loss = str_damage * 10
        target.manpower = max(0, target.manpower - manpower_loss)

        # Урон по снаряжению - пропорционально потерям людей
        if target.max_manpower > 0:
            loss_ratio = manpower_loss / target.max_manpower
            # Уменьшаем каждый тип снаряжения пропорционально
            for eq_type in list(target.equipment.keys()):
                if target.max_equipment.get(eq_type, 0) > 0:
                    equipment_loss = int(target.max_equipment[eq_type] * loss_ratio)
                    target.equipment[eq_type] = max(0, target.equipment.get(eq_type, 0) - equipment_loss)

        # Обновляем боеспособность
        target.update_strength()

    def resolve_turn(self):
        """Проводит одну фазу сражения (за один ход)"""
        if not self.attackers or not self.defenders:
            return False  # Битва закончена

        self.log.append(f"--- Битва за {self.province.name} ---")

        # Проверим ширину фронта атакующих
        current_width = 0
        active_attackers = []
        for att in self.attackers:
            stats = att.get_combat_stats()
            if current_width + stats["width"] <= self.combat_width:
                active_attackers.append(att)
                current_width += stats["width"]
            else:
                self.log.append(f"Дивизия {att.name} осталась в резерве из-за ширины фронта.")

        if not active_attackers:
            active_attackers = [self.attackers[0]]  # Минимум одна всегда воюет

        # Атакующие наносят урон
        for att in active_attackers:
            stats_att = att.get_combat_stats()
            target = random.choice(self.defenders)

            # Урон по организации и прочности (базовый расчет)
            damage_org = max(1, int(stats_att["soft_attack"] * 0.15 - target.get_combat_stats()["defense"] * 0.05))
            damage_str = max(1, int(stats_att["hard_attack"] * 0.05))

            self._apply_damage(target, damage_org, damage_str)
            self.log.append(
                f"{att.name} наносит урон по {target.name}. Урон Орг: -{damage_org}, Сила: -{damage_str * 10} человек.")

        # Обороняющиеся наносят урон
        for df in self.defenders:
            stats_df = df.get_combat_stats()
            target = random.choice(active_attackers)

            damage_org = max(1, int(stats_df["soft_attack"] * 0.15 - target.get_combat_stats()["defense"] * 0.05))
            damage_str = max(1, int(stats_df["hard_attack"] * 0.05))

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
                # Пытаемся автоматически отступить в другую дружественную провинцию
                friendly_provinces = [p for p in self.province.owner.provinces if
                                      p != self.province] if self.province.owner else []
                if friendly_provinces:
                    target_retreat = friendly_provinces[0]
                    target_retreat.divisions.append(df)
                    df.province = target_retreat
                    df.organization = 20.0  # Немного восстановим орг после отступления
                    # При отступлении дивизия теряет часть снаряжения
                    for eq_type in list(df.equipment.keys()):
                        df.equipment[eq_type] = int(df.equipment.get(eq_type, 0) * 0.8)
                    df.update_strength()
                else:
                    self.log.append(f"Дивизия {df.name} не нашла путей к отступлению и была уничтожена.")
                    if df in df.province.divisions:
                        df.province.divisions.remove(df)
                    # Полностью удаляем её у владельца
                    owner = df.province.owner
                    if owner and df in owner.divisions:
                        owner.divisions.remove(df)

        return len(self.attackers) > 0 and len(self.defenders) > 0