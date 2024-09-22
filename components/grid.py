
import os 
from datetime import datetime

import pygame
from enum import Enum, unique

from colors import OFFICE_COLOR, HOUSE_COLOR, MALL_COLOR, PARK_COLOR, ROAD_COLOR, SCHOOL_COLOR, GREY

@unique
class GridState(Enum):
    ROAD = ROAD_COLOR
    OFFICE = OFFICE_COLOR
    HOUSE = HOUSE_COLOR
    MALL = MALL_COLOR
    SCHOOL = SCHOOL_COLOR
    PARK = PARK_COLOR
    EMPTY = None

class Grid:
    def __init__(self, cols, rows, grid_size, surface):
        self.cols = cols
        self.rows = rows
        self.grid_size = grid_size
        self.grid: list[list[GridState]] = [[GridState.EMPTY for _ in range(cols)] for _ in range(rows)]
        self.surface = surface
        self.current_block: GridState = GridState.ROAD

    def draw_grid(self):
        for y in range(self.rows):
            for x in range(self.cols):
                rect = pygame.Rect(
                    x * self.grid_size,
                    y * self.grid_size,
                    self.grid_size,
                    self.grid_size,
                )
                pygame.draw.rect(self.surface, GREY, rect, 1)

                block = self.grid[y][x]
                if block != GridState.EMPTY: 
                    pygame.draw.rect(self.surface, block.value, rect)

    def check_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.cols and 0 <= y < self.rows

    def place_blocks(self, p1: tuple[int, int], p2: tuple[int, int], block_type: GridState):
        x1, y1 = p1 
        x2, y2 = p2

        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        if not self.check_in_bounds(x1, y1) or not self.check_in_bounds(x2, y2):
            return 
        
        for _x in range(x1, x2+1):
            for _y in range(y1, y2+1):
                self.place_block(_x, _y, block_type)

    def place_block(self, x: int, y: int, block_type: GridState):
        if self.check_in_bounds(x, y):
            self.grid[y][x] = block_type

    def remove_block(self, x: int, y: int):
        if self.check_in_bounds(x, y):
            self.place_block(x, y, GridState.EMPTY)

def save_grid_as_txt(grid: "Grid", filename: str | None = None):
    if filename is None:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"saves/grid_{ts}.txt"

    # create saves folder if it doesn't exist 
    if not os.path.exists("saves"):
        os.makedirs("saves")

    # create a file with the timestamp 
    with open(filename, "w") as f:
        # write the grid dimlensions in the first line 
        f.write(f"{grid.cols}x{grid.rows}\n")
        for row in grid.grid:
            for block in row:
                f.write(f"{block.name} ")
            f.write("\n")

def load_grid_from_txt(surface: pygame.Surface, grid_size: int, filename: str | None = None) -> "Grid | None":
    # checkc for saves folder 
    if not os.path.exists("saves"): 
        return
    grid = Grid(0, 0, grid_size, surface)
    # if filename is none check the latest file 
    if filename is None:
        files = os.listdir("saves")
        if not files:
            return 
        filename = max(files)
    
    # open the file and read the grid dimensions 
    with open(f"saves/{filename}", "r") as f:
        cols, rows = map(int, f.readline().strip().split("x"))
        grid.cols = cols
        grid.rows = rows
        grid.grid = [[GridState.EMPTY for _ in range(cols)] for _ in range(rows)]

        # read the grid blocks 
        for y, line in enumerate(f):
            blocks = line.strip().split(" ")
            for x, block in enumerate(blocks):
                grid.grid[y][x] = GridState[block]

    return grid
