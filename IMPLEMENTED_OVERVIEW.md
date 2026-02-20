## HW1 Fast Trajectory Replanning — Implementation Handoff

This file is meant to help a teammate get caught up quickly on **what’s implemented**, **how it works**, and **how to run it**.

The implementation is organized around the assignment contract in `student-readme.md`:
- **Input**: a JSON file of \(k\) mazes, each a 101×101 grid with `0=free`, `1=blocked`
- **Outputs**: JSON results for `q2.py`, `q3.py`, `q5.py` matching the example schemas
- **Core functions**: `repeated_forward_astar`, `repeated_backward_astar`, `adaptive_astar`
- **Custom heap naming**: `custom_pq.py` with `CustomPQ_minG` / `CustomPQ_maxG`

---

## File map (what each file is for)

- **`student-readme.md`**
  - The “grading contract”: required CLI args + exact output JSON formats.

- **`constants.py`**
  - Grid constants: `ROWS=101`, `START_NODE=(0,0)`, `END_NODE=(100,100)`, and optional visualization colors/sizes.

- **`create_grid_worlds.py`**
  - Generates `k` random mazes (JSON list of 2D int grids).
  - Current generator is DFS/stack based with \(30\%\) blocked probability on newly visited neighbors.

- **`cell.py`**
  - The `Cell` object representing a grid coordinate and storing A* metadata:
    - `g`, `parent`, `search_id`
    - `h` (used for Adaptive A*)

- **`grid.py`**
  - `GridWorld` tracks two maps:
    - `true_blocked`: ground truth from the maze JSON
    - `known`: the agent’s knowledge (UNKNOWN/FREE/BLOCKED)
  - `observe_from(cell)` reveals the blocked/free status of the 4-neighborhood and updates `known`.
  - `neighbors(cell)` returns valid neighbor `Cell`s according to the **known** map (blocked neighbors filtered out).

- **`astar_impl.py`**
  - Single-pass A* implementation: `compute_path(...)`.
  - Heuristics:
    - `manhattan(cell, goal)`
    - `adaptive_heuristic(cell, goal)` (uses `cell.h` if available; otherwise Manhattan)
  - Tie-breaking for equal \(f\) is controlled by `tie_breaking` (`max_g` or `min_g`).

- **`custom_pq.py`**
  - Custom heap wrapper (extra credit path) with required class names:
    - `CustomPQ_minG` (tie-break by smaller g)
    - `CustomPQ_maxG` (tie-break by larger g)
  - Note: the current A* implementation uses `heapq` directly for the open list; this file is provided to satisfy the naming requirement and is ready to be integrated if desired.

- **`q2.py`**
  - Repeated Forward A*: `repeated_forward_astar(actual_maze, ..., tie_breaking)`
  - CLI supports `--tie_braking {max_g|min_g|both}` and outputs the `max_g` and/or `min_g` metrics blocks.

- **`q3.py`**
  - Repeated Backward A*: `repeated_backward_astar(actual_maze, ...)` (max_g variant)
  - Compares backward vs forward (`fwd` calls `q2.repeated_forward_astar(..., tie_breaking="max_g")`)

- **`q5.py`**
  - Adaptive A*: `adaptive_astar(actual_maze, ...)` (max_g variant)
  - Compares adaptive vs forward max_g (`fwd`).

---

## What you (already) had vs what was finished/added

### Your original pieces (core model)
- **`Cell` data structure** with per-search A* metadata and a slot for adaptive `h`.
- **`GridWorld` concept** with:
  - a “true” map (blocked/free)
  - a “known” map (agent’s evolving knowledge)
  - neighborhood observation (`observe_from`) and legal neighbor expansion based on knowledge
- Started the A* “single pass” idea (skeleton in `astar.py` earlier).

### What was finished / added to make it runnable end-to-end
- **A* single-pass implementation** in `astar_impl.py::compute_path(...)` (and mirrored in your work-area `astar.py`).
- **Repeated replanning logic** in `q2/q3/q5` that repeatedly calls single-pass A* over the **agent-known** map.
- **Maze generation** implemented in `create_grid_worlds.py`.
- **Custom PQ** file/class names added (`custom_pq.py`, `CustomPQ_minG`, `CustomPQ_maxG`).
- **End-to-end runs tested** to produce valid JSON schemas per `student-readme.md`.

