## Results analysis (from generated JSON)

This document summarizes the regenerated final results in:
- `results_q2.json` (Part 2: forward repeated A* tie-breaking)
- `results_q3.json` (Part 3: forward vs backward)
- `results_q5.json` (Part 5: adaptive vs forward)

All results below use the **same 50 mazes** from `mazes.json` (generated with `--seed 42`) and report:
- `expanded`: total expanded states across all replans (lower is better)
- `runtime_ms`: end-to-end runtime per maze run (lower is better)
- `path_length`: executed path length if found else `-1`
- `replans`: number of A* calls made during the run

---

## Part 2 — Effects of tie-breaking (Repeated Forward A*)

Comparison: **forward `max_g`** vs **forward `min_g`** (both run on each maze).

### Key outcomes (all 50 mazes)

- **Found rate**: identical
  - `max_g`: 26/50 = **52%**
  - `min_g`: 26/50 = **52%**
- **Expanded**: `max_g` is dramatically better
  - Mean expanded: `max_g` **8,920** vs `min_g` **201,837**
  - Median expanded: `max_g` **8,790** vs `min_g` **242,449**
  - Per-maze wins (expanded): `max_g` better on **46/50**, ties **4/50**, `min_g` better on **0/50**
- **Runtime (ms)**: mirrors expansions (min_g much slower)
  - Mean runtime: `max_g` **76.7 ms** vs `min_g` **1,190.4 ms**
  - Median runtime: `max_g` **80.9 ms** vs `min_g` **1,445.2 ms**

### “Both found” subset (26 mazes where both reached the goal)

This removes the `path_length=-1` cases.

- Mean expanded: `max_g` **10,589** vs `min_g` **283,098**
- Median expanded: `max_g` **9,260.5** vs `min_g` **255,814**
- Mean runtime: `max_g` **94.6 ms** vs `min_g` **1,666.8 ms**

### Explanation to use in the report (what + why)

- **What we observed**: Tie-breaking makes an enormous difference. `max_g` expands ~1–2 orders of magnitude fewer nodes than `min_g` and is correspondingly faster, while both produce the same success rate and (in our runs) the same path length/replans when they succeed.
- **Why (intuition)**: When \(f=g+h\) ties occur, choosing **larger \(g\)** (max_g) tends to pick states that are **closer to the goal** (smaller \(h\)) along the same \(f\)-contour, which focuses the search and reduces exploration of the wavefront. Choosing **smaller \(g\)** (min_g) tends to expand states closer to the start along the contour, which behaves more like broad wavefront expansion.

---

## Part 3 — Forward vs. Backward (Repeated A*)

Comparison: **backward (max_g)** vs **forward (max_g)** on each maze.

### Key outcomes (all 50 mazes)

- **Found rate**: identical
  - `bwd`: 26/50 = **52%**
  - `fwd`: 26/50 = **52%**
- **Expanded**: forward is dramatically better
  - Mean expanded: `fwd` **8,920** vs `bwd` **102,180**
  - Median expanded: `fwd` **8,790** vs `bwd` **101,170**
  - Per-maze wins (expanded): `fwd` better on **50/50** mazes
- **Runtime (ms)**: forward is dramatically faster
  - Mean runtime: `fwd` **77.1 ms** vs `bwd` **1,325.6 ms**
  - Median runtime: `fwd` **82.2 ms** vs `bwd` **1,283.9 ms**
  - Per-maze wins (runtime): `fwd` better on **50/50** mazes

### Explanation to use in the report (what + why)

- **What we observed**: In these 50 maze instances, repeated backward A* expanded far more nodes and took much longer than repeated forward A* (while having the same success rate).
- **Why (plausible mechanism)**: Backward replanning searches from the fixed goal toward a changing agent position. Under partial observability, the “useful” knowledge updates occur around the agent’s current location as it moves. Empirically, planning forward from the agent to the goal aligned better with this knowledge frontier and reduced the number of states expanded per replan.

---

## Part 5 — Adaptive A* vs. Repeated Forward A*

Comparison: **adaptive (max_g)** vs **forward (max_g)** on each maze.

### Key outcomes (all 50 mazes)

- **Found rate**: identical
  - `adaptive`: 26/50 = **52%**
  - `fwd`: 26/50 = **52%**
- **Expanded**: adaptive is better (modest but consistent improvement)
  - Mean expanded: `fwd` **8,920** vs `adaptive` **8,549**
  - Median expanded: `fwd` **8,790** vs `adaptive` **8,717**
  - Per-maze wins (expanded): adaptive better on **34/50**, ties **14/50**, worse **2/50**
- **Runtime (ms)**: small improvement on average, but mixed per-maze
  - Mean runtime: `fwd` **76.0 ms** vs `adaptive` **74.6 ms**
  - Median runtime: `fwd` **81.4 ms** vs `adaptive` **78.6 ms**

### Explanation to use in the report (what + why)

- **What we observed**: Adaptive A* usually expands fewer nodes than repeated forward A* on the same maze (34 wins vs 2 losses; 14 ties). Runtime improves slightly on average, but is not consistently better on every maze (timing noise is plausible given small absolute runtimes).
- **Why (intuition)**: Adaptive A* updates the heuristic of expanded states using:
  - \(h_{new}(s) = g(goal) - g(s)\)
  This increases heuristic values toward better lower bounds (while maintaining admissibility/consistency under the assignment’s assumptions), focusing later replans and reducing expansions.

---

## Part 6 — Statistical significance (ready-to-paste plan)

Because each comparison is evaluated on the **same 50 mazes**, use a **paired** hypothesis test on the per-maze metric differences.

### Recommended metric

Use `expanded` as the primary metric:
- It is deterministic given a fixed tie-breaking rule and maze.
- It is less sensitive to machine load than runtime.

### Sign test (simple, assumption-light, paired)

For a chosen comparison (e.g., Part 2 `min_g` vs `max_g`), define for each maze \(i\):
- \(d_i = expanded_{B,i} - expanded_{A,i}\)

Ignore ties (\(d_i=0\)). Let:
- \(W\) be the number of mazes with \(d_i < 0\) (B wins),
- \(L\) be the number with \(d_i > 0\) (B losses),
- \(n=W+L\).

Null hypothesis: \(H_0\): \(P(\text{B wins}) = 0.5\) (no systematic difference).  
Alternative: \(H_1\): \(P(\text{B wins}) \ne 0.5\) (two-sided).

Compute an exact two-sided p-value under a Binomial(\(n, 0.5\)) model.

### Exact sign-test results on our data (expanded)

- **Part 2** (`min_g` vs `max_g`): wins=0, losses=46, ties=4 → \(p \approx 2.84\\times 10^{-14}\)
- **Part 3** (`bwd` vs `fwd`): wins=0, losses=50, ties=0 → \(p \approx 1.78\\times 10^{-15}\)
- **Part 5** (`adaptive` vs `fwd`): wins=34, losses=2, ties=14 → \(p \approx 1.94\\times 10^{-8}\)

Interpretation (with \(\alpha = 0.05\)): for expansions, the differences above are very unlikely to be due to sampling noise in these 50 mazes.

### Note on runtime significance (optional)

If you also test `runtime_ms`, use the same paired framework, but note runtime has additional variance from the OS and Python runtime environment. In our regenerated sample, `adaptive` vs `fwd` runtime sign-test gives wins=25, losses=25 (no ties), so two-sided \(p = 1.0\), i.e., no detectable paired advantage in runtime despite small mean/median differences.

