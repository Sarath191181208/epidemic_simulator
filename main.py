import pygame
import sys
from enum import Enum, unique

from colors import *
from components.grid import Grid, GridState, load_grid_from_txt, save_grid_as_txt
from widgets import Column, Button

# Constants
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
ZOOM_SCALE = 1.1
BUTTON_WIDTH, BUTTON_HEIGHT = 100, 40

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


@unique
class MouseState(Enum):
    PANNING = 1
    PLACING = 2
    IS_PLACING = 3


def main():
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
    map_surface = pygame.Surface((cols * GRID_SIZE + BUFFER_SIZE, rows * GRID_SIZE + BUFFER_SIZE))

    # Create the button surface (action view)
    button_surface_rect = pygame.Rect(MAP_WIDTH, 0, BUTTON_PANEL_WIDTH, HEIGHT)
    button_surface = pygame.Surface((BUTTON_PANEL_WIDTH, HEIGHT))

    # Pass the surface to the grid class
    grid = load_grid_from_txt()
    if grid is None:
        grid = Grid(cols, rows, GRID_SIZE, map_surface)


    # Camera and zoom variables
    offset_x, offset_y = 0, 0
    zoom_level = 1.0

    # Set the current app state
    mouse_state = MouseState.PLACING

    def set_block_type(block_type: GridState):
        def set_block():
            nonlocal mouse_state
            mouse_state = MouseState.PLACING
            grid.current_block = block_type
        return set_block

    buttons_col = Column(button_surface, button_surface_rect, MAX_HEIGHT=300)
    BUTTONS = [
        ("road", GridState.ROAD),
        ("office", GridState.OFFICE),
        ("house", GridState.HOUSE),
        ("mall", GridState.MALL),
        ("school", GridState.SCHOOL),
        ("park", GridState.PARK),
        ("erase", GridState.EMPTY)
    ]
    for button_name, grid_state in BUTTONS:
        buttons_col.add_widget(
            Button(
                button_name,
                set_block_type(grid_state),
                button_color=pygame.Color(*grid_state.value) if grid_state != GridState.EMPTY else pygame.Color(*GREY),
            )
        )

    is_placing_first_coords = None
    is_placing_last_coords = None

    # Main loop
    while True:
        root_surface.fill(WHITE)
        map_surface.fill(WHITE)
        button_surface.fill(GREY)

        mouse_pos = pygame.mouse.get_pos()
        left_click = pygame.mouse.get_pressed()[0]
        right_click = pygame.mouse.get_pressed()[2]

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle the chaning of mouse states if h is pressed
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_h:
                    mouse_state = MouseState.PANNING
                if event.key == pygame.K_v:
                    mouse_state = MouseState.PLACING
                if event.key == pygame.K_s:
                    save_grid_as_txt(grid)
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Zooming
                if event.button == 4:  # Scroll up to zoom in
                    zoom_level *= ZOOM_SCALE
                elif event.button == 5:  # Scroll down to zoom out
                    zoom_level /= ZOOM_SCALE
            if event.type == pygame.MOUSEMOTION:
                if mouse_state == MouseState.PANNING and left_click:
                    dx, dy = event.rel
                    offset_x += dx
                    offset_y += dy
                elif mouse_state == MouseState.IS_PLACING:
                    if map_surface.get_rect().collidepoint(*mouse_pos):
                        grid_x = int((mouse_pos[0] - offset_x) / (GRID_SIZE * zoom_level))
                        grid_y = int((mouse_pos[1] - offset_y) / (GRID_SIZE * zoom_level))

                        # clear the previous block 
                        assert is_placing_first_coords is not None 
                        assert is_placing_last_coords is not None
                        grid.place_blocks(is_placing_first_coords, is_placing_last_coords, GridState.EMPTY)

                        # place the new block
                        is_placing_last_coords = (grid_x, grid_y)
                        grid.place_blocks(is_placing_first_coords, (grid_x, grid_y), grid.current_block)

        # check if released 
        if mouse_state == MouseState.IS_PLACING and not left_click:
            is_placing_first_coords = None
            is_placing_last_coords = None
            mouse_state = MouseState.PLACING

        # check for mouse click
        if mouse_state == MouseState.PLACING:
            mouse_x, mouse_y = mouse_pos
            # check click on map surface use collide point
            if map_surface.get_rect().collidepoint(mouse_x, mouse_y):
                grid_x = int((mouse_x - offset_x) / (GRID_SIZE * zoom_level))
                grid_y = int((mouse_y - offset_y) / (GRID_SIZE * zoom_level))
                if left_click:
                    is_placing_first_coords = (grid_x, grid_y)
                    is_placing_last_coords = (grid_x, grid_y)
                    mouse_state = MouseState.IS_PLACING

        # Set the cursor based on the mouse state
        if mouse_state == MouseState.PLACING:
            pygame.mouse.set_cursor(*pygame.cursors.diamond)
        elif mouse_state == MouseState.PANNING:
            pygame.mouse.set_cursor(
                *pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_SIZEALL)
            )

        # Draw the grid
        grid.draw_grid()

        # Draw the buttons
        buttons_col.update(pygame.mouse.get_pos())
        buttons_col.draw()

        # set limits for zoom level 
        zoom_level = max(0.5, min(zoom_level, 2))
        # Create a scaled version of the grid surface for zooming
        zoomed_surface = pygame.transform.scale(
            map_surface,
            (
                int(map_surface.get_width() * zoom_level),
                int(map_surface.get_height() * zoom_level),
            ),
        )

        # Define the portion of the zoomed surface (map) to display on the screen (viewport)
        viewport = pygame.Rect(-offset_x, -offset_y, MAP_WIDTH, MAP_HEIGHT)

        # Blit the zoomed map surface onto the root surface
        root_surface.blit(zoomed_surface, (0, 0), viewport)

        # Blit the button panel surface onto the root surface (on the right side)
        root_surface.blit(button_surface, button_surface_rect.topleft)

        # Finally, blit the root surface to the screen
        screen.blit(root_surface, (0, 0))

        # Update display
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
