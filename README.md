# LTPE – Line-of-Sight Priority-Guided Escape

**Sparse, goal-biased exploration for confined 3D voids**  
Designed to minimize steps to exit in irregular environments where mapping is secondary to survival.

[📄 Full Concept & Proposal](https://glargod.github.io/LTPE/)

## Quick Summary

LTPE uses:
- Hub scanning + low-cost LOS relocation
- Rapid dead-end pruning
- Retroactive priority reinforcement
- Probabilistic queue selection (weighted lottery + uncertainty decay + 5–10% random pull)
- Layered handling for source-design transitions (e.g. cave → mine drift)
- Separate anomalies layer for subtle "butler" exits (narrow cracks, airflow spikes, etc.)

**Illustrative reasoning** on representative ant-nest topologies (\~60 segments, branch factor 2–5):  
≈120–150 steps to exit (with stochastic selection)  
vs. classic DFS ≈400–800+ steps

These are analytic estimates from branching structure probabilities — full Monte-Carlo validation planned.

## Status

- Concept & proposal: complete at https://glargod.github.io/LTPE/
- Code: skeleton / coming soon
- Hardware ideas: smartphone + LiDAR for SAR/mining

Contributions welcome — forks, PRs, sim ideas, sensor models.

License: CC-BY-4.0 (docs), TBD (code)

🐜🪐 Let's build escape tools that actually save lives.
