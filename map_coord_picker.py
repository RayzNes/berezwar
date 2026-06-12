# map_coord_picker.py
import sys
import pygame
import json

pygame.init()

SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768


def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Выбор координат провинций - Нажмите ПРОБЕЛ для захвата точек")

    # Загружаем карту
    try:
        map_img = pygame.image.load("map.png").convert()
        map_img = pygame.transform.scale(map_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except:
        print("Ошибка: не найден файл map.jpg")
        return

    points = []  # Текущий полигон
    all_polygons = []  # Список всех сохраненных полигонов
    current_name = "Провинция"

    font = pygame.font.SysFont("Arial", 14)
    font_big = pygame.font.SysFont("Arial", 20, bold=True)

    clock = pygame.time.Clock()
    running = True

    # Инструкция
    instructions = [
        "ИНСТРУКЦИЯ:",
        "1. Обведите район, кликая левой кнопкой мыши по углам/изгибам",
        "2. Нажмите ПРОБЕЛ - сохранить текущий полигон и очистить",
        "3. Нажмите BACKSPACE - удалить последнюю точку",
        "4. Нажмите C - очистить текущий полигон",
        "5. Нажмите S - сохранить все полигоны в файл",
        "6. Нажмите L - загрузить полигоны из файла",
        "7. Нажмите ESC - выйти"
    ]

    while running:
        screen.blit(map_img, (0, 0))

        # Рисуем все сохраненные полигоны
        for idx, poly in enumerate(all_polygons):
            if len(poly) >= 3:
                # Разные цвета для разных провинций
                colors = [(255, 100, 100, 128), (100, 255, 100, 128), (100, 100, 255, 128),
                          (255, 255, 100, 128), (255, 100, 255, 128), (100, 255, 255, 128)]
                color = colors[idx % len(colors)]

                # Заливка с прозрачностью
                surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.polygon(surf, color, poly)
                screen.blit(surf, (0, 0))

                # Контур
                pygame.draw.polygon(screen, (255, 255, 255), poly, 2)

                # Номер провинции
                center_x = sum(p[0] for p in poly) // len(poly)
                center_y = sum(p[1] for p in poly) // len(poly)
                num_text = font_big.render(str(idx + 1), True, (255, 255, 255))
                screen.blit(num_text, (center_x - 10, center_y - 10))

        # Рисуем текущий полигон (в процессе обводки)
        if len(points) > 0:
            if len(points) >= 2:
                pygame.draw.lines(screen, (0, 255, 0), False, points, 3)
            for p in points:
                pygame.draw.circle(screen, (0, 255, 0), p, 5)

        # Точка под курсором
        mouse_pos = pygame.mouse.get_pos()
        pygame.draw.circle(screen, (255, 255, 0), mouse_pos, 3)

        # Текст с координатами
        coord_text = font.render(f"X: {mouse_pos[0]}, Y: {mouse_pos[1]}", True, (255, 255, 255))
        screen.blit(coord_text, (10, 10))

        # Счетчик точек
        points_text = font.render(f"Точек в полигоне: {len(points)}", True, (0, 255, 0))
        screen.blit(points_text, (10, 35))

        # Инструкция на экране
        y_offset = SCREEN_HEIGHT - len(instructions) * 18 - 10
        for inst in instructions:
            inst_surf = font.render(inst, True, (200, 200, 200))
            screen.blit(inst_surf, (10, y_offset))
            y_offset += 18

        # Панель сохраненных провинций справа
        panel_x = SCREEN_WIDTH - 250
        pygame.draw.rect(screen, (30, 30, 30, 200), (panel_x, 0, 250, SCREEN_HEIGHT))
        title = font_big.render("СОХРАНЕННЫЕ ПРОВИНЦИИ", True, (255, 255, 100))
        screen.blit(title, (panel_x + 10, 10))

        y = 50
        for idx, poly in enumerate(all_polygons):
            prov_text = font.render(f"{idx + 1}. Точки: {len(poly)}", True, (255, 255, 255))
            screen.blit(prov_text, (panel_x + 10, y))
            y += 20

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # Сохраняем текущий полигон
                    if len(points) >= 3:
                        all_polygons.append(list(points))
                        print(f"\n=== ПРОВИНЦИЯ {len(all_polygons)} ===")
                        print(f"polygon = {points}")
                        print(f"// {current_name} {len(all_polygons)}")
                        points = []
                    else:
                        print("Нужно минимум 3 точки для полигона!")

                elif event.key == pygame.K_BACKSPACE:
                    if points:
                        removed = points.pop()
                        print(f"Удалена точка: {removed}")

                elif event.key == pygame.K_c:
                    points = []
                    print("Текущий полигон очищен")

                elif event.key == pygame.K_s:
                    # Сохраняем в JSON
                    data = {
                        "polygons": all_polygons,
                        "count": len(all_polygons)
                    }
                    with open("map_coords.json", "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"Сохранено {len(all_polygons)} полигонов в map_coords.json")

                    # Также выводим Python-код для вставки в GameEngine
                    print("\n=== PYTHON КОД ДЛЯ ВСТАВКИ В GameEngine.__init__ ===\n")
                    print("# Координаты провинций (получены через map_coord_picker.py)")
                    for idx, poly in enumerate(all_polygons):
                        print(f"Province({idx + 1}, \"Название провинции\", {poly}),")

                elif event.key == pygame.K_l:
                    try:
                        with open("map_coords.json", "r", encoding="utf-8") as f:
                            data = json.load(f)
                        all_polygons = data["polygons"]
                        print(f"Загружено {len(all_polygons)} полигонов из map_coords.json")
                    except:
                        print("Не удалось загрузить файл")

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # ЛКМ - добавить точку
                    points.append(mouse_pos)
                    print(f"Точка {len(points)}: {mouse_pos}")

        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()