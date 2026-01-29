import heapq

# ---------------------------
# OBSTACLE INFLATION
# ---------------------------

def inflate_obstacles(grid, radius):
    rows = len(grid)
    cols = len(grid[0])
    new_grid = [row[:] for row in grid]

    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                for dr in range(-radius, radius + 1):
                    for dc in range(-radius, radius + 1):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < rows and 0 <= nc < cols:
                            new_grid[nr][nc] = 1
    return new_grid


# ---------------------------
# FAST GRID A*
# ---------------------------

def fast_astar(grid, start, goal):
    rows = len(grid)
    cols = len(grid[0])
    INF = 10**9

    # Cost grid
    g = [[INF] * cols for _ in range(rows)]
    came = [[None] * cols for _ in range(rows)]

    g[start[0]][start[1]] = 0
    pq = [(0, start)]

    while pq:
        f, (r, c) = heapq.heappop(pq)

        if (r, c) == goal:
            break

        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0:
                ng = g[r][c] + 1
                if ng < g[nr][nc]:
                    g[nr][nc] = ng
                    came[nr][nc] = (r, c)
                    h = abs(nr - goal[0]) + abs(nc - goal[1])
                    heapq.heappush(pq, (ng + h, (nr, nc)))

    # Rebuild path
    path = []
    cur = goal
    while cur:
        path.append(cur)
        cur = came[cur[0]][cur[1]]

    return path[::-1] if path[-1] == start else []


# ---------------------------
# DEBUG GRID PRINT
# ---------------------------

def print_grid(grid):
    for row in grid:
        print("".join("#" if x else "." for x in row))
    print()

grid = [
    [0,1,0,0,0],
    [0,1,0,1,0],
    [0,0,0,1,0],
    [0,0,0,0,0],
    [0,0,0,0,0],
]

start = (1, 0)
goal  = (4, 4)

# Agent size in tiles
agent_width  = 2
agent_height = 2

# Inflate obstacles for fat agent
radius = max(agent_width, agent_height) // 2
inflated_grid = inflate_obstacles(grid, radius)

# Print grids
print("=== ORIGINAL GRID ===")
print_grid(grid)

print("=== INFLATED GRID (for fat agent) ===")
print_grid(inflated_grid)

# Run A*
path = fast_astar(inflated_grid, start, goal)

print("Path:", path)