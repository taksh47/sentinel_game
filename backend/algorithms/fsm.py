"""
ALGORITHM 3: Finite State Machine (classic game-AI decision making)

The Guard cycles through four explicit states:
  PATROL  -> walks a fixed loop of waypoints
  CHASE   -> player is in line-of-sight, run the A* path to them
  SEARCH  -> lost sight of the player, investigate their last known position
  RETURN  -> gave up searching, walk back to the patrol route

Transitions are driven by a simple line-of-sight (Bresenham) check, which is
itself a small, self-contained algorithm worth calling out on its own.
"""
from . import astar

PATROL, CHASE, SEARCH, RETURN = "PATROL", "CHASE", "SEARCH", "RETURN"


def _has_line_of_sight(a, b, grid, max_range):
    """Bresenham line trace: true if no wall tile sits between a and b, within range."""
    if _heuristic(a, b) > max_range:
        return False
    x0, y0 = a
    x1, y1 = b
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while (x, y) != (x1, y1):
        if grid[y][x] == 1:
            return False
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return True


def _heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


class Guard:
    def __init__(self, start_pos, patrol_route, vision_range=6):
        self.pos = start_pos
        self.state = PATROL
        self.patrol_route = patrol_route or [start_pos]
        self.patrol_index = 0
        self.vision_range = vision_range
        self.last_known_player_pos = None
        self.search_timer = 0

    def step(self, player_pos, grid):
        """Advance one tick: update state, then move one tile. Returns a log string."""
        can_see_player = _has_line_of_sight(self.pos, player_pos, grid, self.vision_range)
        log = None

        if can_see_player:
            if self.state != CHASE:
                log = "GUARD: contact! switching PATROL/SEARCH -> CHASE"
            self.state = CHASE
            self.last_known_player_pos = player_pos
            self.search_timer = 6
        elif self.state == CHASE:
            self.state = SEARCH
            log = "GUARD: lost visual -> SEARCH last known position"
        elif self.state == SEARCH:
            self.search_timer -= 1
            if self.search_timer <= 0:
                self.state = RETURN
                log = "GUARD: search timed out -> RETURN to patrol"

        target = None
        if self.state == CHASE:
            target = self.last_known_player_pos
        elif self.state == SEARCH:
            target = self.last_known_player_pos
        elif self.state == RETURN:
            target = self.patrol_route[self.patrol_index]
            if self.pos == target:
                self.state = PATROL
                log = "GUARD: back on route -> PATROL"
        elif self.state == PATROL:
            target = self.patrol_route[self.patrol_index]
            if self.pos == target:
                self.patrol_index = (self.patrol_index + 1) % len(self.patrol_route)
                target = self.patrol_route[self.patrol_index]

        if target and target != self.pos:
            path = astar.find_path(self.pos, target, grid)
            if path:
                self.pos = path[0]

        return self.state, log
