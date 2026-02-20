"""
gen_test_json.py — Generate N random 101x101 mazes and save as mazes.json. Uses same algorithm as maze_generator.py.

Usage:
    python gen_test_json.py [--num_mazes N] [--seed S] [--output FILE]
"""
import json
import random
import argparse
import random
from constants import ROWS
from tqdm import tqdm
import argparse

# set random seed for reproducibility
random.seed(42)

def create_maze() -> list:
    # TODO: Implement this function to generate and return a random maze as a 2D list of 0s and 1s.
    # DFS / corridor-like generation as described in Assignment1.pdf:
    # - Visit cells depth-first using a stack, random neighbor tie-breaking.
    # - When visiting an unvisited neighbor: block it with 30% probability,
    #   otherwise mark it free and push to stack.
    # - When dead-end, backtrack. If stack empties but unvisited remain, restart.

    UNVISITED, VISITED = 0, 1
    visited = [[UNVISITED for _ in range(ROWS)] for _ in range(ROWS)]
    maze = [[0 for _ in range(ROWS)] for _ in range(ROWS)]  # 0 free, 1 blocked

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < ROWS and 0 <= c < ROWS

    def unvisited_neighbors(r: int, c: int) -> list[tuple[int, int]]:
        nbrs: list[tuple[int, int]] = []
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and visited[nr][nc] == UNVISITED:
                nbrs.append((nr, nc))
        return nbrs

    def pick_unvisited() -> tuple[int, int] | None:
        cells: list[tuple[int, int]] = [
            (r, c) for r in range(ROWS) for c in range(ROWS) if visited[r][c] == UNVISITED
        ]
        if not cells:
            return None
        return random.choice(cells)

    stack: list[tuple[int, int]] = []
    start = pick_unvisited()
    while start is not None:
        r, c = start
        visited[r][c] = VISITED
        maze[r][c] = 0
        stack.append((r, c))

        while stack:
            cr, cc = stack[-1]
            nbrs = unvisited_neighbors(cr, cc)
            if not nbrs:
                stack.pop()
                continue

            nr, nc = random.choice(nbrs)
            visited[nr][nc] = VISITED
            if random.random() < 0.30:
                maze[nr][nc] = 1
            else:
                maze[nr][nc] = 0
                stack.append((nr, nc))

        start = pick_unvisited()

    # ensure start/goal cells are unblocked
    maze[0][0] = 0
    maze[ROWS - 1][ROWS - 1] = 0
    return maze

def main():
    parser = argparse.ArgumentParser(description="Generate random mazes as JSON")
    parser.add_argument("--num_mazes", type=int, default=50,
                        help="Number of mazes to generate")
    parser.add_argument("--seed", type=int, default=42,
                        help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="mazes.json",
                        help="Output JSON file path")
    args = parser.parse_args()

    random.seed(args.seed)
    
    mazes = []
    for _ in tqdm(range(args.num_mazes), desc="Generating mazes"):  
        mazes.append(create_maze())

    with open(args.output, "w") as fp:
        json.dump(mazes, fp)
    print(f"Generated {args.num_mazes} mazes (seed={args.seed}) -> {args.output}")

if __name__ == "__main__":
    main()
