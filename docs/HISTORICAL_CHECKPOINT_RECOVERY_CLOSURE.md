# Historical checkpoint recovery closure

**Status:** CLOSED — archival candidates recovered; historical reproduction remains non-canonical.

## Scope and stopping rule

The final bounded search covered the current repository, sibling project worktrees, the historical `e02a753` worktree, Downloads, OneDrive, Documents, Desktop, and the project-related Codex artifact archives. It also checked Git history/LFS and source archives for embedded checkpoint files. No further search is authorized for Phase 2G.

## Recovered archival candidates

The following checkpoint bytes were found outside the repository:

| Candidate family | Seeds | Update | Bytes per file | Binding status |
|---|---:|---:|---:|---|
| `param_matched_single_graph_5seed_bottleneck_strict_update60_formal_candidate` | 0–4 | 60 | 1,590,846 | archival candidate; config/episode-level strict endpoint binding incomplete |
| `true_no_role_identity_hardened_5seed_strict_update60_formal_candidate` | 0–4 | 60 | 1,591,534 | archival candidate; config/episode-level strict endpoint binding incomplete |

The source root is:

`C:\Users\96251\Documents\Codex\2026-07-12\ni\artifacts_archive\cleanup_20260802\results`

The per-file SHA256 inventory is recorded in `archival/provenance/recovered_checkpoint_candidates_v2.csv`. The bytes are not copied into `results/canonical_v2/checkpoints/`; this keeps historical artifacts separate from future canonical evidence.

## Scientific disposition

These files are not silently promoted to historical reproduction because the recovered candidate directories do not include a complete, independently auditable package tying each selected checkpoint to the frozen v2 endpoint schema, evaluation protocol, raw episode rows, and canonical baseline identity. They may support a later frozen re-evaluation only after an explicit provenance review binds all of those objects.

The historical 5-seed Gate-1 results therefore remain **legacy descriptive evidence**, not canonical confirmatory evidence. The historical 3-seed/10,800-episode survival package remains **legacy survival evidence** and is not a v2 strict-endpoint result. Future confirmatory runs, if authorized after all gates pass, are new canonical experiments rather than reproductions of those historical claims.

## Closure statement

Historical selected checkpoint bytes are not unrecoverable in the broad filesystem sense: archival candidate bytes were found. However, the historical selected checkpoint **evidence packages** are not fully recoverable as canonical v2 evidence. Historical result reproduction remains unresolved and retired from canonical use.
