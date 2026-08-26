# LTPE v6.0 — 3D reference (voxel)

Same locked control loop as the 2D core. Only geometry and neighbor tests change.

Coordinates are `(z, y, x)` with `z` = elevation.

## Locked 3D geometry

| Function | 3D definition |
|---|---|
| `d(p,h)` | 6-connected Manhattan: |\u0394z| + |\u0394y| + |\u0394x| |
| `LineOfSightScan(p)` | Free voxels within Chebyshev range **6** whose 3D Bresenham ray from `p` never hits a wall |
| `has_LOS(p,h)` | Same 3D Bresenham test; endpoints must be free |
| Neighbors | 6-connected (N,S,E,W, up, down) |
| `is_dead_end(n)` | `n` is not the goal **and** every free 6-neighbor is already in `S` |
| `jump_probability` | `0.35` |
| LOS jump target | Visible hub closest to goal estimate |

## 3D heuristics

| Term | Definition |
|---|---|
| A(n) | clip(elev(n) - elev(current) + 0.5, 0, 1) where elev = z / depth |
| B(n) | (free 6-neighbors not in S or D) / 6 |
| H(n) | per-voxel hazard in [0, 1] |
| Initial g-hat | opposite corner of the volume |

## Files

- `ltpe_3d/ltpe3d.py` — voxel grid + 3D loop
- `simulations/run_cave3d_mc.py` — Monte-Carlo on generated 3D caves

Formulas (score, softmax, ritual nudge, alpha, lambda, k, beta, sigma, weights) are unchanged from the white paper.
