# weather.py
import random


class WeatherManager:
    def __init__(self):
        self.seasons = ["spring", "summer", "autumn", "winter"]
        self.season_index = 0
        self.season = self.seasons[self.season_index]
        self.weathers = ["clear", "rain", "snowstorm", "blizzard"]
        self.current_weather = "clear"
        self.turn_counter = 0

    def update(self):
        """Обновляет ход, сезон и тип погоды"""
        self.turn_counter += 1

        # Смена сезона каждые 10 ходов
        if self.turn_counter % 10 == 0:
            self.season_index = (self.season_index + 1) % len(self.seasons)
            self.season = self.seasons[self.season_index]

        # 10% шанс изменения погоды или принудительно на первом ходу
        if random.random() < 0.10 or self.turn_counter == 1:
            if self.season == "winter":
                self.current_weather = random.choice(["clear", "snowstorm", "blizzard"])
            elif self.season == "summer":
                self.current_weather = random.choice(["clear", "rain"])
            else:
                self.current_weather = random.choice(["clear", "rain", "snowstorm"])

    def get_combat_penalty(self, province):
        """Возвращает коэффициенты ослабления атаки и защиты"""
        atk_mult = 1.0
        def_mult = 1.0

        if self.current_weather == "rain":
            atk_mult *= 0.8
            def_mult *= 0.9
        elif self.current_weather == "snowstorm":
            atk_mult *= 0.6
            def_mult *= 0.7
        elif self.current_weather == "blizzard":
            atk_mult *= 0.4
            def_mult *= 0.5

        # Штраф зимнего сезона
        if self.season == "winter":
            atk_mult *= 0.9
            def_mult *= 0.9

        return {"attack": atk_mult, "defense": def_mult}