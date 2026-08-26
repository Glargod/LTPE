"""
LTPE v6.0 reference core — 2D grid implementation of the locked white-paper loop.

This file is the executable ground truth for:
  LineOfSightScan / has_LOS
  is_dead_end
  A(n), B(n), H(n)
  jump_probability
  score, softmax selection, ritual log-nudge
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Optional


# --- Locked defaults (white paper §6) ---------------------------------------

ALPHA = 0.25          # LOS cost factor in [0.20, 0.35]
K = 5                 # top-k in [4, 6]
LAMBDA = 0.15         # ritual nudge in [0.08, 0.22]
T_PERIOD = 100        # periodic ritual marker
SIGMA = 0.40          # uncertainty scale in [0.3, 0.5]
BETA = 1.4            # softmax temperature in [1.0, 1.8]
W1, W2, W3, W4 = 0.40, 0.25, 0.20, 0.15
JUMP_PROBABILITY = 0.35
MAX_SCAN_RANGE = 8    # cells; finite LiDAR-style scan


DIRS4 = ((0, 1), (1, 0), (0, -1), (-1, 0))


def manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


@dataclass
class Grid:
    """0 = free, 1 = wall. Optional per-cell elevation and hazard in [0, 1]."""

    walls: list[list[int]]
    elevation: Optional[list[list[float]]] = None
    hazard: Optional[list[list[float]]] = None

    @property
    def h(self) -> int:
        return len(self.walls)

    @property
    def w(self) -> int:
        return len(self.walls[0]) if self.walls else 0

    def in_bounds(self, p: tuple[int, int]) -> bool:
        y, x = p
        return 0 <= y < self.h and 0 <= x < self.w

    def free(self, p: tuple[int, int]) -> bool:
        return self.in_bounds(p) and self.walls[p[0]][p[1]] == 0

    def elev(self, p: tuple[int, int]) -> float:
        if self.elevation is None:
            return 0.0
        return self.elevation[p[0]][p[1]]

    def haz(self, p: tuple[int, int]) -> float:
        if self.hazard is None:
            return 0.0
        return self.hazard[p[0]][p[1]]

    def neighbors4(self, p: tuple[int, int]) -> list[tuple[int, int]]:
        y, x = p
        out = []
        for dy, dx in DIRS4:
            q = (y + dy, x + dx)
            if self.free(q):
                out.append(q)
        return out


def bresenham(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    """Inclusive cells on the integer line from a to b."""
    y0, x0 = a
    y1, x1 = b
    cells = []
    dy = abs(y1 - y0)
    dx = abs(x1 - x0)
    sy = 1 if y0 < y1 else -1
    sx = 1 if x0 < x1 else -1
    err = dx - dy
    y, x = y0, x0
    while True:
        cells.append((y, x))
        if (y, x) == (y1, x1):
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy
    return cells


def has_los(grid: Grid, p: tuple[int, int], h: tuple[int, int]) -> bool:
    """True iff the Bresenham ray from p to h never hits a wall."""
    if not grid.free(p) or not grid.free(h):
        return False
    cells = bresenham(p, h)
    for c in cells[1:-1]:
        if not grid.free(c):
            return False
    return True


def line_of_sight_scan(grid: Grid, p: tuple[int, int], max_range: int = MAX_SCAN_RANGE) -> set[tuple[int, int]]:
    visible: set[tuple[int, int]] = set()
    py, px = p
    for y in range(max(0, py - max_range), min(grid.h, py + max_range + 1)):
        for x in range(max(0, px - max_range), min(grid.w, px + max_range + 1)):
            q = (y, x)
            if q == p or not grid.free(q):
                continue
            if max(abs(y - py), abs(x - px)) > max_range:
                continue
            if has_los(grid, p, q):
                visible.add(q)
    visible.add(p)
    return visible


def is_dead_end(grid: Grid, n: tuple[int, int], visited: set[tuple[int, int]], goal: tuple[int, int]) -> bool:
    if n == goal:
        return False
    opens = grid.neighbors4(n)
    if not opens:
        return True
    return all(q in visited for q in opens)


def branch_potential(grid: Grid, n: tuple[int, int], visited: set[tuple[int, int]], dead: set[tuple[int, int]]) -> float:
    raw = sum(1 for q in grid.neighbors4(n) if q not in visited and q not in dead)
    return raw / 4.0


def survival_bias_A(grid: Grid, n: tuple[int, int], current: tuple[int, int]) -> float:
    return max(0.0, min(1.0, grid.elev(n) - grid.elev(current) + 0.5))


def hazard_H(grid: Grid, n: tuple[int, int]) -> float:
    return max(0.0, min(1.0, grid.haz(n)))


def score_node(grid, n, current, g_hat, visited, dead, rng) -> float:
    dist = manhattan(n, g_hat)
    goal_term = 1.0 / (dist + 1.0)
    A = survival_bias_A(grid, n, current)
    B = branch_potential(grid, n, visited, dead)
    Hn = hazard_H(grid, n)
    eps = rng.uniform(0.0, SIGMA)
    return W1 * goal_term + W2 * A + W3 * B - W4 * Hn + eps


def ritual_nudge(scores_sorted_desc, m, k, lam=LAMBDA):
    out = []
    kk = max(1, k)
    logm = math.log(1.0 + m)
    for i, s in enumerate(scores_sorted_desc):
        factor = 1.0 - lam * logm * (i / kk)
        out.append(s * max(0.05, factor))
    return out


def weighted_lottery(items, beta, rng):
    weights = [max(1e-9, s) ** beta for s, _n in items]
    total = sum(weights)
    pick = rng.random() * total
    acc = 0.0
    for w, (_s, n) in zip(weights, items):
        acc += w
        if pick <= acc:
            return n
    return items[-1][1]


@dataclass
class Result:
    success: bool
    steps: float
    path: list[tuple[int, int]]
    ritual_count: int
    reason: str


@dataclass
class LTPE:
    grid: Grid
    start: tuple[int, int]
    goal: tuple[int, int]
    use_ritual: bool = True
    max_steps: int = 2000
    seed: Optional[int] = None
    jump_probability: float = JUMP_PROBABILITY
    alpha: float = ALPHA
    k: int = K
    lam: float = LAMBDA
    beta: float = BETA
    rng: random.Random = field(init=False)

    def __post_init__(self):
        self.rng = random.Random(self.seed)

    def run(self) -> Result:
        current = self.start
        H = {current}
        S = {current}
        D = set()
        g_hat = (self.grid.h - 2, self.grid.w - 2)
        steps = 0.0
        ritual_count = 0
        path = [current]
        integer_steps = 0

        while integer_steps < self.max_steps:
            integer_steps += 1
            visible = line_of_sight_scan(self.grid, current)
            H |= visible

            hubs = [h for h in H if h != current and has_los(self.grid, current, h)]
            if hubs and self.rng.random() < self.jump_probability:
                h = min(hubs, key=lambda q: manhattan(q, g_hat))
                current = h
                steps += self.alpha * manhattan(current, h)
                S.add(current)
                path.append(current)
                if current == self.goal:
                    return Result(True, steps, path, ritual_count, "goal")

            for n in self.grid.neighbors4(current):
                if is_dead_end(self.grid, n, S, self.goal):
                    D.add(n)

            candidates = []
            for n in self.grid.neighbors4(current):
                if n in D:
                    continue
                s = score_node(self.grid, n, current, g_hat, S, D, self.rng)
                candidates.append((s, n))

            if not candidates:
                back = [q for q in self.grid.neighbors4(current) if q in S]
                if not back:
                    return Result(False, steps, path, ritual_count, "trapped")
                current = back[self.rng.randrange(len(back))]
                steps += 1.0
                path.append(current)
                continue

            candidates.sort(key=lambda t: t[0], reverse=True)
            top_k = candidates[: min(self.k, len(candidates))]

            if self.use_ritual and (integer_steps % T_PERIOD == 0 or len(top_k) >= 4):
                if len(top_k) >= 4:
                    ritual_count += 1
                    nudged = ritual_nudge([s for s, _ in top_k], ritual_count, len(top_k), self.lam)
                    top_k = [(nudged[i], top_k[i][1]) for i in range(len(top_k))]

            chosen = weighted_lottery(top_k, self.beta, self.rng)
            if manhattan(chosen, self.goal) < manhattan(g_hat, self.goal):
                g_hat = chosen

            current = chosen
            steps += 1.0
            S.add(current)
            path.append(current)
            if current == self.goal:
                return Result(True, steps, path, ritual_count, "goal")

        return Result(False, steps, path, ritual_count, "max_steps")


def make_cave(w: int = 41, h: int = 31, seed: int = 0, wall_p: float = 0.28):
    rng = random.Random(seed)
    walls = [[1 if rng.random() < wall_p else 0 for _ in range(w)] for _ in range(h)]
    for x in range(w):
        walls[0][x] = walls[h - 1][x] = 1
    for y in range(h):
        walls[y][0] = walls[y][w - 1] = 1
    start = (1, 1)
    goal = (h - 2, w - 2)
    y, x = start
    walls[y][x] = 0
    while (y, x) != goal:
        if rng.random() < 0.55 and x < goal[1]:
            x += 1
        elif rng.random() < 0.55 and y < goal[0]:
            y += 1
        elif rng.random() < 0.5 and x > 1:
            x -= 1
        elif y > 1:
            y -= 1
        else:
            x = min(w - 2, x + 1)
        walls[y][x] = 0
    walls[goal[0]][goal[1]] = 0
    walls[start[0]][start[1]] = 0
    elevation = [[y / max(1, h - 1) for _x in range(w)] for y in range(h)]
    hazard = [[0.15 if walls[y][x] == 0 and rng.random() < 0.08 else 0.0 for x in range(w)] for y in range(h)]
    return Grid(walls, elevation, hazard), start, goal
