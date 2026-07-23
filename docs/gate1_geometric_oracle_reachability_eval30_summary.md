# Gate 1 Geometric-Oracle Reachability Diagnostic

Last updated: 2026-07-22

## Purpose

This diagnostic checks whether the nominal maneuvering-target scenarios are reachable under the current 3DOF dynamics, high-level action interface, and attack-window definition. It uses a deterministic non-learning geometric policy instead of trained checkpoints.

This answers the question raised by the learned-policy reachability analysis: seed 1 could reduce range but could not convert approach into attack geometry. The oracle determines whether this is a policy-learning problem or an environment-feasibility problem.

## Artifacts

Main matched evaluation:

- `scripts/analyze_3d_geometric_oracle_reachability.py`
- `results/gate1_geometric_oracle_reachability_offset_eval30/summary.csv`
- `results/gate1_geometric_oracle_reachability_offset_eval30/step_trace.csv`
- `results/gate1_geometric_oracle_reachability_offset_eval30/summary.md`

Mode controls:

- `results/gate1_geometric_oracle_reachability_direct_mild_eval30/summary.csv`
- `results/gate1_geometric_oracle_reachability_lead_mild_eval30/summary.csv`

## Main Result

The offset geometric oracle was evaluated on the same `base_seed=409000` and `30` episodes used by the learned-policy reachability diagnostic.

| Case | Mode | Target | Success | Collision | Min range | Range reduction | Tracking | Max geometry | Geometry > 0.25 | Attack-window episodes |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `weaving_tiny_offset` | `offset` | `weaving_tiny` | 1.000 | 0.000 | 9486.5 | 15213.4 | 0.518 | 0.576 | 1.000 | 1.000 |
| `weaving_mild_offset` | `offset` | `weaving_mild` | 1.000 | 0.000 | 9266.8 | 15433.1 | 0.515 | 0.624 | 1.000 | 1.000 |

## Mode Control on `weaving_mild`

| Case | Mode | Success | Collision | Max geometry | Attack-window episodes |
|---|---|---:|---:|---:|---:|
| `weaving_mild_direct` | `direct` | 0.667 | 0.367 | 0.520 | 0.667 |
| `weaving_mild_lead` | `lead` | 1.000 | 0.000 | 0.566 | 1.000 |
| `weaving_mild_offset` | `offset` | 1.000 | 0.000 | 0.624 | 1.000 |

## Interpretation

The maneuvering-target environment is feasible. A simple lead/offset geometric policy can reliably form attack windows in nominal `weaving_mild` with zero collisions.

Therefore, the current learned-policy weakness is not caused by impossible dynamics or an invalid attack-window definition. The main gap is that PPO fine-tuning from straight-target policies does not reliably learn the phase transition from range reduction to safe attack-geometry formation.

This also explains the seed-1 behavior observed in `docs/gate1_maneuver_reachability_curriculum_3seed_eval30_summary.md`: seed 1 can approach the target but does not discover or preserve the lead/offset geometry needed for attack-window closure.

## Decision

Do not reduce `weaving_mild` difficulty yet. Do not spend a five-seed formal training budget yet.

The next training route should use the oracle as a development tool:

- generate matched oracle demonstration traces for `weaving_tiny` and `weaving_mild`;
- use them for behavior-cloning warm start or auxiliary action imitation during Stage 1 nominal maneuvering training;
- then fine-tune with PPO and compare against the current curriculum-only baseline.

The oracle remains an auxiliary tool and engineering baseline. It is not a main paper contribution.

## Next Acceptance Gate

Before adding strict sensing or relay failure to maneuvering targets:

- `multi_relation` should reach roughly `60%` to `80%` nominal `weaving_mild` success across development seeds;
- collision rate should stay low;
- at least one ablation or baseline should remain clearly weaker;
- results should be selected on validation episodes and tested on disjoint matched episodes.
