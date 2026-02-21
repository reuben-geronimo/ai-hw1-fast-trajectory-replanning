"""
q5.py — Adaptive A* with tie-breaking variants + Pygame visualization

Renders TWO views side-by-side:
- LEFT  : full (ground-truth) maze used for the run
- RIGHT : agent knowledge + search visualization

Controls:
- R : generate a new random maze and run again (max-g by default)
- 1 : run MAX-G Adaptive A* on the current maze
- 2 : run MAX-G Forward A* on the current maze
- ESC or close window : quit

Maze file format helper:
- readFile(fname) reads 0/1 space-separated tokens, 1=blocked, 0=free, one row per line.

Legend (colors):
GREY   = expanded / frontier / unknown (unseen)
PATH   = executed path
YELLOW = start + agent position
BLUE   = goal
WHITE  = known free
BLACK  = known blocked
"""

from __future__ import annotations

import heapq
import argparse
import json
import time
from typing import Callable, Dict, List, Optional, Tuple
from tqdm import tqdm
try:
    import pygame  # type: ignore
except Exception:  # pragma: no cover
    pygame = None  # type: ignore
from q2 import repeated_forward_astar
from constants import ROWS, START_NODE, END_NODE, BLACK, WHITE, GREY, YELLOW, BLUE, PATH, NODE_LENGTH, GRID_LENGTH, WINDOW_W, WINDOW_H, GAP
from custom_pq import CustomPQ_maxG
from grid import GridWorld, UNKNOWN, FREE, BLOCKED
from astar_impl import compute_path, adaptive_heuristic, manhattan


# ---------------- FILE LOADER ----------------
def readMazes(fname: str) -> List[List[List[int]]]:
    """
    Reads a JSON file containing a list of mazes.
    Each maze is a list of ROWS lists, each with ROWS int values (0=free, 1=blocked).
    Returns a list of maze[r][c] grids.
    """
    with open(fname, "r", encoding="utf-8") as fp:
        data = json.load(fp)
    mazes: List[List[List[int]]] = []
    for idx, grid in enumerate(data):
        if len(grid) != ROWS or any(len(row) != ROWS for row in grid):
            raise ValueError(f"Maze {idx}: expected {ROWS}x{ROWS}, got {len(grid)}x{len(grid[0]) if grid else 0}")
        maze = [[int(v) for v in row] for row in grid]
        maze[START_NODE[0]][START_NODE[1]] = 0
        maze[END_NODE[0]][END_NODE[1]] = 0
        mazes.append(maze)
    return mazes

def adaptive_astar(
    actual_maze: List[List[int]],
    start: Tuple[int, int] = START_NODE,
    goal: Tuple[int, int] = END_NODE,
    visualize_callbacks: Optional[Dict[str, Callable[[Tuple[int, int]], None]]] = None,
) -> Tuple[bool, List[Tuple[int, int]], int, int]:
    
    # TODO: Implement Adaptive A* with max_g tie-braking strategy.
    # Use heapq for standard priority queue implementation and name your max_g heap class as `CustomPQ_maxG` and use it. 
    grid = GridWorld(ROWS, ROWS, start, goal, actual_maze=actual_maze)

    cur = grid.cell(start[0], start[1])
    goal_cell = grid.cell(goal[0], goal[1])
    executed: List[Tuple[int, int]] = [cur.coord]
    expanded_total = 0
    replans = 0
    search_id = 0

    grid.observe_from(cur)

    while cur.coord != goal_cell.coord:
        search_id += 1
        replans += 1

        path, expanded = compute_path(grid, cur, goal_cell, adaptive_heuristic, search_id, tie_breaking="max_g")
        expanded_total += len(expanded)
        if path is None:
            return False, executed, expanded_total, replans

        # Adaptive A* heuristic update: for expanded states, h(s) = g(goal) - g(s)
        g_goal = goal_cell.g
        if g_goal != float("inf"):
            for s in expanded:
                s.h = g_goal - s.g

        for step in path[1:]:
            grid.observe_from(cur)
            if grid.is_true_blocked(step.r, step.c):
                grid.known[step.r][step.c] = 2  # BLOCKED
                break

            cur = step
            executed.append(cur.coord)
            grid.observe_from(cur)

            if visualize_callbacks and "on_move" in visualize_callbacks:
                visualize_callbacks["on_move"](cur.coord)

            if cur.coord == goal_cell.coord:
                return True, executed, expanded_total, replans

    return True, executed, expanded_total, replans

