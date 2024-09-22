from typing import override
import pygame
from . import Drawable


class Column(Drawable):
    def __init__(self, surface, rect: pygame.Rect, child : Drawable, padding=10, **kwargs):
        self._surface = surface
        self.child = child
        self._padding = padding
        self._rect = rect
        self._max_h = kwargs.get("MAX_HEIGHT", float("inf"))
    
    @override
    def draw(self, surface = None):
        self.child.draw(self._surface)

    def update(self, mouse_pos):
        rel_mouse_pos = (mouse_pos[0] - self._rect.x, mouse_pos[1] - self._rect.y)
        self.child.update(rel_mouse_pos)

