"""
ALGORITHM 1: Cellular Automata (procedural content generation)

Classic "4-5 rule" cave generation: seed random noise, then repeatedly apply
Conway-style smoothing rules so walls clump into organic cave shapes instead
of random static. Finishes with a flood-fill pass to guarantee the map is
fully connected (games can't ship a maze the player literally cannot cross).
"""
import random
from collections import deque

WALL = 1
FLOOR = 0


def _seed_grid(width, height, fill_prob, rng):
    grid = [[WALL if rng.random() < fill_prob else FLOOR for _ in range(width)] for _ in range(height)]
    # force a clean border so the player can never walk off the map
    for x in range(width):
        grid[0][x] = WALL
        grid[height - 1][x] = WALL
    for y in range(height):
        grid[y][0] = WALL
        grid[y][width - 1] = WALL
    return grid


def _count_wall_neighbors(grid, x, y, width, height):
    count = 0
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                count += 1  # treat out-of-bounds as wall, keeps the border solid
            elif grid[ny][nx] == WALL:
                count += 1
    return count


def _smooth(grid, width, height, birth_limit, death_limit):
    new_grid = [row[:] for row in grid]
    for y in range(height):
        for x in range(width):
            walls = _count_wall_neighbors(grid, x, y, width, height)
            if grid[y][x] == WALL:
                new_grid[y][x] = WALL if walls >= death_limit else FLOOR
            else:
                new_grid[y][x] = WALL if walls > birth_limit else FLOOR
    return new_grid


def _largest_connected_region(grid, width, height):
    """BFS flood fill to find the biggest open region, and cells within it."""
    seen = [[False] * width for _ in range(height)]
    best_region = []
    for y in range(height):
        for x in range(width):
            if grid[y][x] == FLOOR and not seen[y][x]:
                region = []
                q = deque([(x, y)])
                seen[y][x] = True
                while q:
                    cx, cy = q.popleft()
                    region.append((cx, cy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < width and 0 <= ny < height and not seen[ny][nx] and grid[ny][nx] == FLOOR:
                            seen[ny][nx] = True
                            q.append((nx, ny))
                if len(region) > len(best_region):
                    best_region = region
    return best_region


def generate_cave(width=21, height=15, fill_prob=0.42, steps=4, seed=None):
    """
    Returns (grid, floor_cells) where grid[y][x] is 0 (floor) or 1 (wall),
    and floor_cells is the list of walkable (x, y) tiles in the single
    largest connected region -- so any two floor cells are guaranteed
    reachable from one another.
    """
    rng = random.Random(seed)
    grid = _seed_grid(width, height, fill_prob, rng)
    for _ in range(steps):
        grid = _smooth(grid, width, height, birth_limit=4, death_limit=3)

    region = _largest_connected_region(grid, width, height)
    region_set = set(region)
    # anything not in the main region gets walled off so it can't be reached
    for y in range(height):
        for x in range(width):
            if (x, y) not in region_set:
                grid[y][x] = WALL

    return grid, region
