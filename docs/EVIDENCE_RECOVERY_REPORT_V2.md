# Evidence Recovery Report v2

Generated: 2026-08-12

## Search scope

- Current workspace and sibling project worktrees;
- Git branches, tags, reachable history, and Git LFS metadata;
- historical results, configs, logs, manifests, checkpoint inventories, and checkpoint paths.

## Recovered archival evidence

| Evidence | Source/location | Status | Evaluation use |
|---|---|---|---|
| 5-seed formal test episode CSV | Git `e02a753`, `archival/provenance/legacy_e02a753/results/intercept_3d_gate1_hardened_safety_5seed_formal_candidate/checkpoint_sweep_fixed_update60_test/` | Git objects recoverable; SHA retained in Git | Raw descriptive analysis; strict fields incomplete |
| 5-seed per-seed test CSVs | Git `e02a753`, same formal directory | Recoverable | Raw descriptive analysis; checkpoint bytes missing |
| Formal protocol | Git `e02a753`, `.../protocol.md` | Recoverable | Protocol provenance |
| Validation summaries and selected-checkpoint CSVs | Git `e02a753`, `.../checkpoint_sweep*` | Recoverable | Selection provenance |
| Training logs | Git `e02a753`, `.../runs/{multi_relation,no_graph,single}/bc_ppo_seed*/` | Recoverable | Diagnostics, not model restoration |
| Historical survival v1.1 package | Git `e02a753`, `.../docs/statistics/survival_*` | Recoverable | Legacy reference only |
| Historical OOD/robustness CSVs | Git `e02a753`, matching `results/` paths | Recoverable candidates | Each requires protocol binding |

## Checkpoint search result

- Current working tree: no `.pt`, `.pth`, `.ckpt`, model archive, or Git LFS pointer.
- Archival worktree at `e02a753`: no `.pt`, `.pth`, or `.ckpt` files.
- `git lfs ls-files`: no entries.
- CSV checkpoint fields point to historical paths such as `actor_critic_update_0060.pt`, but the referenced bytes are absent from reachable Git objects.
- Existing external sibling worktrees were inspected; no project checkpoint bytes were found.

## Provenance findings

1. The 5-seed formal raw data and selection artifacts are recoverable.
2. The formal package documents 5 seeds and 100 test episodes per cell, while the historical survival package documents a separate 3-seed, 10,800-episode package. They must remain separate until a manifest proves identity.
3. No recovered artifact is sufficient for frozen re-evaluation because checkpoint bytes are missing.
4. No archival file has been copied into canonical `results/`; the archival worktree is evidence storage only.

## Remaining missing evidence

- selected checkpoint bytes and SHA256 hashes;
- richer episode fields required by `RECOVERY_ENDPOINT_PROTOCOL_V2.md`;
- explicit mapping between the 3-seed survival package and raw episode source;
- complete OOD/robustness raw provenance with checkpoint identity;
- canonical baseline identity manifest.

## Decision

Historical results can be inspected and audited. Frozen re-evaluation is blocked until checkpoint bytes are recovered from an external backup or artifact store. Any future retraining must be labeled new confirmatory training and must not silently replace historical results.
