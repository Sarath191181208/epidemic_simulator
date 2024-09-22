# Column widget for vertical layout with space calculated based on surface
from typing import override
import pygame
from . import Drawable


class Column(Drawable):
    def __init__(self, surface, rect: pygame.Rect, children : list[Drawable] = list(), padding=10, **kwargs):
        self._surface = surface
        self._children : list[Drawable] = children
        self._padding = padding
        self._rect = rect
        self._max_h = kwargs.get("MAX_HEIGHT", float("inf"))
    
    def add_widget(self, widget: Drawable):
        self._children.append(widget)
        self.recalculate_positions()

    def recalculate_positions(self):
        h = min(self._max_h, self._surface.get_height()) 
        total_child_height = sum(widget.height for widget in self._children)
        available_height = h - total_child_height

        assert total_child_height <= h, "Column overflow"
        
        # Calculate dynamic padding between widgets
        if len(self._children) > 1:
            dynamic_padding = available_height // (len(self._children) - 1)
        else:
            dynamic_padding = 0  # No padding needed if there's only one child
        
        dynamic_padding = max(dynamic_padding, self._padding)  # Ensure padding is at least the default
        current_y = self._rect.y

        for widget in self._children:
            widget.x = (self._surface.get_width() - widget.width) // 2
            widget.y = current_y
            current_y += widget.height + dynamic_padding
    
    @override
    def draw(self, surface = None):
        for widget in self._children:
            widget.draw(self._surface)

    def update(self, mouse_pos):
        rel_mouse_pos = (mouse_pos[0] - self._rect.x, mouse_pos[1] - self._rect.y)

        for widget in self._children: 
            widget.update(rel_mouse_pos)

