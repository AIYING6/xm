# B-line P0 execution report

**Verdict:** `B_P0_CONDITIONAL`.

## Counterexample definition

P0 fixes the current UAV geometry, current communication graph, and remaining mission demand. In both cases the scout–relay edge is connected and the relay–terminal edge is disconnected. The candidate decisions are exactly `continue_mission` and `reconfigure_relay`; their ordering is fixed as hard continuity feasibility, mission completion, reconfiguration count, path cost, then action identifier.

The histories differ only in current consecutive outage duration:

| Paired case | Legal history summary | Current outage duration | Preferred decision |
| --- | --- | ---: | --- |
| Newly disconnected | connected → disconnected | 1 | `continue_mission` |
| Persistent disconnected | connected → disconnected → disconnected → disconnected | 3 | `reconfigure_relay` |

The current snapshot hash is identical in both cases: `7f5640f258e44086bfb926a9f61c21872a705b7c18977962309a1d826ccaebf5`.

## Why transition history matters here

Under the frozen continuity contract, at most three consecutive disconnected slots are allowed. Continuing after the newly disconnected state yields duration two and remains feasible; reconfiguration is therefore dominated by completing the outstanding mission. Continuing after the persistent state yields duration four and is infeasible; relay reconfiguration is then required.

Consequently, a deterministic snapshot-only rule cannot be both feasible and preferred in the two paired cases: always continue violates the persistent-outage constraint, while always reconfigure is dominated in the new-outage case.

## Deterministic execution

The CPU-only script executed with zero environment steps, zero PPO updates, no checkpoint, and no evaluation tape. Its result files are in `p0-execution/`:

- Result JSON SHA-256: `d41412086fa6e97953d325e56e9aaad48fd51039bf9811a31326033f88544a71`.
- Decision ledger SHA-256: `151f88e0e509e1e6828170424a1535c3e9883a406f0e07d4e1e36d223d0c0d29`.
- Report SHA-256: `1d6f3af6504848a8186e58e41872ee1a953c0a23c6e1c5e060f70606b8baf52a`.

The test suite regenerates the artifacts in two independent temporary directories and requires byte-identical hashes.

## Why this is conditional, not a solver GO

The counterexample establishes a real decision distinction **if** the eventual target system legitimately has an outage-duration continuity limit and can expose that duration without violating its information boundary. P0 did not audit whether the present 3D/6-UAV environments encode that semantics, whether physical relay motion can restore the route within the assumed slot, or whether the constraint belongs to the intended deployment task.

## Next allowed step

Only a zero-training semantic feasibility audit is allowed: verify or reject the outage-duration/recovery semantics against the target environment and deployment contract. No solver implementation, benchmark, training, or P1 formal-problem freeze is authorized by this conditional result.
