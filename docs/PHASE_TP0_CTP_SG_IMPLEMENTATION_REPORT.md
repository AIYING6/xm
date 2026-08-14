# Phase TP-0 — CTP-SG Implementation and Technical Verification Report

## Decision

**TP-0 PASS.** `PHASE_TP0_CTP_SG_READY` is authorized as an implementation-readiness tag only.

**TP-1 is not started and remains separately unauthorized.** The only training execution in TP-0 was a one-update CPU smoke test; no long training, schedule selection, tuning result, or paper-level result was produced.

## Required 19-item completion response

1. **Implementation commit SHA:** `e4911f76d5f1e17e44329790a2f70aa3801195cf`.
2. **Branch:** `codex/relation-aware-single-graph-v1`.
3. **SG architecture unchanged:** PASS. CTP uses the same `graph_encoder="single"`, hidden size `115`, role/intent dimensions, PPO path, and actor/critic implementation as the frozen matched Single-Graph.
4. **Trainable parameter count — frozen SG:** `116,728`.
5. **Trainable parameter count — CTP-SG:** `116,728`.
6. **No new trainable parameters:** PASS. State-dict keys and trainable parameter counts are identical; TP adds only deterministic condition sampling and logging.
7. **Curriculum scheduler tests:** PASS. Schedules A/B/C are present exactly; all probability rows sum to one; empirical sampling at the middle phase agrees within 0.03; Ftrain contains eight pairs and excludes `(44,80)`.
8. **Failure-semantics regression:** PASS. F0 remains exactly relay `1`, onset `44`, duration `80`; Ftrain changes only the frozen onset/duration fields and preserves the existing `_is_comm_failed` timing semantics.
9. **Actor information boundary:** PASS. Existing `tests/test_phase2h_information_boundary.py`: 3 tests passed.
10. **Graph legality:** PASS. Existing S2 receiver/sender orientation, failure edge pruning, self-edge, and task-support legality verifier passed.
11. **Deterministic scheduler replay:** PASS. Same seed/update/environment/episode tuple reproduces the same condition and Ftrain pair; logging is not an input to sampling.
12. **1-update smoke:** PASS. SG + Schedule A, two environments, eight rollout steps, one update; checkpoint save/reload, manifest, curriculum log, and train log all verified. This is an engineering smoke only.
13. **Tuning seeds:** `1601, 1602`.
14. **Held-out confirmation seeds:** `1701, 1702, 1703`.
15. **Tuning tape:** paired episode IDs `350000–350049`.
16. **Confirmation tape:** paired episode IDs `360000–360099`.
17. **Exact 300,032-step tuning command:**

```bash
python scripts/train_ri_gmappo.py \
  --env-name 3d_intercept --seed 1601 --num-envs 4 --rollout-steps 64 --updates 1172 \
  --hidden-dim 115 --graph-encoder single --role-gate-mode none \
  --target-policy straight --strict-target-sensing --agent-target-info-bottleneck \
  --relay-dependent-task --business-grounded-geometry \
  --communication-range-scale 1.0 --communication-dropout-prob 0.0 \
  --message-delay-steps 0 --radar-dropout-prob 0.0 \
  --min-success-step 260 --failed-blue-agent 1 \
  --node-failure-start-step 44 --node-failure-duration-steps 80 \
  --disable-evaluation --save-interval 1172 --device cuda \
  --out-dir results/phase_tp1/sg_seed1601
```

The matched SG command is repeated for seed `1602`. The CTP command uses the same command and adds:

```bash
--topology-curriculum-schedule A --topology-curriculum-seed 1601 --topology-curriculum-logging
```

with `--out-dir results/phase_tp1/ctp_A_seed1601`; the second CTP tuning seed is `1602`. The step count is fixed by `4 × 64 × 1172 = 300,032`.

18. **Exact 500,224-step confirmation command:** TP-2 is not authorized. After TP-1 freezes exactly one schedule, the fixed command is the following, with the already-frozen schedule substituted once and never tuned during confirmation:

```bash
python scripts/train_ri_gmappo.py \
  --env-name 3d_intercept --seed 1701 --num-envs 4 --rollout-steps 64 --updates 1954 \
  --hidden-dim 115 --graph-encoder single --role-gate-mode none \
  --target-policy straight --strict-target-sensing --agent-target-info-bottleneck \
  --relay-dependent-task --business-grounded-geometry \
  --communication-range-scale 1.0 --communication-dropout-prob 0.0 \
  --message-delay-steps 0 --radar-dropout-prob 0.0 \
  --min-success-step 260 --failed-blue-agent 1 \
  --node-failure-start-step 44 --node-failure-duration-steps 80 \
  --disable-evaluation --save-interval 1954 --device cuda \
  --topology-curriculum-schedule <TP1_FROZEN_SCHEDULE> \
  --topology-curriculum-seed 1701 --topology-curriculum-logging \
  --out-dir results/phase_tp2/ctp_seed1701
```

The confirmation schedule token is intentionally unresolved until TP-1 selection; this command is not an authorization to run TP-2. The matched-SG confirmation command omits the curriculum flags and is repeated for seeds `1701,1702,1703`.

19. **Canonical seeds `0–4`:** untouched. No canonical seed, canonical result, canonical tape, or formal headline result was used.

## Implementation boundary audit

The TP sampler changes only training-time values of the existing environment fields `failed_blue_agent`, `node_failure_start_step`, and `node_failure_duration_steps`. It does not modify geometry, communication radius, reward, terminal rules, target behavior, sensing, graph construction, actor inputs, or evaluation code. F0 is identical to the frozen S2 condition. Ftrain is sampled uniformly from the pre-frozen Cartesian pool excluding the canonical `(44,80)` pair.

The Schedule A hash recorded by the smoke manifest is:

```text
2549a3fea99e5f6f60c98ad90daaae52bbd00ebd45e70d03caea9e95475f610b
```

Machine-readable TP-0 output:

`results/development/phase_tp0_ctp_sg_technical_verification_v3.json`

No TP-1 schedule has been selected. No performance conclusion is permitted from TP-0.
