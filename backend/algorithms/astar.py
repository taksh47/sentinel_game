"""
ALGORITHM 2: A* Pathfinding

Used by the Guard AI to plot the shortest walkable route to the player.
Standard implementation: g = cost so far, h = Manhattan distance heuristic,
f = g + h, always expand the lowest-f node first via a min-heap.
"""
import heapq


def _heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _neighbors(pos, grid, width, height):
    x, y = pos
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height and grid[ny][nx] == 0:
            yield (nx, ny)


def find_path(start, goal, grid):
    """Returns list of (x, y) from start to goal (exclusive of start), or [] if unreachable."""
    height = len(grid)
    width = len(grid[0]) if height else 0

    if start == goal:
        return []

    open_heap = [(0, start)]
    came_from = {}
    g_score = {start: 0}
    visited = set()

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            path = []
            node = current
            while node != start:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path

        for neighbor in _neighbors(current, grid, width, height):
            tentative_g = g_score[current] + 1
            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f_score = tentative_g + _heuristic(neighbor, goal)
                heapq.heappush(open_heap, (f_score, neighbor))

    return []  # no path found
