# Row widget for horizontal layout with space calculated based on surface
from . import Drawable


class Row:
    def __init__(self, surface, x=0, y=0, padding=10):
        self._surface = surface
        self._children: list[Drawable] = []
        self._padding = padding
        self._start_x = x
        self._start_y = y

    def add_widget(self, widget: Drawable):
        self._children.append(widget)
        self.recalculate_positions()

    def recalculate_positions(self):
        total_child_width = sum(widget.width for widget in self._children)
        available_width = self._surface.get_width() - total_child_width

        # Calculate dynamic padding between widgets
        if len(self._children) > 1:
            dynamic_padding = available_width // (len(self._children) - 1)
        else:
            dynamic_padding = 0  # No padding needed if there's only one child

        dynamic_padding = max(
            dynamic_padding, self._padding
        )  # Ensure padding is at least the default

        current_x = self._start_x
        for widget in self._children:
            widget.x = current_x
            widget.y = self._start_y + (self._surface.get_height() - widget.height) // 2
            current_x += widget.width + dynamic_padding

    def draw(self):
        for widget in self._children:
            widget.draw(self._surface)
