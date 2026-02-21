from __future__ import annotations

from cell import Cell

UNKNOWN, FREE, BLOCKED = range(3)


class GridWorld:
    """
    Submission-local helper that mirrors your work-area GridWorld.

    - `true_blocked`: ground truth (bool)
    - `known`: agent knowledge (UNKNOWN/FREE/BLOCKED)
    """

    def __init__(
        self,
        height: int,
        width: int,
        start: tuple[int, int],
        goal: tuple[int, int],
        actual_maze: list[list[int]] | None = None,
    ):
        self.H = height
        self.W = width
        self.start = start
        self.goal = goal

        sr, sc = self.start
        gr, gc = self.goal
        if not (0 <= sr < self.H and 0 <= sc < self.W):
            raise ValueError("Start out of bounds")
        if not (0 <= gr < self.H and 0 <= gc < self.W):
            raise ValueError("Goal out of bounds")

        self.cells: list[list[Cell]] = [[Cell((r, c)) for c in range(self.W)] for r in range(self.H)]

        if actual_maze is None:
            self.true_blocked = [[False for _ in range(self.W)] for _ in range(self.H)]
        else:
            self.true_blocked = [[(actual_maze[r][c] == 1) for c in range(self.W)] for r in range(self.H)]

        self.known = [[UNKNOWN for _ in range(self.W)] for _ in range(self.H)]
        self.known[sr][sc] = FREE

        # safety
        self.true_blocked[sr][sc] = False
        self.true_blocked[gr][gc] = False

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.H and 0 <= c < self.W

    def is_true_blocked(self, r: int, c: int) -> bool:
        return self.true_blocked[r][c]

    def is_known_blocked(self, r: int, c: int) -> bool:
        return self.known[r][c] == BLOCKED

    def reset_known(self) -> None:
        self.known = [[UNKNOWN for _ in range(self.W)] for _ in range(self.H)]
        sr, sc = self.start
        self.known[sr][sc] = FREE

    def cell(self, r: int, c: int) -> Cell:
        return self.cells[r][c]

    def neighbors(self, cell: Cell) -> list[Cell]:
        r, c = cell.coord
        out: list[Cell] = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not self.in_bounds(nr, nc):
                continue
            if self.is_known_blocked(nr, nc):
                continue
            out.append(self.cells[nr][nc])
        return out

    def observe_from(self, cell: Cell) -> None:
        r, c = cell.coord
        self.known[r][c] = FREE
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if not self.in_bounds(nr, nc):
                continue
            if self.is_true_blocked(nr, nc):
                self.known[nr][nc] = BLOCKED
            else:
                self.known[nr][nc] = FREE

