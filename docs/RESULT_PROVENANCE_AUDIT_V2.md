# Result Provenance Audit v2 (Phase 1)

Status: **NO-GO for final evidence release**

Frozen baseline: `upgrade-baseline-20260812` / commit `4122f6d`.

## Current retained inventory

| Artifact class | Current state | Audit judgment |
|---|---|---|
| Source/configs | Present; 8 paper configs and active algorithms/envs/scripts | Usable after code audit |
| Current episode-level raw CSV | `results/gate1_safety_fx60_failure_timing_generalization_formal_merged/test_episode_metrics.csv`, 3000 rows, 5 training seeds × 3 graph variants × 2 scenarios × 100 episodes | Useful raw data, but missing strict pre-establishment field |
| Current final summary CSV | `results/final_comm_300_eval.csv` and related summaries | Derived/terminal summaries only; not sufficient for survival re-analysis |
| Old survival outputs | Removed from current tree but recoverable from Git history (`e02a753`) | Legacy only until v2 validation |
| Checkpoint files | No `.pt`, `.pth`, `.ckpt`, or archive files in current tree | **Blocker** |
| Checkpoint paths in CSV | Point to historical `results/.../actor_critic_update_0060.pt` paths | Path provenance exists; file provenance does not |
| Raw episode provenance | Current CSV has seed, episode, scenario, checkpoint update, and protocol fields | Partial; checkpoint bytes and strict endpoint derivation unavailable |
| Derived statistics | Existing tables/figures/reports are present | Must be regenerated after endpoint/statistics audit |
| SHA manifest | Current manifest covers retained artifacts | It cannot certify missing checkpoint bytes or deleted raw sources |

## Claim-to-evidence disposition

| Evidence type | Can directly reuse? | Action |
|---|---|---|
| Terminal success/collision summaries | Yes, descriptively | Recompute from retained raw/summary CSV and verify labels |
| Legacy post-failure closure rate | Yes, with downgraded naming | Call it post-failure chain establishment/closure until strict fields are restored |
| Strict recovery cohort | No | Recover richer raw episode CSV or perform frozen re-evaluation |
| Legacy RMST/KM | No as canonical result | Recompute with v2 after endpoint and reference validation |
| OOD summaries | Partially | Audit raw OOD episode files and checkpoint mapping before reuse |
| Mechanism figures | Partially | Verify source CSV and method identity; do not infer causality from aggregate curves |
| Training-seed confirmatory evidence | Partially | Current 5-seed Gate-1 raw CSV exists, but checkpoint bodies are absent |

## Git-history recovery opportunity

The pre-cleanup history contains multiple raw episode CSVs and the historical survival v1.1 outputs. These can be selectively restored into an archival/provenance area without retraining. They must not be silently mixed into the current release or treated as current canonical data until their protocol and headers are checked.

## Blockers

1. Missing checkpoint bytes.
2. Strict recovery endpoint fields absent from the retained 3000-row CSV.
3. Current manuscript claims 10,800 episodes and three seeds, while the retained Gate-1 CSV documents 3,000 episodes and five seeds for three variants/two scenarios.
4. Historical survival implementation has known censor-risk-set and tau-specific observed-delta defects.

No result files were overwritten by this audit.
