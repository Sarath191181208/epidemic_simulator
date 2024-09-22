import pygame
from functools import wraps
from typing import Callable

from . import Drawable

WHITE = (255, 255, 255)
BUTTON_COLOR = pygame.Color(100, 100, 100)
BUTTON_WIDTH, BUTTON_HEIGHT = 100, 40


class Button(Drawable):
    def __init__(self, text: str, action: Callable[[], None], width: int = BUTTON_WIDTH, height: int = BUTTON_HEIGHT, button_color: pygame.Color = BUTTON_COLOR, border_color: pygame.Color | None = None, show_border_fn: Callable[[], bool] | None = None):
        super().__init__(width, height)
        self.text = text
        self.action = action
        self.font = pygame.font.SysFont(None, 24)
        self.button_color = button_color

        # calc the hover color using hsv from color 
        h, s, v, a = button_color.hsla

        # adjust v 
        v = min(max(int(v*0.8), 0), 100)

        # assign the color 
        self.hover_button_color = pygame.Color(0, 0, 0)
        self.hover_button_color.hsla = (h, s, v, a)
        
        self.border_color = border_color or BUTTON_COLOR
        self.show_border_fn = show_border_fn


    def draw(self, surface: pygame.Surface):
        # Get the mouse position and check if it's hovering over the button
        mouse_pos = self.get_mouse_pos()
        color = self.hover_button_color if self.is_hovered(mouse_pos) else self.button_color
        
        # Draw the button rectangle
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))

        # check the show_border_fn 
        if self.show_border_fn is not None and self.show_border_fn():
            pygame.draw.rect(surface, self.border_color, (self.x, self.y, self.width, self.height), 2)

        # check for click 
        self.check_click(mouse_pos)

        # Render the text and center it inside the button
        text_surface = self.font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(
            center=(self.x + self.width // 2, self.y + self.height // 2)
        )
        surface.blit(text_surface, text_rect)

    def is_hovered(self, mouse_pos):
        return (
            self.x <= mouse_pos[0] <= self.x + self.width
            and self.y <= mouse_pos[1] <= self.y + self.height
        )

    def check_click(self, mouse_pos):
        left_click = pygame.mouse.get_pressed()[0]
        if self.is_hovered(mouse_pos) and left_click:
            self.action()
        return None
