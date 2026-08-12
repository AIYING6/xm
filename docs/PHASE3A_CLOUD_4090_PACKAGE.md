# Phase 3A cloud 4090 package

Local Wave 1 was stopped at the user’s request and recorded in `results/canonical_v2/manifests/wave1/run_incident_log.csv`. Existing artifacts are preserved; no artifact was deleted.

The cloud launcher is `scripts/cloud/run_phase3a_wave1_4090.sh`. It uses the RTX 4090 through CUDA, runs Full and MAPPO jobs with bounded concurrency, and keeps the frozen scientific training values: `num_envs=4`, `rollout_steps=64`, `updates=3907`, seeds `0..4`, and the fixed Phase 3A failure/communication protocol. `RUN_CONCURRENCY` controls hardware scheduling only; it does not alter the protocol.

Before launch on the cloud server:

```bash
python -m pip install -r requirements.txt
nvidia-smi
CUDA_VISIBLE_DEVICES=0 RUN_CONCURRENCY=2 bash scripts/cloud/run_phase3a_wave1_4090.sh
```

The package includes code, configs, protocol documents, smoke evidence, launch manifests, and the incomplete local Wave 1 artifacts. The incomplete artifacts are not complete formal evidence and must be labeled with the recorded incident. If resuming from a partial checkpoint, create a new incident entry with the exact checkpoint SHA256 and update offset; do not relabel it as a fresh complete run.