---

## The main algorithmic ideas (teaching section)

### 1) Agent knowledge model (“fog of war”)
The agent does *not* know the full grid initially. It assumes unknown cells are traversable until observed blocked.

- `GridWorld.true_blocked[r][c]`: the actual maze (ground truth)
- `GridWorld.known[r][c]`: agent belief:
  - UNKNOWN (unseen)
  - FREE
  - BLOCKED

When the agent is at a cell, it calls:
- `grid.observe_from(current_cell)`

This reveals the blocked/free status of the 4 adjacent cells and updates `known`.

During planning, A* expands neighbors using:
- `grid.neighbors(cell)` which filters out **known blocked** cells.

### 2) Single-pass A* (`astar_impl.compute_path`)
`compute_path(grid, start, end, heuristic_fn, search_id, tie_breaking)` computes a shortest path on the **current known map**.

It returns:
- `path`: list of `Cell` from start to goal, or `None` if no path exists in the known map
- `expanded`: the list of expanded cells (used for metrics, and for Adaptive A*’s heuristic update)

**Expanded definition**: a state is counted as expanded when it is popped from the open heap and accepted (not already closed).

### 3) Tie-breaking (`max_g` vs `min_g`)
In A*, many states can have the same \(f=g+h\). Tie-breaking decides which of those gets expanded first.

In `astar_impl.py`, the open list heap key is `(f, tie, counter, cell)`:
- **`min_g`**: `tie = g` → smaller g expanded first among equal f
- **`max_g`**: `tie = -g` → larger g expanded first among equal f

This changes *which equal-cost shortest path* is found and can greatly change the number of expanded nodes.

### 4) Repeated Forward A* (`q2.py`)
Loop:
1. Observe from current cell (updates `known`).
2. Run A* on the known map from current → goal.
3. Follow the planned path step-by-step.
4. If the next step is actually blocked in the true maze, mark it blocked in `known` and **replan**.
5. Stop when reaching goal or when A* returns no path.

Metrics reported:
- `found`: reached goal or not
- `path_length`: executed steps (len(executed)-1) if found else -1
- `expanded`: sum of expanded nodes across all replans
- `replans`: number of A* calls
- `runtime_ms`: measured around the whole run for that maze/variant

### 5) Repeated Backward A* (`q3.py`)
Same replanning loop idea, except each planning step runs A* **from goal to current** on the known map, then reverses the path for execution.

It outputs both:
- `bwd`: backward variant metrics
- `fwd`: forward max_g metrics (calls into `q2`)

### 6) Adaptive A* (`q5.py`)
Same replanning loop as forward, but after each A* call it updates heuristics for expanded states:

For each expanded state \(s\):
\[
h_{new}(s) = g(goal) - g(s)
\]

In code, after `compute_path(...)` returns:
- `goal_cell.g` is the \(g(goal)\) found by the latest search
- each expanded cell’s stored `h` is updated to `goal_g - s.g`

Then future searches use `adaptive_heuristic`:
- if `cell.h` exists, use it; else fall back to Manhattan

This often reduces expansions on later replans.

---

## How to run (from this folder)

### Generate mazes
```bash
python create_grid_worlds.py --num_mazes 50 --seed 42 --output mazes.json
```

### Q2
```bash
python q2.py --maze_file mazes.json --tie_braking both --output results_q2.json
```

### Q3
```bash
python q3.py --maze_file mazes.json --output results_q3.json
```

### Q5
```bash
python q5.py --maze_file mazes.json --output results_q5.json
```

### Visualization
The CLI supports `--show_vis`, but actual visualization code is not implemented (the hook function is a stub).
Also, if `pygame` is not installed, `--show_vis` will raise an error. Headless runs are fine.

---

## Known gaps / follow-ups (things to revisit)

- **Maze generation**: `create_grid_worlds.py` currently uses the DFS/stack approach with a 30% block probability on newly visited neighbors. You mentioned wanting to revisit this; that’s a good next step for performance/consistency of experiments.
- **Custom PQ integration**: `custom_pq.py` exists and satisfies naming, but `compute_path` currently uses `heapq` directly. If you want the extra credit “custom PQ is actually used”, we can swap the open-list implementation to use `CustomPQ_*`.
- **Visualization**: optional; currently not implemented beyond saving the surface if a window exists.

