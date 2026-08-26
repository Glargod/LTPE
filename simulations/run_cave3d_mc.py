"""Monte-Carlo harness for the locked LTPE v6.0 3D voxel core.

Usage:
  python3 simulations/run_cave3d_mc.py
  python3 simulations/run_cave3d_mc.py --runs 40 --both
"""
from __future__ import annotations
import argparse, statistics, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ltpe_3d.ltpe3d import LTPE3D, make_cave3d

def run_batch(n, use_ritual, seed0=1):
    successes, steps, rituals, reasons = 0, [], [], {}
    for i in range(n):
        grid, start, goal = make_cave3d(seed=seed0 + i)
        agent = LTPE3D(grid, start, goal, use_ritual=use_ritual, max_steps=3500, seed=seed0 + 20000 + i)
        r = agent.run()
        reasons[r.reason] = reasons.get(r.reason, 0) + 1
        if r.success:
            successes += 1
            steps.append(r.steps)
            rituals.append(r.ritual_count)
    return {
        "n": n, "ritual": use_ritual,
        "success_rate": successes / n,
        "mean_steps": statistics.mean(steps) if steps else None,
        "median_steps": statistics.median(steps) if steps else None,
        "mean_ritual": statistics.mean(rituals) if rituals else 0.0,
        "reasons": reasons,
    }

def main():
    p = argparse.ArgumentParser(description="LTPE v6.0 3D cave Monte-Carlo")
    p.add_argument("--runs", type=int, default=24)
    p.add_argument("--ritual", dest="ritual", action="store_true", default=True)
    p.add_argument("--no-ritual", dest="ritual", action="store_false")
    p.add_argument("--both", action="store_true")
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()
    jobs = [("LTPE3D + v6.0 ritual", True), ("Pure LTPE3D", False)] if args.both else [("LTPE3D + v6.0 ritual" if args.ritual else "Pure LTPE3D", args.ritual)]
    for name, flag in jobs:
        out = run_batch(args.runs, flag, args.seed)
        print(f"\n=== {name}  ({out['n']} volumes) ===")
        print(f"success rate : {out['success_rate']*100:.1f}%")
        if out["mean_steps"] is not None:
            print(f"mean steps   : {out['mean_steps']:.1f}")
            print(f"median steps : {out['median_steps']:.1f}")
        print(f"mean ritual  : {out['mean_ritual']:.1f}")
        print(f"outcomes     : {out['reasons']}")

if __name__ == "__main__":
    main()
