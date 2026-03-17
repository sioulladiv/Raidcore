"""A* pathfinder with configuration-space (C-space) obstacle expansion."""
from __future__ import annotations

import heapq


class Pathfind:
    """A* pathfinder that accounts for the agent's physical footprint.

    The collision grid is expanded (C-space) so that a point-sized A* search
    produces paths that a rectangular agent of size *agent_w* x *agent_h* can
    follow without clipping walls.
    """

    def __init__(self, grid: list[list[int]], agent_w: int = 1, agent_h: int = 1) -> None:
        """Build the pathfinder and precompute the configuration space.

        Args:
            grid: 2-D grid where 1 = walkable, 0 = blocked (rows × columns).
            agent_w: Agent width in grid cells (default 1).
            agent_h: Agent height in grid cells (default 1).
        """
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.agent_w = agent_w
        self.agent_h = agent_h

        self.cspace = self.build_cspace()

    
    def build_prefix(self) -> list[list[int]]:
        """Build a 2-D prefix-sum table over the *inverted* grid.

        Inverted means walkable (1) becomes 1 in the prefix sum so that
        :meth:`rect_sum` can test whether a rectangular region is fully
        walkable in O(1).

        Returns:
            ``(rows+1) x (cols+1)`` prefix-sum table.
        """
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

    def rect_sum(self, ps: list[list[int]], r: int, c: int, h: int, w: int) -> int:
        """Return the sum of prefix values in the rectangle [r..r+h, c..c+w].

        Args:
            ps: Prefix-sum table from :meth:`build_prefix`.
            r: Top row index (0-based).
            c: Left column index (0-based).
            h: Rectangle height in cells.
            w: Rectangle width in cells.

        Returns:
            Integer sum; 0 means the region is fully walkable.
        """
        # Returns the sum of values in rectangle from (r, c) to (r+h-1, c+w-1)
        return ps[r+h][c+w] - ps[r][c+w] - ps[r+h][c] + ps[r][c]

    def build_cspace(self) -> list[list[int]]:
        """Expand obstacles by the agent's footprint to produce a C-space grid.

        Returns:
            2-D grid of same shape as the input where 1 = blocked for the
            agent and 0 = safely reachable.
        """
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

   


   
    def find_path(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        """
        Find an A* path from start to goal in the C-space grid.

        Temporarily unblocks the start/goal cells if needed so the search can
        always begin and end, then restores them afterwards.

        Args:
            start: row, col of the starting cell
            goal: row, col of the destination cell

        Returns:
            Ordered list of row, col   tuples from start to goal
            inclusive, or an empty list when no path exists.
        """


        # clamp start and end to grid bouds and check if they are blocked

        start = (max(0, min(start[0], self.rows-1)), max(0, min(start[1], self.cols-1)))
        goal = (max(0, min(goal[0], self.rows-1)), max(0, min(goal[1], self.cols-1)))
        
        
        start_was_blocked = self.cspace[start[0]][start[1]] == 1
        goal_was_blocked = self.cspace[goal[0]][goal[1]] == 1
        
        #if start is blocked then unblock it temporarily so that search can start anyways
        if start_was_blocked:
            self.cspace[start[0]][start[1]]=0

        if goal_was_blocked:

            self.cspace[goal[0]][goal[1]] =0
        
        try:
            if start == goal:
                return [start]
            
            # a billion is close enough to infinityinity
            infinity= 10**9  # a large number representing infinityinity which is good enough for grid sizes up to 100000

            # set g to infinity for all cells expcept start which is 0

            g = [[infinity]*self.cols for _ in range(self.rows)]

            # Stores parent cell for path reconstruction after reaching goal
            came = [[None]  * self.cols for _ in range(self.rows)]

            # Heuristic function for A* (Manhattan distance)
            # named after the way you would navigate around Manhattan with a grid like city layout 
            def heuristic(a, b): return abs(a[0]-b[0])+abs(a[1]-b[1])


            # Priority queue for A* with (f, (row, col)) entries where f=g + h
            pq = []
            g[start[0]][start[1]] = 0
            
            heapq.heappush(pq, (0, start))

            # A* search loop
            while pq:
                
                f, (r, c) = heapq.heappop(pq)

                if (r, c) == goal:
                    break
                # explore all neighbouring cells plus diagonals
                for dr, dc in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                    nr,nc =r+dr,c+dc

                    # check if within boundary and walkable in cspace for a larger agent
                    if 0 <= nr<self.rows and 0<= nc<self.cols:

                        if self.cspace[nr][nc] == 1:
                            continue
                        
                        # If moving diagonally, check for corner cutting
                        if dr != 0 and dc != 0:
                            if self.cspace[r+dr][c] == 1 or self.cspace[r][c+dc] == 1:
                                continue
                        
                        # Diagonal moves cost more (sqrt(2) ~ 1.4) than orthogonal moves (1.0)
                        # 1 times root2
                        move_cost = 1.4 if (dr != 0 and dc != 0) else 1.0
                        # New g cost to neighbour
                        ng = g[r][c] + move_cost
                        # If this path to neighbour is better update the costs and push to priority queue
                        if ng < g[nr][nc]:
                            g[nr][nc] = ng
                            came[nr][nc] = (r, c)
                            # f = g + h
                            heapq.heappush(pq, (ng + heuristic((nr,nc), goal), (nr,nc)))

            path = []
            cur = goal
            
            # if goal is unreachable then came[goal] will be None and return empy path
            if came[cur[0]][cur[1]] is None and cur != start:
                return [] 
            
            # Reconstruct path from goal to start using the came array then reverse it
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

   
    def print_grid(self, grid: list[list[int]]) -> None:
        """Print a grid to stdout using ``'#'`` for blocked and ``'.'`` for walkable.

        Args:
            grid: 2-D integer grid to print.
        """
        for row in grid:
            print("".join("#" if x else "." for x in row))
        print()

