# P3-A Formal Exposure Preflight Audit Memo (v1.1 lock)

- date: 2026-08-08
- protocol tag: `p3a-ood-protocol-v1.1` (commit `c5e8aab`)
- implementation tag: `p3a-ood-eval-impl-v1.1.3` (commit `9608ad7`)
- run: formal exposure-only preflight, GPU batch=8, worktree `p3a_preflight_v1_1_3`
- command: `run_p3a_ood_preflight.py --held-out-root docs/statistics/p3a_ood_results_v1_1 --device cuda --eval-batch-size 8`

## Mechanical audit (final hard gate)

| check | result |
|---|---|
| expected cells | 84 |
| observed cells | 84 |
| unique cells | 84 |
| PASS cells | 84 |
| FAIL cells | 0 |
| episodes / cell | 100 |
| min exposure rate | 1.0000 |
| exposure >= 0.99 | 84/84 |
| missing cells | 0 |
| duplicate cells | 0 |
| runtime error | 0 |
| checkpoint SHA match | 12/12 |
| method x seed -> 7 cells | OK (12 x 7 = 84) |

## Checkpoint / loader provenance (identical to formal held-out)

| method | seeds (update) | agent | load signature |
|---|---|---|---|
| full_ea_rg | 700 / 900 / 977 | RIGMAPPOAgent | 74 / 0 / 0 |
| mappo | 600 / 900 / 100 | MAPPOAgent3D STRICT | 12 / 0 / 0 |
| happo | 300 / 977 / 800 | HAPPOBaselineAgent | 84 / 0 / 0 |
| param_matched_single | 500 / 200 / 900 | RIGMAPPOAgent (single) | 34 / 0 / 0 |

- SHA256: 12/12 match copied frozen held-out manifest (`held_out_split_manifest.csv`).
- All partial = 0, skipped = 0. MAPPO uses strict state_dict load.

## Boundaries

- OOD cells: G1 G2 M1 M2 C1 C2 J1 (protocol v1.1 definitions unchanged).
- failure onset = 25, duration = 80, horizon = 260, exposure gate >= 0.99.
- Only exposure endpoints were recorded. No success / recovery / t_rec / RMST /
  reward / method-ranking endpoint was inspected or stored.

## Verdict

> VERDICT: PASS
> 84/84 primary cells satisfy exposure >= 0.99.
> No OOD performance endpoint was inspected before this lock.
> P3-A.3 formal zero-shot evaluation is authorized.
