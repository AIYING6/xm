# P3-A Diagnostic Audit Summary (2026-08-07)

- implementation tag: `p3a-ood-eval-impl-v1.1.3`
- implementation SHA: `9608ad7`
- protocol tag: `p3a-ood-protocol-v1.1` (`c5e8aab`)
- run: exposure-only diagnostic, GPU, batch=8, worktree `p3a_preflight_v1_1_3`
- PID 21112, exit code 0

## Audit (8 items)

1. process finished normally ............ PASS
2. observed unique cells = 84 ........... PASS
3. missing = 0 .......................... PASS
4. duplicate = 0 ........................ PASS
5. runtime error = 0 .................... PASS
6. Gate 3 checkpoint audit = 12/12 ...... PASS
7. exposure PASS = 84/84 ................ PASS
8. every cell exposure >= 0.99 .......... PASS (all cells = 1.0000)

## Load-signature provenance (identical to formal held-out)

- full_ea_rg:       RIGMAPPOAgent 74/0/0, updates 700/900/977
- mappo:            MAPPOAgent3D STRICT 12/0/0, updates 600/900/100
- happo:            HAPPOBaselineAgent 84/0/0, updates 300/977/800
- param_matched_single: RIGMAPPOAgent (single encoder) 34/0/0, updates 500/200/900
- SHA256: 12/12 match copied frozen held-out manifest

## Exposure

- 84/84 cells, episodes=100 each, exposure_rate = 1.0000 everywhere.
- No performance endpoint (success / recovery / t_rec / RMST / reward / ranking)
  was inspected or recorded.

## Verdict

> DIAGNOSTIC PASS.
> Gate 3 12/12, 84/84 exposure >= 0.99, no runtime error, no duplicate/missing cell.
> Formal exposure-only preflight is authorized from the same v1.1.3 worktree.
