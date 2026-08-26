# EGTR P3 云端启动说明

## 固定范围

- UTR-SG / DRTP-SG / EGTR-DRTP-SG；
- seeds `2501, 2502, 2503`；
- 每路 `3,907 updates = 1,000,192 env steps`；
- tape `520000–520099`；
- 只启动 1M；本 launcher 不自动评估、不自动续训 3M、不自动关机；
- 不使用 held-out 或 canonical seeds。

## 解压与启动

```bash
cd /root/autodl-tmp
mkdir -p /root/autodl-tmp/EA-RG-MAPPO_EGTR_P3_DEVELOPMENT
unzip -q EA-RG-MAPPO_EGTR_P3_DEVELOPMENT_c3bb329.zip \
  -d /root/autodl-tmp/EA-RG-MAPPO_EGTR_P3_DEVELOPMENT
cd EA-RG-MAPPO_EGTR_P3_DEVELOPMENT

screen -dmS egtr_p3 bash -lc '
set -e
cd /root/autodl-tmp/EA-RG-MAPPO_EGTR_P3_DEVELOPMENT
PYTHON_BIN=python MAX_PARALLEL=6 CPU_THREADS_TOTAL=16 \
  bash scripts/launch_egtr_p3_development_autodl.sh
'
screen -ls
```

`MAX_PARALLEL=6` 只控制并发调度，不改变实验合同。若云端 CPU/GPU 资源充足，可在启动前显式改为 `9`，但不建议在显存紧张时盲目提高并发。

## 进度检查

```bash
cd /root/autodl-tmp/EA-RG-MAPPO_EGTR_P3_DEVELOPMENT
for arm in utr_sg drtp_sg egtr_sg; do
  for seed in 2501 2502 2503; do
    f="results/development/egtr_p3/runs/${arm}/seed${seed}/train_log.csv"
    if [ -s "$f" ]; then
      u=$(tail -n 1 "$f" | cut -d, -f1)
      awk -v a="$arm" -v s="$seed" -v u="$u" \
        'BEGIN{printf "%s seed%s: %d/3907 (%.2f%%)\\n",a,s,u,100*u/3907}'
    else
      echo "$arm seed$seed: 尚未开始"
    fi
  done
done
nvidia-smi
```

训练完成后只检查 9 个 run 的 `run_manifest.json`、final checkpoint、milestone checkpoint 和 runtime-state；评估与 3M continuation 必须等待单独授权。
