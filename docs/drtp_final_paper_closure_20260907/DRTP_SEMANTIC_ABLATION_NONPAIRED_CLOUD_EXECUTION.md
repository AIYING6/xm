# DRTP 非配对机制消融：云端执行说明

## 冻结设计

本包只训练 10 条全新轨迹：

| 方法 | seeds | 是否新训练 | 目的 |
|---|---|---:|---|
| Fixed-DRTP | 80011–80015 | 是 | 检验连续 adaptive update 是否提供额外价值 |
| Random-DRTP | 80011–80015 | 是 | 检验 topology-semantic difficulty mapping 是否提供额外价值 |
| UTR | 主实验 A/B 冻结终点 | 否 | 主结果参考 |
| DRTP | 主实验 A/B 冻结终点 | 否 | 主结果参考 |

每条新增轨迹固定为 39,063 updates、4 environments、64 rollout steps，即 10,000,128 环境步；总新增计算量为 100,001,280 环境步。训练与最终评估均不读取 endpoint tape。

这是**非配对 fresh cohort**：不得将新 seed 的 Fixed/Random-DRTP 与历史 A/B DRTP 写成 paired delta。论文中应将其表述为独立机制队列，并报告 mean、median、lower tail、sample SD、success、timeout 与 collision。

## 上传文件

- `DRTP_SEMANTIC_ABLATION_NONPAIRED_10M_V1.zip`
- `DRTP_SEMANTIC_ABLATION_NONPAIRED_10M_V1.zip.sha256`

## 启动命令

在新云端实例的 `/root/autodl-tmp` 下执行：

```bash
PKG=DRTP_SEMANTIC_ABLATION_NONPAIRED_10M_V1.zip
PROJ=/root/autodl-tmp/drtp_semantic_ablation_nonpaired_10m_v1

tr -d '\r' < "${PKG}.sha256" | sha256sum -c -
test ! -e "$PROJ" || { echo "项目目录已存在，拒绝覆盖"; exit 1; }
mkdir -p "$PROJ"
unzip -q "$PKG" -d "$PROJ"

screen -dmS drtp_semantic_ablation bash -lc '
set -euo pipefail
cd /root/autodl-tmp/drtp_semantic_ablation_nonpaired_10m_v1/DRTP_SEMANTIC_ABLATION_NONPAIRED_10M
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
MAX_PARALLEL=10 PYTHON_BIN=python \
bash scripts/launch_drtp_semantic_ablation_autodl.sh \
  > semantic_ablation.out 2> semantic_ablation.err
sync
'

sleep 8
screen -ls
tail -n 30 "$PROJ/DRTP_SEMANTIC_ABLATION_NONPAIRED_10M/semantic_ablation.err" || true
```

该命令不包含自动关机，避免在异常退出时过早销毁诊断信息；只有在你确认完整性与打包需求后，才应单独设置云端关机策略。

## 完成后下载的目录

下载完整 `results/ablation/drtp_semantic_ablation_nonpaired/`，尤其保留：

- `runs/*/seed*/run_manifest.json`；
- `runs/*/seed*/drtp_topology_sampler_manifest.json`；
- `runs/*/seed*/drtp_topology_sampler_log.csv`；
- `evaluations/final_10m/`；
- `diagnostics/semantic_ablation_final/`。
