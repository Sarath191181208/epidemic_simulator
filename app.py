
from enum import Enum, unique

import pygame 
from components.grid import Grid, GridState, load_grid_from_txt, save_grid_as_txt
from const import BUTTON_WIDTH, WIDTH, HEIGHT, BLOCK_SIZE, ZOOM_SCALE


@unique
class MouseState(Enum):
    PANNING = 1
    PLACING = 2
    IS_PLACING = 3

class App:
    cols, rows = 100, 100

    BUTTON_PANEL_WIDTH = BUTTON_WIDTH + 20

    # Dimensions
    MAP_WIDTH = (
        WIDTH - BUTTON_PANEL_WIDTH
    )  # Adjust map width to leave space for buttons
    MAP_HEIGHT = HEIGHT

    # Create the root surface (which will hold both the map and button surfaces)
    root_surface = pygame.Surface((WIDTH, HEIGHT))

    # Create the map surface
    BUFFER_SIZE = 10
    map_surface = pygame.Surface(
        (cols * BLOCK_SIZE + BUFFER_SIZE, rows * BLOCK_SIZE + BUFFER_SIZE)
    )

    # Create the button surface (action view)
    button_surface_rect = pygame.Rect(MAP_WIDTH, 0, BUTTON_PANEL_WIDTH, HEIGHT)
    button_surface = pygame.Surface((BUTTON_PANEL_WIDTH, HEIGHT))

    # Pass the surface to the grid class
    _grid = load_grid_from_txt(map_surface, BLOCK_SIZE)
    if _grid is None:
        _grid = Grid(cols, rows, BLOCK_SIZE, map_surface)
    grid: Grid = _grid

    # Camera and zoom variables
    offset_x, offset_y = 0, 0
    zoom_level = 1.0

    # Set the current app state
    mouse_state = MouseState.PLACING

    # used to store the first and last coords of the block being placed
    is_placing_first_coords = None
    is_placing_last_coords = None

    def handle_key_click(self, event: pygame.event.Event):
        grid = self.grid
        # check for num keys and handle trigger the keypress from buttons
        if event.key == pygame.K_1:
            grid.current_block = GridState.ROAD
        if event.key == pygame.K_2:
            grid.current_block = GridState.OFFICE
        if event.key == pygame.K_3:
            grid.current_block = GridState.HOUSE
        if event.key == pygame.K_4:
            grid.current_block = GridState.MALL
        if event.key == pygame.K_5:
            grid.current_block = GridState.SCHOOL
        if event.key == pygame.K_6:
            grid.current_block = GridState.PARK
        if event.key == pygame.K_0:
            grid.current_block = GridState.EMPTY
        if event.key == pygame.K_ESCAPE:
            self.mouse_state = MouseState.PLACING
        if event.key == pygame.K_h:
            self.mouse_state = MouseState.PANNING
        if event.key == pygame.K_v:
            self.mouse_state = MouseState.PLACING
        if event.key == pygame.K_s:
            save_grid_as_txt(grid)

    def handle_zoom(self, event: pygame.event.Event):
        # Zooming
        if event.button == 4:  # Scroll up to zoom in
            self.zoom_level *= ZOOM_SCALE
        elif event.button == 5:  # Scroll down to zoom out
            self.zoom_level /= ZOOM_SCALE
        self.zoom_level = max(0.5, min(self.zoom_level, 2))

    def update_offset(self, rel: tuple[int, int]):
        dx, dy = rel
        self.offset_x += dx
        self.offset_y += dy

    def set_block_type(self, block_type: GridState):
        def set_block():
            self.mouse_state = MouseState.PLACING
            self.grid.current_block = block_type

        return set_block

    def set_to_pan_state(self):
        def change_to_pan_state():
            self.mouse_state = MouseState.PANNING

        return change_to_pan_state

    def get_grid_coords(self, mouse_pos: tuple[int, int]) -> tuple[int, int]:
        offset_x, offset_y = self.offset_x, self.offset_y
        zoom_level = self.zoom_level

        grid_x = int((mouse_pos[0] - offset_x) / (BLOCK_SIZE * zoom_level))
        grid_y = int((mouse_pos[1] - offset_y) / (BLOCK_SIZE * zoom_level))

        return grid_x, grid_y

    def update_place_blocks_state(self, left_click: bool, mouse_pos: tuple[int, int]):
        mouse_x, mouse_y = mouse_pos
        # check click on map surface use collide point
        if self.map_surface.get_rect().collidepoint(mouse_x, mouse_y):
            grid_x, grid_y = self.get_grid_coords(mouse_pos)
            if left_click:
                self.is_placing_first_coords = (grid_x, grid_y)
                self.is_placing_last_coords = (grid_x, grid_y)
                self.mouse_state = MouseState.IS_PLACING

    def place_blocks_in_grid(self, mouse_pos: tuple[int, int]):
        grid = self.grid
        grid_x, grid_y = self.get_grid_coords(mouse_pos)

        # clear the previous block
        assert self.is_placing_first_coords is not None
        assert self.is_placing_last_coords is not None
        grid.place_blocks(
            self.is_placing_first_coords,
            self.is_placing_last_coords,
            GridState.EMPTY,
        )

        # place the new block
        self.is_placing_last_coords = (grid_x, grid_y)
        grid.place_blocks(
            self.is_placing_first_coords,
            (grid_x, grid_y),
            grid.current_block,
        )

    def draw(self):
        zoom_level = self.zoom_level 
        offset_x, offset_y = self.offset_x, self.offset_y

        # Draw the grid
        self.grid.draw_grid()

        # Create a scaled version of the grid surface for zooming
        zoomed_surface = pygame.transform.scale(
            self.map_surface,
            (
                int(self.map_surface.get_width() * zoom_level),
                int(self.map_surface.get_height() * zoom_level),
            ),
        )

        # Define the portion of the zoomed surface (map) to display on the screen (viewport)
        viewport = pygame.Rect(-offset_x, -offset_y, self.MAP_WIDTH, self.MAP_HEIGHT)

        # Blit the zoomed map surface onto the root surface
        self.root_surface.blit(zoomed_surface, (0, 0), viewport)

        # Blit the button panel surface onto the root surface (on the right side)
        self.root_surface.blit(self.button_surface, self.button_surface_rect.topleft)
