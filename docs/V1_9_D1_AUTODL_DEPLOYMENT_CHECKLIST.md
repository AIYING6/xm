# v1.9 D1 AutoDL Deployment Checklist

**Status: ready for an explicitly authorized cloud launch; no instance has
been created and no D1 training has started.**

## Why D1 is not launched locally

The local machine exposes CUDA but has a 4 GB GTX 1650 Ti. The in-progress
v1.8 repair matrix is also consuming local CPU for environment rollouts. D1
requires 8 environments and a realistic GPU memory/throughput audit; launching
it locally would contend with v1.8 and would not measure the intended cloud
deployment capacity. It is therefore deferred to a dedicated GPU instance.

## Instance requirement

- one NVIDIA GPU with at least 16 GB VRAM (24 GB preferred);
- at least 16 vCPU and 64 GB RAM, because the simulator rollout is CPU-heavy;
- at least 100 GB working disk for source, immutable checkpoints, event
  records, and logs;
- CUDA-compatible PyTorch installation; Python 3.10+ recommended;
- a persistent output location plus an off-instance backup destination.

## Pre-launch procedure on AutoDL

1. Create the instance and copy its SSH login command. Do not send a password
   or private key in chat.
2. Obtain the fixed repository commit and install the project dependencies in
   an isolated environment.
3. Run, in order:

```bash
python scripts/check_gpu_runtime_v1_9.py \
  --output results/v1_9_d1_engineering/runtime_manifest.json
python scripts/test_actor_boundary_v1_8.py
python scripts/test_pcrf_d0_v1_9.py
```

4. Review the written CUDA manifest, then run the prepared serial launcher:

```bash
bash scripts/run_v1_9_d1_autodl.sh
```

5. After the four runs finish, run:

```bash
python scripts/check_v1_9_d1_artifacts.py --root results/v1_9_d1_engineering
```

6. Back up the entire `results/v1_9_d1_engineering` directory, including the
runtime manifest, every snapshot, validation CSV, summary, hash manifest, and
stdout/stderr logs, before releasing the instance.

## Do not do

- do not run the launcher beside an active local formal matrix;
- do not change the D1 command after any pilot curve is seen;
- do not use a D1 checkpoint for held-out, OOD, or paper results;
- do not start v1.9 formal training from this launcher.
