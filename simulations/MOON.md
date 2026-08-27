# Hypothetical lunar lava tube

Schematic Mare-style volume for LTPE v6.0. Not a mapped pit.

- `moon_cavern.py` — carves a sinuous tube, inflation lobes, collapse chimney, skylight
- `run_moon_mc.py` — Monte-Carlo against the locked 3D core
- `moon_cavern_viz.html` + `moon_cavern_viz.js` — multilevel browser escape

```bash
python3 simulations/run_moon_mc.py --runs 20 --both
```

Start is deep in the gallery. Goal is the skylight lip (high Z / vacuum).
Hazard rises near the lip (radiation / thermal shock) and on breakdown rubble.
Ice pockets sit in the deep shadow and slightly raise the elevation term.