def show_astar_search(win: pygame.Surface, actual_maze: List[List[int]], algo: str, fps: int = 240, step_delay_ms: int = 0, save_path: Optional[str] = None) -> None:
    if save_path is None:
        save_path = f"vis_{algo}.png"

    vis_grid = GridWorld(ROWS, ROWS, START_NODE, END_NODE, actual_maze=actual_maze)
    agent_pos = START_NODE
    executed_path: List[Tuple[int, int]] = [START_NODE]
    vis_grid.observe_from(vis_grid.cell(START_NODE[0], START_NODE[1]))

    def draw_scene() -> None:
        win.fill(GREY)

        # Left pane: full, ground-truth maze.
        for r in range(ROWS):
            for c in range(ROWS):
                color = BLACK if actual_maze[r][c] == 1 else WHITE
                rect = pygame.Rect(c * NODE_LENGTH, r * NODE_LENGTH, NODE_LENGTH, NODE_LENGTH)
                pygame.draw.rect(win, color, rect)

        # Right pane: agent's current knowledge.
        right_x = GRID_LENGTH + GAP
        for r in range(ROWS):
            for c in range(ROWS):
                state = vis_grid.known[r][c]
                if state == BLOCKED:
                    color = BLACK
                elif state == FREE:
                    color = WHITE
                elif state == UNKNOWN:
                    color = GREY
                else:
                    color = GREY
                rect = pygame.Rect(right_x + c * NODE_LENGTH, r * NODE_LENGTH, NODE_LENGTH, NODE_LENGTH)
                pygame.draw.rect(win, color, rect)

        # Overlay executed path in both panes for easy comparison.
        for pr, pc in executed_path:
            left_rect = pygame.Rect(pc * NODE_LENGTH, pr * NODE_LENGTH, NODE_LENGTH, NODE_LENGTH)
            right_rect = pygame.Rect(right_x + pc * NODE_LENGTH, pr * NODE_LENGTH, NODE_LENGTH, NODE_LENGTH)
            pygame.draw.rect(win, PATH, left_rect)
            pygame.draw.rect(win, PATH, right_rect)

        # Start and goal markers.
        for pane_x in (0, right_x):
            sr, sc = START_NODE
            gr, gc = END_NODE
            start_rect = pygame.Rect(pane_x + sc * NODE_LENGTH, sr * NODE_LENGTH, NODE_LENGTH, NODE_LENGTH)
            goal_rect = pygame.Rect(pane_x + gc * NODE_LENGTH, gr * NODE_LENGTH, NODE_LENGTH, NODE_LENGTH)
            pygame.draw.rect(win, YELLOW, start_rect)
            pygame.draw.rect(win, BLUE, goal_rect)

        # Current agent position on the right pane.
        ar, ac = agent_pos
        agent_rect = pygame.Rect(right_x + ac * NODE_LENGTH, ar * NODE_LENGTH, NODE_LENGTH, NODE_LENGTH)
        pygame.draw.rect(win, YELLOW, agent_rect)

        pygame.display.flip()

    draw_scene()

    def on_move(coord: Tuple[int, int]) -> None:
        nonlocal agent_pos
        agent_pos = coord
        executed_path.append(coord)
        vis_grid.observe_from(vis_grid.cell(coord[0], coord[1]))
        draw_scene()
        pygame.event.pump()
        if step_delay_ms > 0:
            pygame.time.wait(step_delay_ms)
        elif fps > 0:
            pygame.time.delay(max(1, int(1000 / fps)))

    if algo == "fwd":
        found, executed, expanded, replans = repeated_forward_astar(
            actual_maze=actual_maze,
            start=START_NODE,
            goal=END_NODE,
            tie_breaking="max_g",
            visualize_callbacks={"on_move": on_move},
        )
    else:
        found, executed, expanded, replans = adaptive_astar(
            actual_maze=actual_maze,
            start=START_NODE,
            goal=END_NODE,
            visualize_callbacks={"on_move": on_move},
        )
    if len(executed) > len(executed_path):
        executed_path[:] = executed
    draw_scene()
    print(f"[{algo}] found={found}  executed_steps={len(executed)-1}  expanded={expanded}  replans={replans}")

    pygame.image.save(win, save_path)
    print(f"Saved the visualization -> {save_path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Q5: Adaptive A*")
    parser.add_argument("--maze_file", type=str, required=True,
                        help="Path to input JSON file containing a list of mazes")
    parser.add_argument("--output", type=str, default="results_q5.json",
                        help="Path to output JSON results file")
    parser.add_argument("--show_vis", action="store_true",
                        help="[Bonus] If set, show Pygame visualization for the selected maze")
    parser.add_argument("--maze_vis_id", type=int, default=0,
                        help="[Bonus] maze_id (index) 0 ... 49 among 50 grid worlds")
    parser.add_argument("--save_vis_path", type=str, default="q5-vis-max-g.png",
                        help="[Bonus] If set, save visualization to this PNG file")
    args = parser.parse_args()

    mazes = readMazes(args.maze_file)
    results: List[Dict] = []

    for maze_id in tqdm(range(len(mazes)), desc="Processing mazes"):
        entry: Dict = {"maze_id": maze_id}

        t0 = time.perf_counter()
        found, executed, expanded, replans = adaptive_astar(
            actual_maze=mazes[maze_id],
            start=START_NODE,
            goal=END_NODE,
        )
        t1 = time.perf_counter()

        entry["adaptive"] = {
            "found": found,
            "path_length": len(executed) - 1 if found else -1,
            "expanded": expanded,
            "replans": replans,
            "runtime_ms": (t1 - t0) * 1000,
        }

        t0 = time.perf_counter()
        found, executed, expanded, replans = repeated_forward_astar(
            actual_maze=mazes[maze_id],
            start=START_NODE,
            goal=END_NODE,
            tie_breaking="max_g",
        )
        t1 = time.perf_counter()

        entry["fwd"] = {
            "found": found,
            "path_length": len(executed) - 1 if found else -1,
            "expanded": expanded,
            "replans": replans,
            "runtime_ms": (t1 - t0) * 1000,
        }

        results.append(entry)

    if args.show_vis:
        if pygame is None:
            raise RuntimeError("pygame is not installed; run without --show_vis")
        # In case, PyGame is used for visualization, this code initializes a window and runs the visualization for the selected maze and algorithm.
        # Feel free to modify this code if you use a different visualization library or approach.
        pygame.init()
        win = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption("Adaptive A* Visualization")
        clock = pygame.time.Clock()
        selected_maze = mazes[args.maze_vis_id]
        current_algo = "adaptive"
        show_astar_search(win, selected_maze, algo=current_algo, fps=240, step_delay_ms=0, save_path=args.save_vis_path)
        running = True
        while running:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        current_algo = "adaptive"
                        show_astar_search(win, selected_maze, algo=current_algo, fps=240, step_delay_ms=0, save_path=args.save_vis_path)
                    elif event.key == pygame.K_1:
                        current_algo = "adaptive"
                        show_astar_search(win, selected_maze, algo=current_algo, fps=240, step_delay_ms=0, save_path=args.save_vis_path)
                    elif event.key == pygame.K_2:
                        current_algo = "fwd"
                        show_astar_search(win, selected_maze, algo=current_algo, fps=240, step_delay_ms=0, save_path=args.save_vis_path)
            pygame.display.flip()

        pygame.quit()

    with open(args.output, "w") as fp:
        json.dump(results, fp, indent=2)
    print(f"Results for {len(results)} mazes written to {args.output}")


if __name__ == "__main__":
    main()