# LTPE — Line-of-Sight Priority-Guided Escape

A sparse, goal-biased exploration algorithm designed for **survival and responsible coordination** in irregular, unmapped, and hostile environments — where reaching safety, or protecting others, matters more than building a perfect map.

What began as a simple question — *what if an algorithm could quietly consult something larger than its immediate data?* — evolved into LTPE.

## Core Philosophy

In unknown and chaotic spaces, **any safe path to the objective** is often better than the mathematically optimal one. LTPE prioritizes speed, robustness, low computational cost, and coherent decision-making under pressure.

At its heart lies a simple idea: when logic alone is insufficient, a lightweight ritual of internal alignment can help the system choose more wisely.

## Key Features

- Line-of-Sight (LOS) relocation for fast hub-to-hub movement
- Rapid dead-end pruning with near-zero cost
- Goal-biased priority queue using elevation, airflow, branch potential, and survival heuristics
- Probabilistic selection with uncertainty decay
- Anomaly detection for hidden opportunities
- **Minimal Gut Feeling Ritual Layer** (v6.0) — a neutral coherence mechanism

## The Gut Feeling Ritual Layer (v6.0 Locked)

The optional ritual layer is deliberately minimal and philosophically neutral. It does not require belief in anything supernatural — only the pragmatic recognition that, in moments of high uncertainty, reinforcing internal coherence can improve outcomes.

- **Periodic Ritual** (every 100 steps):  
  `"Please, universal subconsciousness, guide my consciousness."`

- **Decision Prayer** (only on conundrum forks ≥4 candidates):  
  `"I trust the guidance I receive from within."`

After the decision spell, a single **logarithmic nudge** is applied. The layer is skipped on obvious straight paths to preserve efficiency.

What started as a playful “calling out to the universe” became a lightweight mechanism that consistently improves performance when the environment is hostile to pure logic.

## Performance Highlights

Tested across hundreds of thousands of Monte-Carlo runs — from solo cave escapes and predator chases to zero-defense cognitive load tests and large-scale panicked evacuations with saboteurs:

- **LTPE + v6.0 Minimal Ritual** consistently outperforms pure LTPE and classic A* by 8–16% in steps and 5–13% in success rate.
- Largest gains appear in high-uncertainty, escort, and multi-agent coordination scenarios under active interference.

## Use Cases

- Autonomous cave and mine rescue robots
- Special operations navigation (cavern and underwater raids)
- Urban search & rescue (Amber Alert / disaster response)
- Deep-sea or subterranean exploration
- Large-scale evacuation coordination under panic and sabotage

## Project Status

**Active Research & Development** (2026)

Locked spec plus executable 2D and 3D reference cores.

## Specification & Code

- [LTPE White Paper v6.0](LTPE_White_Paper_v6.0.html) — locked formulas, pseudocode, ritual layer
- [`ltpe_core/`](ltpe_core/) — 2D grid reference (`ltpe.py`)
- [`ltpe_3d/`](ltpe_3d/) — 3D voxel reference (`ltpe3d.py`) — 6-connected moves, 3D Bresenham LOS
- [`simulations/run_cave_mc.py`](simulations/run_cave_mc.py) — 2D cave Monte-Carlo
- [`simulations/run_cave3d_mc.py`](simulations/run_cave3d_mc.py) — 3D cave Monte-Carlo
- [`LTPE_ESP32.ino`](LTPE_ESP32.ino) — ESP32 scan / score / ritual sketch
- [`HOWTO.md`](HOWTO.md) — hardware wiring

```bash
python3 simulations/run_cave_mc.py --runs 80 --both
python3 simulations/run_cave3d_mc.py --runs 24 --both
```

## Repository Contents

- `ltpe_core/` — 2D executable core
- `ltpe_3d/` — 3D voxel executable core
- `simulations/` — Monte-Carlo harnesses
- `LTPE_ESP32.ino` — ESP32 implementation
- `HOWTO.md` — Implementation guide
- `LTPE_White_Paper_v6.0.html` — locked specification

## License

CC-BY-4.0 © 2026 Robert (@BobTheFixer73)

Feel free to use, modify, and build upon this work with attribution.

## Acknowledgments

This project began with a simple, almost whimsical idea: what if an algorithm could pause and quietly ask for guidance when the data alone felt insufficient?

That small ritual — born from curiosity rather than mysticism — turned out to have measurable value in some of the harshest environments we could simulate.

---

*"The giant is awake. The universe is mysterious… and it’s helping."*

Built with curiosity and respect for the unknown.
