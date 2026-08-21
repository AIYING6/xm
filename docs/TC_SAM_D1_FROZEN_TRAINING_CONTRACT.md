# TC-SAM-D1 Frozen Training Contract

## Authority and source

- D0 technical decision: `A — TC_SAM_TECHNICAL_GO`.
- Source commit: `a7acf84`.
- Comparator provenance: `results/development/t1_telemetry_native_reference_1m_run1`.
- T1 protocol: `T1-TELEMETRY-NATIVE-UTR-SG-TRAINING-V1`.

## Paired development trajectories

TC-SAM trains from scratch only on frozen T1 development seeds **2201, 2202,
2203, 2204, 2205**. Every trajectory uses 4 environments × 64 rollout steps ×
3907 updates = **1,000,192 environment steps**, runtime persistence from update
zero, final checkpoint only, no resume, no early stop, no seed exclusion, and
no checkpoint promotion.

UTR is not retrained if the five existing T1 run manifests pass exact-contract
provenance verification. The paired reference is `UTR(seed_i)` for the same
`seed_i`.

## Only allowed difference

TC-SAM keeps the matched single graph model (116,728 parameters), PPO,
environment, reward, legal actor inputs, failure semantics, fixed 50% nominal
anchor, and conditional-uniform six failure groups. It changes only the actor
optimizer update to standard Euclidean SAM:

`sam_enabled=True; sam_rho=0.05; sam_epsilon=1e-12; actor_gradient_mode="utr"`.

The critic remains ordinary PPO. No change of rho, scope, learning rate,
clipping, entropy, topology exposure, architecture, reward, or seed is
permitted after launch.

## Evaluation and decision

Final checkpoints will use the frozen T1-compatible development tape
(`920000–920099`, hash `3de6e4fabf07bb76fe7c9271b3f3e70a5910262581ac14b3de162533ef83e6c3`).
Per seed, report `J_nominal`, `J_F0`, `Delta_J`, `J_OOD_mean`, `J_OOD_worst`,
timeout, collision, and constraint violation, then compare TC-SAM and UTR by
paired training seed. The final result is limited to `TC_SAM_DEV_PASS`,
`TC_SAM_DEV_MIXED`, or `TC_SAM_DEV_FAIL`; it never automatically starts 2M,
held-out, canonical, or another SAM variant.
