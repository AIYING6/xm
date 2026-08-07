# P3-A OOD Generalization Protocol v1.1 (exact cell definitions)

- status: **FROZEN** (tag: `p3a-ood-protocol-v1.1`); supersedes v1.0.
- Amendment trigger: v1.0 left G/C definitions with "e.g."; v1.1 fixes EXACT generation
  rules. This amendment was made BEFORE any OOD performance was viewed, so it is legitimate.
- Unchanged from v1.0: scientific question, methods, estimand, Decision Gate.
- Upstream: `p3a-ood-protocol-v1.0`, `paper-v1.6-p2.5-content-ready`,
  `formal-held-out-results-lock-v1.5.1`, `survival-protocol-v1.1`.

## 1. Exact OOD cell definitions (no e.g. anywhere)

| cell | exact rule |
|---|---|
| **G1** | blue horizontal formation: scale spacing × **1.20** about the blue centroid, then rotate +**20°** in the world XY plane; height/speed/heading/gamma unchanged |
| **G2** | target: horizontal range from current blue centroid × **1.40**, bearing +**25°**; target height/speed/heading/gamma distributions unchanged |
| **M1** | `target_policy = weaving` |
| **M2** | `target_policy = break_turn` |
| **C1** | after reset, identify the blue-blue pair with the largest horizontal distance; hard-prune BOTH directions of that pair for the whole episode |
| **C2** | same longest pair; prune ONLY the direction lower-y endpoint → higher-y endpoint |
| **J1** | **G1 + M1 + C1** composed; NO additional scalar dropout/delay/range stress |

- M1/M2 are real, already-implemented maneuver families; formal runs use `straight`.
- C1/C2 act on the communication-adjacency formation process (topology shift), NOT on
  range/dropout/delay scalars — distinct from robustness R01–R09.

## 2. Frozen evaluation parameters

```
eval_base_seed   = 1208607
episodes         = 100 / (method × train-seed × cell)
failed_agent     = relay (1)
failure_start    = 25
failure_duration = 80
horizon          = 260
primary          = RMST(80)
full-window      = RMST(220)
exposure gate    = >= 0.99 (hard; 84/84 primary cells must pass)
```

## 3. Primary cells (preflight gate)

4 methods (EA-RG Full, MAPPO, HAPPO, Wider Single-Graph) × 3 training seeds × 7 cells
= **84 cells** must all pass exposure_rate >= 0.99. Any failure => STOP (no performance
viewing); archive the failed preflight, revise the OOD rule, new protocol version, re-freeze,
re-preflight.

## 4. Code-level single source

- `scripts/p3a_ood_cells.py` is the single code-level definition of the 7 cells.
- Env eval-side extensions are default no-op: `blue_init_rotation_deg`,
  `blue_init_spacing_scale`, `target_init_range_scale`, `target_init_bearing_offset_deg`,
  `comm_topology_mode`; default behavior of training / held-out / robustness is unchanged.
- MAPPO (graph_encoder=no_graph CTDE) reuses the RI 3DOF evaluator with frozen checkpoints;
  HAPPO uses its own evaluator but the same `make_env`, so all four methods see the same
  OOD config.
- `scripts/run_p3a_ood_preflight.py` outputs ONLY exposure fields (method, train_seed, cell,
  episodes, failure_start, exposed_count, exposure_rate, threshold, pass, base_seed,
  checkpoint, checkpoint_sha256, frozen cell config). It NEVER outputs success / recovery /
  t_rec / RMST / reward / rankings.

## 5. Deliverables

- `docs/statistics/p3a_ood_protocol_v1_1.md` (this file)
- `scripts/p3a_ood_cells.py`, `scripts/run_p3a_ood_preflight.py`
- env/config extension (default no-op) + RI/HAPPO evaluator pass-through
- `tests/test_p3a_ood_eval_config.py` (5/5 targeted + smoke)
- preflight output: `docs/statistics/p3a_ood_results_v1_0/p3a_preflight_exposure.csv`
- after PASS: proceed to P3-A.3; final results tag `p3a-ood-results-lock-v1.0`.
