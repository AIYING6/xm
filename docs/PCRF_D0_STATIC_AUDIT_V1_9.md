# PCRF D0 Static Audit v1.9

**Status: PASS for static design gates only.** No PCRF training, validation,
held-out evaluation, OOD evaluation, or performance comparison was run.

## Scope

This audit implements the candidate **Provenance-Conditioned Relation
Factorization (PCRF)** encoder introduced in
[V1_9_Q1_RECONSTRUCTION_PLAN.md](V1_9_Q1_RECONSTRUCTION_PLAN.md). The encoder
has three legal relation channels and a receiver-local fusion gate. Its gate
sees only:

- already provenance-masked relation rows;
- relation overlap/disagreement;
- delivered communication age and confidence.

It has no union residual channel and no static Role-Pair gate. It therefore
does not add simulator-global state, pending packet payload, unavailable
teammate state, or critic state to the actor.

## Static test results

Command:

```text
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/test_pcrf_d0_v1_9.py
```

| Test | Result | What it establishes |
|---|---|---|
| relation agreement has neutral gate | PASS | Equal legal relation evidence produces a uniform three-factor gate at initialization. |
| relation conflict changes gate | PASS | A communication-only legal relation changes the gate; stale legal packet age reduces its communication weight. |
| conflict gate receives gradient | PASS | The learnable correction path has nonzero gradient on a fixed conflict batch. |
| unavailable teammate truth remains hidden | PASS | Changing an undelivered sender’s simulator state leaves the recipient graph and PCRF actor output unchanged. |
| capacity matching | PASS | PCRF actor with hidden width 128 has 196,856 parameters; a single-graph actor with hidden width 168 has 195,837 parameters (0.52% gap). |

The existing actor-boundary suite was re-run after the implementation and
passed 14/14.

## Interpretation boundary

These tests establish that the candidate mechanism is structurally
identifiable and uses no new actor information. They do **not** establish that
PCRF improves RMST, establishment probability, learning stability, nominal
performance, or OOD robustness.

## D0 decision

`D0_STATIC_GATES_PASS`.

The design may proceed to a non-formal D1 engineering-feasibility pilot only
after author authorization. D1 must use fresh engineering seeds, a short fixed
budget, the PCRF-128 vs single-168 capacity pairing, R5-style boundary checks,
and no confirmatory/held-out episode. A D1 result cannot be used as formal
evidence or to tune the architecture after observing performance.
