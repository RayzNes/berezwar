# ui_elements.py
import pygame
from constants import COLOR_PANEL_LIGHT, COLOR_ACCENT, COLOR_TEXT_LIGHT


class Button:
    def __init__(self, x, y, width, height, text, font, bg_color=COLOR_PANEL_LIGHT, hover_color=COLOR_ACCENT):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.bg_color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)

        # Отрисовка текста по центру
        text_surf = self.font.render(self.text, True, COLOR_TEXT_LIGHT)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)