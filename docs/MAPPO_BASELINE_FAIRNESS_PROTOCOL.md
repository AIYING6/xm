# MAPPO Baseline Fairness Protocol (v1.5) — FROZEN

**Status:** FROZEN (immutable; created before any MAPPO validation result exists)
**Date:** 2026-08-06
**Tag:** `mappo-fairness-freeze-v1.5.0`
**Worktree:** `mappo-baseline-v1.5` @ 65bd96c (post 24-checkpoint lock)

## 0. Precondition

The v1.5 8-method validation is locked immutably
(`formal-ablation-validation-lock-v1.5.0`, 24 checkpoints). MAPPO joins as a
9th method with a SEPARATE 3-checkpoint lock. The joint 27-checkpoint
held-out manifest is built only after both locks exist.

## 1. Purpose

Add MAPPO (canonical cooperative/CTDE-PPO) as a standard external baseline
without re-running existing methods and without touching the frozen held-out
test.

## 2. BC initialization adjudication (FROZEN before any MAPPO validation)

Verified facts: all v1.4 methods (incl. HAPPO) and all v1.5 ablations start
from BC initialization with the same demo data and BC budget
(`pretrain_ri_gmappo_3d_bc.py`: episodes=120, epochs=20).

Decision: MAPPO receives an **equivalent warm-start**:
- SAME demo data source
- SAME BC budget (episodes=120, epochs=20)
- MAPPO's OWN network structure (shared MLP actor + centralized MLP critic;
  the EA-RG BC cannot be loaded because the architectures differ)
- 3 BC seeds 0/1/2 corresponding to the PPO seeds

This decision is made BEFORE looking at any MAPPO validation result. BC will
NOT be added later to rescue weak MAPPO performance.

## 3. Fairness matrix (identical to v1.5 Full unless noted)

| Item | Requirement |
|---|---|
| Environment | Same 3D strict-sensing environment as v1.5 Full |
| Rewards | Identical reward coefficients |
| Observations/actions | Same information boundary; NO failure ground-truth added |
| Comm failure | Same dropout / delay / failed-agent / topology mechanics |
| Training seeds | 0, 1, 2 |
| PPO budget | 977 updates, same rollout/sampling budget |
| Checkpoints | 100, 200, ..., 900, 977 (durable training state + optimizer) |
| Validation | base_seed 641939, 4 scenarios x 50 episodes |
| Selector | Same `v1_5_wilson` |
| Collision gate | Same (0.0 hard ineligibility) |
| Parameter count | Reported separately; NOT forced equal to EA-RG (report & explain) |
| MAPPO structure | Standard shared actor + centralized critic; MUST NOT include EA-RG-only relation/gate modules |

## 4. Architecture (FROZEN)

- **Shared actor** (canonical MAPPO) + **role one-hot** appended to the
  per-agent observation.
- The role one-hot is used ONLY as an identity/role observation: NO failure
  ground-truth, NO graph relation, NO EA-RG-specific information. Without it a
  single shared policy cannot distinguish the 3 heterogeneous UAV roles; this
  matches the information boundary (roles are observable as in other methods).
- **Centralized critic** over the global state (share_obs), canonical MAPPO.
- Decided BEFORE validation; the shared+role-hot vs per-role actor variants
  will NOT be selected by validation performance.

## 5. Dev-seed policy (888000)

888000 is used ONLY for correctness smoke: env loads, actor/critic dims,
checkpoint save/load round-trip, episode fields complete (failure_exposed /
recovered derivable), and the `v1_5_wilson` selector consumes MAPPO output.
Performance MUST NOT tune network or hyperparameters.

## 6. Effective-config diff audit

Machine diff between MAPPO config and frozen v1.5 Full config shows
differences ONLY in the algorithm-structure whitelist:

```text
EA-RG graph actor / multi-relation modules  -> absent (standard MLP actor)
graph-aware components                       -> absent
centralized critic                           -> MAPPO canonical MLP critic
```

Environment, budget, rewards, seeds, checkpoint nodes, validation split,
selector, collision gate: ZERO non-whitelisted differences.

## 7. Formal pipeline (stage gates)

1. Freeze this protocol + config (commit + tag)
2. Adapt 3D training entrypoint (new formal scripts, NOT the old 2D simplified
   entry; env params programmatically inherited from the frozen formal config
   to prevent drift in target_speed / communication_radius /
   strict_target_sensing / failure timing / dropout-delay / horizon / rewards)
3. Wire 100..977 checkpoints + durable training state + optimizer
4. Wire v1.5 episode statistics + unified selection schema
5. Unit tests + checkpoint-load test + effective-config diff audit
6. Tiny temporary BC smoke (structure + load of the full chain)
7. Generate formal 3-seed BC (episodes=120, epochs=20); audit BC (loadable,
   architecture, config, seed, SHA)
8. 888000 minimal correctness smoke on BC + PPO chain
9. Freeze MAPPO code, config, BC manifest (commit + tags)
10. Formal PPO training seeds 0/1/2 to 977
11. 3/3 training audit
12. Evaluate 641939 (6000 episodes per method)
13. 3/3 unique selection + SHA lock (separate 3-checkpoint lock)
14. Build 27-checkpoint joint held-out manifest

Notes: 888000 smoke happens before formal PPO; formal BC is generated only
after the tiny temporary BC chain smoke passes; once formal BC is complete,
downstream results must NOT modify config.

## 8. Locking

- 24-checkpoint v1.5 lock: IMMUTABLE, untouched.
- MAPPO: separate 3-checkpoint lock.
- Joint 27-checkpoint manifest for the single one-shot held-out test.

## 9. Efficiency reporting

Parameter count and inference cost of MAPPO are reported separately (expected
to differ from EA-RG due to absent graph modules); reported and explained,
not hidden.
