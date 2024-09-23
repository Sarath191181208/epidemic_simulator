import pygame
import sys

from app import App, MouseState
from colors import BLACK, GREEN, GREY, WHITE
from components.grid import GridState, save_grid_as_txt
from components.timer import SECOND, Timer
from const import HEIGHT, WIDTH
from widgets import Column, Button

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()


def main():
    app = App()
    grid = app.grid

    ###### BUTTONS ######
    buttons_col = Column(app.button_surface, app.button_surface_rect, MAX_HEIGHT=600)
    BUTTONS = [
        ("road", GridState.ROAD),
        ("office", GridState.OFFICE),
        ("house", GridState.HOUSE),
        ("mall", GridState.MALL),
        ("school", GridState.SCHOOL),
        ("park", GridState.PARK),
        ("erase", GridState.EMPTY),
    ]

    for button_name, grid_state in BUTTONS:
        buttons_col.add_widget(
            Button(
                button_name,
                app.ops_set_block_type(grid_state),
                button_color=(
                    pygame.Color(*grid_state.value)
                    if grid_state != GridState.EMPTY
                    else pygame.Color(*BLACK)
                ),
                show_border_fn=app.ops_set_border(grid_state),
            )
        )

    buttons_col.add_widget(
        Button(
            "save",
            lambda: save_grid_as_txt(app.get_grid()),
            button_color=pygame.Color(*GREEN),
        )
    )

    # add change to pan state button
    buttons_col.add_widget(
        Button(
            "pan",
            app.ops_set_to_pan_state(),
            button_color=pygame.Color(*GREEN),
        )
    )

    simulation_timer = Timer(
        SECOND / (120), lambda: app.simulation.update_min(), loop=True
    )

    def start_simulation():
        app.simulation.generate_population()
        simulation_timer.start_timer()

    buttons_col.add_widget(
        Button(
            "simulate",
            start_simulation,
            button_color=pygame.Color(*GREEN),
        )
    )

    # create a save timer
    save_timer = Timer(SECOND * 30, lambda: save_grid_as_txt(grid), loop=True)
    save_timer.start_timer()

    # Main loop
    while True:
        save_timer.update()
        simulation_timer.update()

        app.root_surface.fill(WHITE)
        app.map_surface.fill(WHITE)
        app.button_surface.fill(GREY)
        app.hud_surface.fill(GREY)

        mouse_pos = pygame.mouse.get_pos()
        left_click = pygame.mouse.get_pressed()[0]

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # handle key press events
            if event.type == pygame.KEYDOWN:
                app.handle_key_click(event)

            # scroll to zoom
            if event.type == pygame.MOUSEBUTTONDOWN:
                app.handle_zoom(event)

            # handle mouse motion for drag
            if event.type == pygame.MOUSEMOTION:
                if app.mouse_state == MouseState.PANNING and left_click:
                    app.update_offset(event.rel)

                elif app.mouse_state == MouseState.IS_PLACING:
                    BUFFER_SIZE = 20
                    if mouse_pos[0] < (
                        app.MAP_WIDTH - BUFFER_SIZE
                    ) and app.map_surface.get_rect().collidepoint(*mouse_pos):
                        app.place_blocks_in_grid(mouse_pos)

        # check if released
        left_release = not left_click
        if app.mouse_state == MouseState.IS_PLACING and left_release:
            app.is_placing_first_coords = None
            app.is_placing_last_coords = None
            app.mouse_state = MouseState.PLACING

        # check for mouse click
        if app.mouse_state == MouseState.PLACING:
            app.update_place_blocks_state(left_click, mouse_pos)

        # Set the cursor based on the mouse state
        if app.mouse_state == MouseState.PLACING:
            # pygame.mouse.set_cursor(*pygame.cursors.diamond)
            # the cursor should have a color at the center
            cx, cy = 16, 16
            cursor_surf = pygame.Surface((32, 32), pygame.SRCALPHA)

            # draw a circle
            pygame.draw.circle(
                cursor_surf, grid.current_block.value or (GREY), (cx, cy), 12
            )
            # draw a black outline around the circle
            pygame.draw.circle(cursor_surf, BLACK, (cx, cy), 12, 2)
            # draw a cross
            pygame.draw.line(cursor_surf, BLACK, (cx - 5, cy), (cx + 5, cy), 2)
            pygame.draw.line(cursor_surf, BLACK, (cx, cy - 5), (cx, cy + 5), 2)

            # Create the cursor
            cursor = pygame.cursors.Cursor((16, 16), cursor_surf)
            # set the cursor
            pygame.mouse.set_cursor(cursor)

        elif app.mouse_state == MouseState.PANNING:
            pygame.mouse.set_cursor(
                *pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_SIZEALL)
            )

        # Draw and update the buttons
        buttons_col.update(pygame.mouse.get_pos())
        buttons_col.draw()

        # Create a text on app.hud_surface with grid.day, grid.hour, grid.sec use pygame
        font = pygame.font.Font(None, 36)
        text = font.render(
            f"Day: {app.simulation.day}, Hour: {app.simulation.hrs}, Sec: {app.simulation.secs}",
            True,
            BLACK,
        )
        app.hud_surface.blit(text, (10, 10))

        # Draw the app
        app.draw()

        # blit the root surface
        screen.blit(app.root_surface, (0, 0))

        # Update display
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    main()
