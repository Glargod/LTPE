# LTPE v6.0 — locked 2D reference choices

The white paper left a few simulator-only details unspecified. This file locks them for the executable core.

## Geometry

| Function | Locked definition |
|---|---|
| `d(p,h)` | 4-connected Manhattan distance |
| `LineOfSightScan(p)` | All free cells within Chebyshev range 8 whose Bresenham ray from `p` never hits a wall |
| `has_LOS(p,h)` | Same Bresenham test; endpoints must be free |
| `is_dead_end(n)` | `n` is not the goal **and** every free 4-neighbor is already in the visited set `S` |
| `jump_probability` | `0.35` |
| LOS jump target | Among currently visible hubs, the one closest to $\hat{g}$ |

## Domain heuristics for the 2D cave maps

| Term | Definition |
|---|---|
| $A(n)$ | `clip(elevation(n) - elevation(current) + 0.5, 0, 1)` with elevation = row / height (higher row = exit-ward) |
| $B(n)$ | (count of free 4-neighbors not in `S` or `D`) / 4 |
| $H(n)$ | per-cell hazard in `[0,1]` (sparse random hotspots on generated maps) |
| Initial $\hat{g}$ | opposite corner of the map (weak exit prior). Updated only when the chosen cell is closer to the **true** goal |

## Files

- `ltpe_core/ltpe.py` — full control loop
- `simulations/run_cave_mc.py` — Monte-Carlo harness on generated caves
- `LTPE_ESP32.ino` — same score / nudge / softmax loop on a servo-swept LiDAR

These maps are **not** the unpublished campaigns that produced the 8–16% paper figures. They are a faithful, inspectable reference so v6.0 is no longer paper-only.
