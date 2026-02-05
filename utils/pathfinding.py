import heapq

class Pathfind:
    def __init__(self, grid, agent_w=1, agent_h=1):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.agent_w = agent_w
        self.agent_h = agent_h

        self.cspace = self.build_cspace()

    
    def build_prefix(self):

        # Create a grid to 0
        ps = [[0]*(self.cols+1) for _ in range(self.rows+1)]
    #each row
        for r in range(self.rows):
            #each column
            for c in range(self.cols):
                # Invert grid value so 1 goes to 0 and vis versa
                inverted_val = 0 if self.grid[r][c] == 1 else 1
                # Compute prefix sum for cell (r+1, c+1)
                ps[r+1][c+1] = (
                    inverted_val
                    + ps[r][c+1]  # sum above
                    + ps[r+1][c]  
                    # sum to the left
                    - ps[r][c]    
                )
        return ps

    def rect_sum(self, ps, r, c, h, w):
        # Returns the sum of values in rectangle from (r, c) to (r+h-1, c+w-1)
        return ps[r+h][c+w] - ps[r][c+w] - ps[r+h][c] + ps[r][c]

    def build_cspace(self):
        ps = self.build_prefix()

        #initialise cspace grid 1= block 0 =walkable
        cspace = [[1]*self.cols for _ in range(self.rows)]
        # Loop over all possible top-left positions for the agent
        for r in range(self.rows - self.agent_h + 1):
            for c in range(self.cols - self.agent_w + 1):
                # If the agent's footprint is fully walkable (sum == 0)
                if self.rect_sum(ps, r, c, self.agent_h, self.agent_w) == 0:
                    cspace[r][c] = 0  # Mark as walkable for the object
        # Return the configuration space grid
        return cspace

   


   
    def find_path(self, start, goal):
        start = (max(0, min(start[0], self.rows-1)), max(0, min(start[1], self.cols-1)))
        goal = (max(0, min(goal[0], self.rows-1)), max(0, min(goal[1], self.cols-1)))
        
        
        start_was_blocked = self.cspace[start[0]][start[1]] == 1
        goal_was_blocked = self.cspace[goal[0]][goal[1]] == 1
        
        if start_was_blocked:
            self.cspace[start[0]][start[1]] = 0
        if goal_was_blocked:
            self.cspace[goal[0]][goal[1]] = 0
        
        try:
            if start == goal:
                return [start]
            
            INF = 10**9
            g = [[INF]*self.cols for _ in range(self.rows)]
            came = [[None]*self.cols for _ in range(self.rows)]

            def heuristic(a, b):
                return abs(a[0]-b[0]) + abs(a[1]-b[1])

            pq = []
            g[start[0]][start[1]] = 0
            heapq.heappush(pq, (0, start))

            while pq:
                f, (r, c) = heapq.heappop(pq)

                if (r, c) == goal:
                    break

                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        if self.cspace[nr][nc] == 1:
                            continue
                        
                        
                        if dr != 0 and dc != 0:
                            if self.cspace[r+dr][c] == 1 or self.cspace[r][c+dc] == 1:
                                continue

                        move_cost = 1.4 if (dr != 0 and dc != 0) else 1.0
                        ng = g[r][c] + move_cost
                        if ng < g[nr][nc]:
                            g[nr][nc] = ng
                            came[nr][nc] = (r, c)
                            heapq.heappush(pq, (ng + heuristic((nr,nc), goal), (nr,nc)))

            path = []
            cur = goal
            
            if came[cur[0]][cur[1]] is None and cur != start:
                return [] 
            
            while cur:
                path.append(cur)
                cur = came[cur[0]][cur[1]]
            
            path.reverse()
            return path
            
        finally:
            if start_was_blocked:
                self.cspace[start[0]][start[1]] = 1
            if goal_was_blocked:
                self.cspace[goal[0]][goal[1]] = 1

   
    def print_grid(self, grid):
        for row in grid:
            print("".join("#" if x else "." for x in row))
        print()

