# Phase 2I-A4 cloud training

This package is for `DEVELOPMENT_ONLY` training. It does not contain local results or checkpoints.

## On the AutoDL server

```bash
unzip EA-RG-MAPPO_PHASE2IA4_CLOUD.zip -d /root/ri_gmappo_uav
cd /root/ri_gmappo_uav
python -m pip install -r requirements.txt
chmod +x scripts/launch_phase2ia4_development.sh
CUDA_VISIBLE_DEVICES=0 PYTHON_BIN=python DEVICE=cuda nohup bash scripts/launch_phase2ia4_development.sh > phase2ia4.out 2> phase2ia4.err &
echo $! > phase2ia4.pid
```

The launcher keeps the frozen protocol (`num_envs=4`, `rollout_steps=64`) and uses CPU environment parallelism plus CUDA. It runs the six fixed runs sequentially to avoid GPU-memory contention and protocol drift. After all six runs complete successfully, it executes `shutdown -h now`. To disable automatic shutdown, set `AUTO_SHUTDOWN=0` before launching. A failed run exits before shutdown and preserves the error log.

The launcher performs exactly six fresh runs: `full_gate`/`no_role_gate` × seeds `101/202/303`, each with 3907 updates and 1,000,192 environment steps. It refuses to overwrite an existing run directory and never resumes.

## Monitor without inspecting performance

```bash
tail -f phase2ia4.out phase2ia4.err
for f in results/development/role_gate_phase2ia4/runs/*/*/train_log.csv; do echo -n "$f "; tail -n 1 "$f"; done
nvidia-smi
```

## After all six runs finish

Do not run validation until all six final checkpoints and logs exist. Copy the results directory back to the project machine, then run the fixed final-checkpoint validation locally or on the server:

```bash
python scripts/run_phase2ia4_validation.py --device cuda
```

The validation outputs are `DEVELOPMENT_ONLY`. V0 risk-set adequacy must be evaluated before any Role-Gate retention decision.
