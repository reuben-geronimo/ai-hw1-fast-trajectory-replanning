from __future__ import annotations

from cell import Cell
from grid import GridWorld
from custom_pq import CustomPQ_maxG, CustomPQ_minG

# compute the manhattan distance between two cells
def manhattan(cell: Cell, goal: Cell) -> int:
    return abs(cell.r - goal.r) + abs(cell.c - goal.c)

# compute the adaptive heuristic
def adaptive_heuristic(cell: Cell, goal: Cell) -> float:
    if cell.h is not None:
        return float(cell.h)
    return float(abs(cell.r - goal.r) + abs(cell.c - goal.c))

# compute the path using A* search (single pass)
def compute_path(
    grid: GridWorld,
    start: Cell,
    end: Cell,
    heuristic_fn,
    search_id: int,
    tie_breaking: str = "max_g",
) -> tuple[list[Cell] | None, list[Cell]]:
    if tie_breaking not in ("max_g", "min_g"):
        raise ValueError("tie_breaking must be 'max_g' or 'min_g'")

    start.reset_for_search(search_id)
    end.reset_for_search(search_id)
    start.g = 0.0
    start.parent = None

    # Open list priority queue (from-scratch heap implementation).
    if tie_breaking == "max_g":
        pq = CustomPQ_maxG[Cell]()
    else:
        pq = CustomPQ_minG[Cell]()

    def push(cell: Cell) -> None:
        g = float(cell.g)
        f = g + float(heuristic_fn(cell, end))
        pq.push(f=f, g=g, item=cell)

    push(start)

    closed: set[tuple[int, int]] = set()
    expanded: list[Cell] = []

    while not pq.empty():
        _, g_popped, cur = pq.pop()
        if cur.coord in closed:
            continue
        if cur.search_id != search_id:
            continue
        # Lazy-duplicate handling: skip stale queue entries.
        if float(cur.g) != float(g_popped):
            continue

        closed.add(cur.coord)
        expanded.append(cur)

        if cur.coord == end.coord:
            path: list[Cell] = []
            node: Cell | None = cur
            while node is not None:
                path.append(node)
                node = node.parent
            path.reverse()
            return path, expanded

        for nbr in grid.neighbors(cur):
            nbr.reset_for_search(search_id)
            tentative = cur.g + 1.0
            if tentative < nbr.g:
                nbr.g = tentative
                nbr.parent = cur
                push(nbr)

    return None, expanded

