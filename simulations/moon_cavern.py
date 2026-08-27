"""Hypothetical lunar lava-tube volume for LTPE v6.0.

Geology is schematic, not a mapped pit:
  - sinuous main tube in mare basalt
  - inflation-lobe side galleries
  - collapse chimneys / skylights (surface exit)
  - breakdown rubble (hazard)
  - cold-trap ice in deep shadowed recesses (annotated only)
  - radiation penalty near open skylights

Coordinates match ltpe_3d: (z, y, x), higher z = toward surface.
Start is deep in the tube. Goal is a skylight lip.
"""
from __future__ import annotations

import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from ltpe_3d.ltpe3d import Grid3D


def _solid(d, h, w):
    return [[[1 for _ in range(w)] for _ in range(h)] for _ in range(d)]


def _carve_ball(walls, z, y, x, rz, ry, rx):
    d, h, w = len(walls), len(walls[0]), len(walls[0][0])
    for zz in range(max(1, z - rz), min(d - 1, z + rz + 1)):
        for yy in range(max(1, y - ry), min(h - 1, y + ry + 1)):
            for xx in range(max(1, x - rx), min(w - 1, x + rx + 1)):
                if ((zz - z) / max(1, rz)) ** 2 + ((yy - y) / max(1, ry)) ** 2 + (
                    (xx - x) / max(1, rx)
                ) ** 2 <= 1.05:
                    walls[zz][yy][xx] = 0


def _carve_line(walls, a, b, r=1):
    z0, y0, x0 = a
    z1, y1, x1 = b
    n = max(abs(z1 - z0), abs(y1 - y0), abs(x1 - x0), 1)
    for i in range(n + 1):
        t = i / n
        z = int(round(z0 + t * (z1 - z0)))
        y = int(round(y0 + t * (y1 - y0)))
        x = int(round(x0 + t * (x1 - x0)))
        _carve_ball(walls, z, y, x, r, r, r + 1)


def make_moon_cavern(w=29, h=19, d=12, seed=0):
    """Return Grid3D, start, goal, meta dict."""
    rng = random.Random(seed)
    walls = _solid(d, h, w)

    z_tube = 2 + rng.randint(0, 1)
    y_mid = h // 2
    points = []
    y, z = y_mid, z_tube
    for x in range(2, w - 2):
        if rng.random() < 0.35:
            y = max(3, min(h - 4, y + rng.choice((-1, 0, 1))))
        if rng.random() < 0.18:
            z = max(2, min(d // 2, z + rng.choice((-1, 0, 1))))
        points.append((z, y, x))
        _carve_ball(walls, z, y, x, 1, 2 if rng.random() < 0.25 else 1, 2)

    start = points[1]
    walls[start[0]][start[1]][start[2]] = 0

    for _ in range(rng.randint(2, 4)):
        base = points[rng.randrange(len(points) // 4, len(points) * 3 // 4)]
        dy = rng.choice((-1, 1)) * rng.randint(3, 6)
        end = (base[0], max(2, min(h - 3, base[1] + dy)), base[2] + rng.randint(-1, 2))
        _carve_line(walls, base, end, r=1)
        _carve_ball(walls, *end, 2, 2, 2)

    lip = points[-3]
    sky_z = d - 2
    sky = (sky_z, lip[1], lip[2])
    _carve_line(walls, lip, sky, r=1)
    _carve_ball(walls, sky_z, sky[1], sky[2], 1, 2, 2)
    if rng.random() < 0.45:
        mid = points[len(points) // 2]
        sky2 = (sky_z, mid[1], mid[2])
        _carve_line(walls, mid, sky2, r=1)

    goal = sky
    walls[goal[0]][goal[1]][goal[2]] = 0
    walls[start[0]][start[1]][start[2]] = 0

    elevation = [[[zz / max(1, d - 1) for _x in range(w)] for _y in range(h)] for zz in range(d)]
    hazard = [[[0.0 for _x in range(w)] for _y in range(h)] for zz in range(d)]
    ice = set()

    for z in range(d):
        for y in range(h):
            for x in range(w):
                if walls[z][y][x]:
                    continue
                if z >= d - 3:
                    hazard[z][y][x] = max(hazard[z][y][x], 0.35 + 0.25 * (z / max(1, d - 1)))
                if rng.random() < 0.06:
                    hazard[z][y][x] = max(hazard[z][y][x], 0.55)
                if z <= 3 and rng.random() < 0.04:
                    ice.add((z, y, x))
                    elevation[z][y][x] = min(1.0, elevation[z][y][x] + 0.12)

    meta = {"kind": "moon_lava_tube", "ice": ice, "skylight": goal, "start": start}
    return Grid3D(walls, elevation, hazard), start, goal, meta
