import pygame

# Initialize Pygame
pygame.init()

# Define screen size (viewport)
SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("City Simulation with Roads, Panning, Zooming, and Grid")

# Define colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREY = (128, 128, 128)
ROAD_COLOR = (50, 50, 50)
PERSON_COLOR = (255, 0, 0)

# Grid size
GRID_SIZE = 10

# Set up font
pygame.font.init()
font = pygame.font.SysFont('Arial', 18)

# Define panning and zooming variables
offset_x, offset_y = 0, 0  # Offset for panning
zoom_level = 1.0           # Zoom level
is_panning = False          # Flag to check if panning is in progress
pan_start = (0, 0)          # Starting position of the panning

# Create an offscreen surface to represent the entire map (larger than the display window)
MAP_WIDTH, MAP_HEIGHT = 2000, 2000
map_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))

# Snap to grid function
def snap_to_grid(value):
    return GRID_SIZE * round(value / GRID_SIZE)

# Define building class
class Building:
    def __init__(self, name, x, y, width, height, color):
        self.name = name
        # Snap building position and size to the grid
        self.rect = pygame.Rect(snap_to_grid(x), snap_to_grid(y), snap_to_grid(width), snap_to_grid(height))
        self.color = color
    
    def draw(self, surface):
        # Draw the building rectangle
        pygame.draw.rect(surface, self.color, self.rect)
        # Render and center the text inside the building
        text_surface = font.render(self.name, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

# Define people class
class Person:
    def __init__(self, x, y):
        # Snap person's position to the grid
        self.x = snap_to_grid(x)
        self.y = snap_to_grid(y)
    
    def draw(self, surface):
        pygame.draw.circle(surface, PERSON_COLOR, (self.x, self.y), 10)

# Define fixed locations for buildings with varying sizes, snapped to the grid
buildings = [
    Building('Apartments', 50, 50, 200, 150, (0, 128, 255)),
    Building('Villas', 300, 50, 150, 100, (0, 128, 255)),
    Building('Shopping Mall', 50, 250, 250, 150, (34, 139, 34)),
    Building('School', 50, 450, 200, 100, (255, 165, 0)),
    Building('Religious Shrine', 300, 450, 150, 100, (128, 0, 128)),
    Building('Sports Club', 50, 650, 250, 150, (255, 69, 0)),
    Building('Public Park', 350, 650, 200, 150, (50, 205, 50)),
    Building('Police Station', 50, 850, 150, 100, (255, 0, 0)),
    Building('Fire Station', 300, 850, 150, 100, (178, 34, 34)),
    Building('Transport Station', 50, 1050, 200, 150, (75, 0, 130)),
    Building('Government Offices', 300, 1050, 200, 150, (105, 105, 105))
]

# Function to create roads dynamically based on building positions
def create_roads(buildings):
    roads = []

    # Create vertical roads between Apartments and School, Villas and Religious Shrine
    for building1, building2 in [("Apartments", "School"), ("Villas", "Religious Shrine")]:
        b1 = next(b for b in buildings if b.name == building1)
        b2 = next(b for b in buildings if b.name == building2)
        road_x = snap_to_grid(b1.rect.centerx)  # Vertical road along the center x of b1
        roads.append(((road_x, b1.rect.bottom), (road_x, b2.rect.top)))

    # Create horizontal roads connecting multiple buildings
    for building1, building2 in [("Apartments", "Villas"), ("School", "Religious Shrine"), ("Police Station", "Fire Station"), ("Transport Station", "Government Offices")]:
        b1 = next(b for b in buildings if b.name == building1)
        b2 = next(b for b in buildings if b.name == building2)
        road_y = snap_to_grid(b1.rect.centery)  # Horizontal road along the center y of b1
        roads.append(((b1.rect.right, road_y), (b2.rect.left, road_y)))

    return roads

# Create roads based on building positions
roads = create_roads(buildings)

# Create people
people = [Person(900, 100), Person(900, 200), Person(900, 300)]

# Main loop
running = True
clock = pygame.time.Clock()

# Draw all buildings, roads, and people onto the offscreen map surface once
def draw_map():
    map_surface.fill(WHITE)
    
    # Draw grid lines (optional, to visualize the grid)
    for x in range(0, MAP_WIDTH, GRID_SIZE):
        pygame.draw.line(map_surface, GREY, (x, 0), (x, MAP_HEIGHT))
    for y in range(0, MAP_HEIGHT, GRID_SIZE):
        pygame.draw.line(map_surface, GREY, (0, y), (MAP_WIDTH, y))
    
    # Draw roads
    for road in roads:
        pygame.draw.line(map_surface, ROAD_COLOR, road[0], road[1], 10)
    
    # Draw buildings
    for building in buildings:
        building.draw(map_surface)

    # Draw people
    for person in people:
        person.draw(map_surface)

draw_map()  # Draw the initial map

while running:
    screen.fill(WHITE)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click for panning
                is_panning = True
                pan_start = event.pos
            elif event.button == 4:  # Mouse wheel up (zoom in)
                zoom_level = min(zoom_level + 0.1, 3)  # Limit zoom level
            elif event.button == 5:  # Mouse wheel down (zoom out)
                zoom_level = max(zoom_level - 0.1, 0.5)  # Limit zoom level
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:  # Stop panning
                is_panning = False
        elif event.type == pygame.MOUSEMOTION:
            if is_panning:
                # Update offset for panning
                dx, dy = event.rel
                offset_x += dx
                offset_y += dy

    # Create a scaled version of the map surface for zooming
    zoomed_surface = pygame.transform.scale(map_surface, (int(MAP_WIDTH * zoom_level), int(MAP_HEIGHT * zoom_level)))

    # Define the portion of the zoomed surface (map) to display on the screen (viewport)
    viewport = pygame.Rect(-offset_x, -offset_y, SCREEN_WIDTH, SCREEN_HEIGHT)

    # Blit the zoomed surface onto the screen using the viewport as a reference
    screen.blit(zoomed_surface, (0, 0), viewport)

    # Update the screen
    pygame.display.flip()
    
    # Limit the frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
