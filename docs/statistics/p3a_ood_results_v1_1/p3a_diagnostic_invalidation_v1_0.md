# P3-A Diagnostic Run Invalidation Memo (2026-08-07)

- status: **INVALID / DIAGNOSTIC ONLY — no scientific result may be derived.**
- run: `run_p3a_ood_preflight.py` background run, started on `28b4836`-era code
  (impl before `p3a-ood-eval-impl-v1.1.2`), stopped at 28/84 cells by operator.
- log tail kept at repository root: `_tmp_p3a_preflight.txt`, `_tmp_p3a_preflight_err.txt`.

## Reason (both are P3-A.2 implementation failures, NOT protocol failures)

1. **Seed-dependent checkpoint selection mismatch.**
   The preflight `_CHECKPOINT_TMPL` pinned a single update for all seeds
   (full=0700, happo=0300, mappo=0600, wider=0500), whereas the frozen
   held-out manifest (`held_out_split_manifest.csv`) validation-selects a
   per-seed update (e.g. full s1=0900, s2=0977). Seeds 1/2 therefore loaded
   different checkpoint files (different SHA256) than the formal held-out assets.
2. **MAPPO policy architecture / loader mismatch.**
   MAPPO was routed through `evaluate_ri_gmappo_3d.build_agent`
   (RIGMAPPOAgent + `load_matching_state_dict`), producing
   `5 matching + 1 partial + 6 skipped`. The formal held-out evaluation uses
   `MAPPOAgent3D` + STRICT state_dict load (12/12, 0 partial, 0 skipped).
3. (Also found during Gate-3 audit) Wider Single-Graph
   (`param_matched_single`) was built with `graph_encoder="multi_relation"`
   instead of the held-out `single` encoder (34/0/0 -> 24/0/10 until fixed in
   v1.1.2).

## Boundary

- G/M/C/J cell definitions, failure onset (25), duration (80), horizon (260),
  exposure gate (>=0.99), and the frozen protocol parameters were NOT changed.
- No OOD performance endpoint (success / recovery / t_rec / RMST / reward /
  ranking) was inspected by this run.

## Consequence

- This run is NOT an exposure lock and cannot contribute to any P3-A result.
- All 28 completed cells are void. The formal 84-cell exposure preflight is
  re-run from the clean `p3a-ood-eval-impl-v1.1.2` worktree after the Gate-3
  asset/load audit passes 12/12.
