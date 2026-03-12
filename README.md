# LTPE – Line-of-Sight Teleport Priority-Guided Escape

**Sparse, goal-directed exploration for confined 3D voids**  
Escape-first algorithm inspired by ant scouts — fast pruning of dead-ends, priority reinforcement on rich branches, probabilistic selection to avoid traps, and layered handling of hybrid environments (natural ↔ engineered transitions).

[![GitHub Pages Proposal](https://img.shields.io/badge/Full%20Proposal-Read%20Here-blue?style=for-the-badge&logo=githubpages)](https://glargod.github.io/LTPE/)

## Quick Overview

In unknown caves, mines, lava tubes, or asteroid structures, the goal is usually **any safe path to exit** — not shortest path or full map. LTPE achieves this with:

- Hub scanning + low-cost LOS jumps
- O(1) dead-end rejection
- Retroactive pri boosts on discoveries
- Stochastic queue selection (weighted lottery + uncertainty decay)
- Independent layers for source-design transitions (e.g., cave → mine drift)

**Simulation highlight**: \~120–150 steps to exit in modeled ant-nest voids vs. 400–800+ for classic DFS/BFS.

## Key Features

- **Escape mode** (exifil): aggressive pruning, strong exit bias (airflow, elevation, gradients)
- **Explore/Map mode** (per-layer): keep-all nodes, systematic coverage
- **Hybrid support**: Transition nodes as exit in old layer, origin in new layer
- **Probabilistic selection**: prevents local optima (e.g., spiral ramps)

## Current Status

- Concept & proposal: live at https://glargod.github.io/LTPE/
- Simulation code: coming soon (Python-based nest generator + LTPE runner)
- Hardware mock-up ideas: smartphone + LiDAR for SAR/mining use

## Installation / Try It

(Once code is added)

```bash
git clone https://github.com/glargod/LTPE.git
cd LTPE
pip install -r requirements.txt
python sim/run_nest.py --trials 100
