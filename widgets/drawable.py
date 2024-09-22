from abc import ABC, abstractmethod
import pygame
from typing import overload, override
import pygame

# Base class for widgets
class Drawable(ABC):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0

        self._mouse_pos = (0, 0)
    
    @abstractmethod
    def draw(self, surface: pygame.Surface):
        pass

    def update(self, mouse_pos: tuple[int, int]):
        self._mouse_pos = mouse_pos

    def get_mouse_pos(self):
        return self._mouse_pos
