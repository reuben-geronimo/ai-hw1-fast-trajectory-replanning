# importing cell class
from cell import Cell

UNKNOWN, FREE, BLOCKED = range(3)
# print(UNKNOWN, FREE, BLOCKED)

def generate_maze(height: int, width: int) -> list[list[bool]]:
    """
    Placeholder generator:
    - False = free
    - True  = blocked
    Replace later with maze generator.
    """
    return [[False for _ in range(width)] for _ in range(height)]

class GridWorld:
    def __init__(self, height: int, width: int, start: tuple[int, int], goal: tuple[int, int]):
        self.H = height
        self.W = width
        self.start = start
        self.goal = goal

        # bounds check for start and goal
        sr, sc = self.start
        gr, gc = self.goal
        if not (0 <= sr < self.H and 0 <= sc < self.W):
            raise ValueError("Start out of bounds")
        if not (0 <= gr < self.H and 0 <= gc < self.W):
            raise ValueError("Goal out of bounds")

        # grid of cells
        self.cells: list[list[Cell]] = [
            [Cell((r, c)) for c in range(self.W)]
            for r in range(self.H)
        ]

        # true map : true = blocked, false = free
        self.true_blocked: list[list[bool]] = generate_maze(self.H, self.W)

        # known map, initially unknown, agent's knowledge of the grid : UNKNOWN = 0, FREE = 1, BLOCKED = 2
        self.known = [
            [UNKNOWN for _ in range(self.W)]
            for _ in range(self.H)
        ]

        # initialize start location to FREE
        self.known[sr][sc] = FREE

        # safety : makes sure the goal and the start are not blocked in true map
        self.true_blocked[sr][sc] = False
        self.true_blocked[gr][gc] = False

    # checks if the coordinates are within the bounds of the grid
    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.H and 0 <= c < self.W
    
    # checks if the cell at the given coordinates is blocked in the true map
    def is_true_blocked(self, r: int, c: int) -> bool:
        return self.true_blocked[r][c]
    
    # checks if the cell at the given coordinates is blocked in the known map
    def is_known_blocked(self, r: int, c: int) -> bool:
        return self.known[r][c] == BLOCKED

    # resets the known map to all UNKNOWN, except for the start cell which is FREE
    def reset_known(self) -> None:
        self.known = [[UNKNOWN for _ in range(self.W)] for _ in range(self.H)]
        sr, sc = self.start
        self.known[sr][sc] = FREE

    # returns the cell at the given coordinates
    def cell(self, r: int, c: int) -> Cell:
        return self.cells[r][c]

    # reveals the available neighbors of the given cell (for A* search calculations)
    def neighbors(self, cell: Cell) -> list[Cell]:
        r, c = cell.coord
        out = []
        for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
            nr, nc = r + dr, c + dc
            if not self.in_bounds(nr, nc):
                continue
            if self.is_known_blocked(nr, nc):
                continue
            out.append(self.cells[nr][nc])
        return out

    # updates the known map based on the observation from the given cell (used by the agent)
    def observe_from(self, cell: Cell) -> None:
        r, c = cell.coord
        self.known[r][c] = FREE

        for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
            nr, nc = r + dr, c + dc
            if not self.in_bounds(nr, nc):
                continue
            if self.is_true_blocked(nr, nc):
                self.known[nr][nc] = BLOCKED
            else:
                self.known[nr][nc] = FREE