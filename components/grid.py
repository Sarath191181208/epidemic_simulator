import os
from datetime import datetime
import random
from typing import DefaultDict

import pygame
from enum import Enum, unique

from colors import (
    OFFICE_COLOR,
    HOUSE_COLOR,
    MALL_COLOR,
    PARK_COLOR,
    ROAD_COLOR,
    SCHOOL_COLOR,
    GREY,
)
from .person import Day, Person, PersonState, TimeTable


@unique
class GridState(Enum):
    ROAD = ROAD_COLOR
    OFFICE = OFFICE_COLOR
    HOUSE = HOUSE_COLOR
    MALL = MALL_COLOR
    SCHOOL = SCHOOL_COLOR
    PARK = PARK_COLOR
    EMPTY = None


PLACES = [
    GridState.OFFICE,
    GridState.MALL,
    GridState.SCHOOL,
    GridState.PARK,
]


def get_min_max_time_limit(state: GridState) -> tuple[int, int]:
    if state == GridState.OFFICE:
        return 4, 8
    elif state == GridState.MALL:
        return 4, 10
    elif state == GridState.SCHOOL:
        return 8, 12
    elif state == GridState.PARK:
        return 2, 6
    raise Exception("Invalid state")


class Grid:
    def __init__(self, cols, rows, grid_size, surface):
        self.cols = cols
        self.rows = rows
        self.grid_size = grid_size
        self.grid: list[list[GridState]] = [
            [GridState.EMPTY for _ in range(cols)] for _ in range(rows)
        ]
        self.surface = surface
        self.current_block: GridState = GridState.ROAD

        self.block_ids: list[list[int]] = [[-1] * self.cols for _ in range(self.rows)]
        self.people: list[Person] = []
        self.path_cache = {}
        self.hrs: int = 0
        self.secs: int = 0
        self.day = Day.Monday

    def generate_population(self):
        blocks = [[-1 for _ in range(self.cols)] for _ in range(self.rows)]
        block_id_to_capacity = DefaultDict(int)
        block_id = 0
        sm_blocks = 0

        def dfs(c, r, block_id):
            nonlocal sm_blocks
            if (
                not self.check_in_bounds(c, r)
                or blocks[r][c] != -1
                or self.grid[r][c] == GridState.EMPTY
            ):
                return
            if self.grid[r][c] == GridState.ROAD:
                return
            blocks[r][c] = block_id
            sm_blocks += 1
            block_id_to_capacity[block_id] += 1
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                dfs(c + dx, r + dy, block_id)

        for r in range(self.rows):
            for c in range(self.cols):
                if not blocks[r][c] == -1:
                    continue
                if (
                    self.grid[r][c] == GridState.EMPTY
                    or self.grid[r][c] == GridState.ROAD
                ):
                    continue
                dfs(c, r, block_id)
                block_id += 1

        self.block_ids = blocks

        # collect avaiable blocks
        available_blocks = {
            (r, c)
            for c in range(self.cols)
            for r in range(self.rows)
            if blocks[r][c] != -1
            and self.grid[r][c] not in [GridState.HOUSE, GridState.ROAD]
        }

        # collect available houses
        available_houses = {
            (r, c)
            for c in range(self.cols)
            for r in range(self.rows)
            if blocks[r][c] != -1 and self.grid[r][c] == GridState.HOUSE
        }

        # collect max capacity of people
        max_people_capacity = len(available_houses)

        print("Max people capacity: ", max_people_capacity)
        print("Available blocks: ", len(available_blocks))
        print("Available houses: ", len(available_houses))

        # generate population
        population = random.randint(0, max_people_capacity)

        def get_random_person() -> Person:
            house_location = random.choice(list(available_houses))
            # remove the house from the available houses
            available_houses.remove(house_location)
            # get house id
            house_id = house_location

            return Person(
                TimeTable(
                    Monday=[(house_id, random.randint(4, 8)), (house_id, -1)],
                    Tuesday=[(house_id, random.randint(4, 8)), (house_id, -1)],
                    Wednesday=[(house_id, random.randint(4, 8)), (house_id, -1)],
                    Thursday=[(house_id, random.randint(4, 8)), (house_id, -1)],
                    Friday=[(house_id, random.randint(4, 8)), (house_id, -1)],
                    Saturday=[(house_id, random.randint(4, 8)), (house_id, -1)],
                ),
                loc=house_location,
            )

        # generate people
        people = [get_random_person() for _ in range(population)]
        for day in range(0, 6):
            available_cpy = available_blocks.copy()
            for person in people:
                day_schedule = person.get_day_schedule(Day(day))
                # pick from available_blocks
                r, c = random.choice(list(available_cpy))
                # remove the place from available blocks
                available_cpy.remove((r, c))

                # get the block block_type
                rand_place_type = self.grid[r][c]

                # get random time limit
                rand_time = random.randint(*get_min_max_time_limit(rand_place_type))

                # insert the place into the day schedule
                day_schedule.insert(1, ((r, c), rand_time))

        self.people = people

    def update_hr(self):
        for person in self.people:
            person.update(self.day)

    def update_min(self):
        self.secs += 1
        if self.secs == 60:
            self.secs = 0
            self.hrs += 1
            self.update_hr()
            if self.hrs == 24:
                self.hrs = 0
                self.day = Day((self.day.value + 1) % 6)
        # move the person if they are in moving state
        moving_persons = [
            (i, person)
            for i, person in enumerate(self.people)
            if person.state == PersonState.Moving
        ]

        # get all the people locations
        people_locs = {person.loc for person in self.people}

        for i, person in moving_persons:
            if i in self.path_cache:
                path = self.path_cache[i]
            else:
                path = self.calculate_path(person)
                self.path_cache[i] = path

            if not path:
                continue

            dest = path[0]
            if dest in people_locs:
                continue

            path.pop(0)
            person.loc = dest
            people_locs.add(dest)
            people_locs.remove(person.loc)

    def get_closest_road(self, loc: tuple[int, int]) -> tuple[int, int] | None:
        # find the nearest road which should be connected to the current block
        def dfs(r, c, self_state: GridState, visited: set):
            if not self.check_in_bounds(c, r) or (r, c) in visited:
                return None
            if self.grid[r][c] == GridState.ROAD:
                return r, c
            if self.grid[r][c] != self_state:
                return None
            visited.add((r, c))
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                point = dfs(r + dy, c + dx, self_state, visited)
                if point is not None:
                    return point

        visited = set()
        r, c = loc
        return dfs(r, c, self.grid[r][c], visited)

    def calculate_path(self, person: Person):
        r, c = person.loc
        # check if the person isn't on a road
        road_loc = None
        if self.grid[r][c] == GridState.ROAD:
            road_loc = r, c
        road_loc = road_loc or self.get_closest_road(person.loc)
        if road_loc is None:
            raise Exception(f"No road found from location {person.loc}")

        src = road_loc
        dest = person.get_dest(self.day)
        return self.get_a_star_path(src, dest)

    def get_a_star_path(self, src, dest):
        r, c = dest
        dest_type = self.grid[r][c]

        def match(p1: tuple[int, int], p2: tuple[int, int]) -> bool:
            r, c = p1
            p1_id = self.block_ids[r][c]
            r, c = p2
            p2_id = self.block_ids[r][c]
            return p1_id == p2_id

        def is_dest(loc: tuple[int, int]) -> bool:
            ng = get_neighbours(loc)
            for n in ng:
                if match(n, dest):
                    return True
            return False

        def h(loc1, loc2):
            return abs(loc1[0] - loc2[0]) + abs(loc1[1] - loc2[1])

        def get_neighbours(loc):
            r, c = loc
            neighbours = []
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                if self.check_in_bounds(c + dx, r + dy) and self.grid[r + dy][
                    c + dx
                ] in [GridState.ROAD, dest_type]:
                    neighbours.append((r + dy, c + dx))
            return neighbours

        # find the path from src to dest
        def a_star(src, dest):
            open_list = [src]
            visited_set = set()
            g = {src: 0}
            f = {src: h(src, dest)}
            came_from = dict()

            while open_list:
                current = min(open_list, key=lambda x: f[x])
                if is_dest(current):
                    path = [dest]
                    while current != src:
                        path.append(current)
                        current = came_from[current]
                    path.append(src)
                    return path[::-1]

                open_list.remove(current)
                visited_set.add(current)

                for neighbour in get_neighbours(current):
                    if neighbour in visited_set:
                        continue
                    if neighbour not in open_list:
                        open_list.append(neighbour)

                    tentative_g = g[current] + 1
                    if tentative_g >= g.get(neighbour, float("inf")):
                        continue

                    came_from[neighbour] = current
                    g[neighbour] = tentative_g
                    f[neighbour] = g[neighbour] + h(neighbour, dest)

            return []

        return a_star(src, dest)

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
                    clr = block.value
                    pygame.draw.rect(self.surface, clr, rect)

        # draw the pepole as circles
        for person in self.people:
            r, c = person.loc
            rect = pygame.Rect(
                c * self.grid_size,
                r * self.grid_size,
                self.grid_size,
                self.grid_size,
            )
            pygame.draw.circle(self.surface, (255, 0, 0), rect.center, 10)

    def check_in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.cols and 0 <= y < self.rows

    def place_blocks(
        self, p1: tuple[int, int], p2: tuple[int, int], block_type: GridState
    ):
        x1, y1 = p1
        x2, y2 = p2

        x1, x2 = min(x1, x2), max(x1, x2)
        y1, y2 = min(y1, y2), max(y1, y2)

        if not self.check_in_bounds(x1, y1) or not self.check_in_bounds(x2, y2):
            return

        for _x in range(x1, x2 + 1):
            for _y in range(y1, y2 + 1):
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


def load_grid_from_txt(
    surface: pygame.Surface, grid_size: int, filename: str | None = None
) -> "Grid | None":
    # checkc for saves folder
    if not os.path.exists("saves"):
        return
    grid = None
    # if filename is none check the latest file
    if filename is None:
        files = os.listdir("saves")
        if not files:
            return
        filename = max(files)

    # open the file and read the grid dimensions
    with open(f"saves/{filename}", "r") as f:
        cols, rows = map(int, f.readline().strip().split("x"))
        grid = Grid(cols, rows, grid_size, surface)

        # read the grid blocks
        for y, line in enumerate(f):
            blocks = line.strip().split(" ")
            for x, block in enumerate(blocks):
                grid.grid[y][x] = GridState[block]

    return grid
