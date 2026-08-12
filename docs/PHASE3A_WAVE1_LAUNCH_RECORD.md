# Phase 3A Wave 1 launch record

**Launch status:** authorized after B1 timing amendment and smoke PASS  
**Scientific status:** formal results are not yet available; no result has been inspected  
**Methods:** `EA-RG-MAPPO-S` and `MAPPO`  
**Seeds:** exactly `0, 1, 2, 3, 4` per method  
**Budget:** `num_envs=4`, `rollout_steps=64`, `updates=3907` (`B_star`, approximately 1M environment steps)  
**Selection:** validation-only; test evaluation occurs only after selected checkpoints are frozen and hashed

All runs use the frozen 3DOF straight-target, strict sensing, target bottleneck, dropout 0.30, delay 2, relay failure at step 40 for 80 steps protocol. The two method identities differ only in graph encoder: `multi_relation` for Full and `no_graph` for MAPPO.

The command-level manifest and process logs are stored under `results/canonical_v2/manifests/wave1/`. Every restart must be recorded in `run_incident_log.csv`; disappointing metrics are not a restart reason.

This record was written before inspecting any Wave 1 formal result. No endpoint, tau, seed set, failure protocol, training budget, or checkpoint selection rule may be changed after launch.
