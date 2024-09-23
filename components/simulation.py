import random
from typing import DefaultDict

import pygame
from components.grid import Grid, GridState
from components.person import Day, Person, PersonState, TimeTable


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


class Simulation:
    def __init__(self, grid: Grid):
        self.cols, self.rows = grid.cols, grid.rows
        self.block_ids: list[list[int]] = [[-1] * grid.cols for _ in range(grid.rows)]
        self.people: list[Person] = []
        self.path_cache = {}
        self.hrs: int = 0
        self.secs: int = 0
        self.day = Day.Monday

        self.grid = grid

    def draw(self): 
        # draw the pepole as circles
        for person in self.people:
            r, c = person.loc
            rect = pygame.Rect(
                c * self.grid.grid_size,
                r * self.grid.grid_size,
                self.grid.grid_size,
                self.grid.grid_size,
            )
            pygame.draw.circle(self.grid.surface, (255, 0, 0), rect.center, 10)


    def generate_population(self):
        blocks = [[-1 for _ in range(self.cols)] for _ in range(self.rows)]
        block_id_to_capacity = DefaultDict(int)
        block_id = 0
        sm_blocks = 0

        def dfs(c, r, block_id):
            nonlocal sm_blocks
            if (
                not self.grid.check_in_bounds(c, r)
                or blocks[r][c] != -1
                or self.grid[r, c] == GridState.EMPTY
            ):
                return
            if self.grid[r, c] == GridState.ROAD:
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
                    self.grid[r, c] == GridState.EMPTY
                    or self.grid[r, c] == GridState.ROAD
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
            and self.grid[r, c] not in [GridState.HOUSE, GridState.ROAD]
        }

        # collect available houses
        available_houses = {
            (r, c)
            for c in range(self.cols)
            for r in range(self.rows)
            if blocks[r][c] != -1 and self.grid[r, c] == GridState.HOUSE
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
                rand_place_type = self.grid[r, c]

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
                for p in self.people:
                    p.day_changed(self.day)
        # move the person if they are in moving state
        moving_persons = [
            (i, person)
            for i, person in enumerate(self.people)
            if person.state == PersonState.Moving
        ]

        for i, person in moving_persons:
            if i in self.path_cache:
                path = self.path_cache[i]
            else:
                path = self.calculate_path(person)
                self.path_cache[i] = path

            path_completed = path is None or len(path) == 0
            if path_completed:
                # remove the path from the cache 
                self.path_cache.pop(i)
                # change the persons state to staying 
                person.state = PersonState.Staying
                # go to the current location 
                person.current_idx += 1
                continue

            dest = path.pop(0)
            person.loc = dest

    def get_closest_road(self, loc: tuple[int, int]) -> tuple[int, int] | None:
        # find the nearest road which should be connected to the current block
        def dfs(r, c, self_state: GridState, visited: set):
            if not self.check_in_bounds(c, r) or (r, c) in visited:
                return None
            if self.grid[r, c] == GridState.ROAD:
                return r, c
            if self.grid[r, c] != self_state:
                return None
            visited.add((r, c))
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                point = dfs(r + dy, c + dx, self_state, visited)
                if point is not None:
                    return point

        visited = set()
        r, c = loc
        return dfs(r, c, self.grid[r, c], visited)

    def calculate_path(self, person: Person):
        r, c = person.loc
        # check if the person isn't on a road
        road_loc = None
        if self.grid[r, c] == GridState.ROAD:
            road_loc = r, c
        road_loc = road_loc or self.get_closest_road(person.loc)
        if road_loc is None:
            raise Exception(f"No road found from location {person.loc}")

        src = road_loc
        dest = person.get_dest(self.day)
        return self.get_a_star_path(src, dest)

    def get_a_star_path(self, src, dest):
        r, c = dest
        dest_type = self.grid[r, c]

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
                if self.check_in_bounds(c + dx, r + dy) and self.grid[r + dy, c + dx] in [GridState.ROAD, dest_type]:
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

    def check_in_bounds(self, c: int, r: int):
        return self.grid.check_in_bounds(c, r)
