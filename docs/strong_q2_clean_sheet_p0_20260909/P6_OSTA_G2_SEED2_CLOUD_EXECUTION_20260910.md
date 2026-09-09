# OSTA G2 seed-2 严格续跑执行说明

上传：

- `OSTA_G2_SEED2_STRICT_CONTINUATION_V1.zip`
- `OSTA_G2_SEED2_STRICT_CONTINUATION_V1.zip.sha256`

在 AutoDL `/root/autodl-tmp` 执行：

```bash
cd /root/autodl-tmp

PKG=OSTA_G2_SEED2_STRICT_CONTINUATION_V1.zip
PROJ=/root/autodl-tmp/osta_g2_seed2_strict_continuation_v1

tr -d '\r' < "${PKG}.sha256" | sha256sum -c - || exit 1
test ! -e "$PROJ" || { echo "目录已存在，拒绝覆盖：$PROJ"; exit 1; }

mkdir -p "$PROJ"
unzip -q "$PKG" -d "$PROJ"
cd "$PROJ/OSTA_G2_SEED2_STRICT_CONTINUATION_V1"
find . -type f -name '*.sh' -exec sed -i 's/\r$//' {} +

screen -dmS osta_g2_seed2 bash -lc '
set -euo pipefail
cd /root/autodl-tmp/osta_g2_seed2_strict_continuation_v1/OSTA_G2_SEED2_STRICT_CONTINUATION_V1
bash AUTODL_RUN_G2_SEED2.sh > g2_seed2_workflow.out 2> g2_seed2_workflow.err
'

sleep 8
screen -ls
tail -n 30 g2_seed2_workflow.out 2>/dev/null || true
tail -n 30 g2_seed2_workflow.err 2>/dev/null || true
```

进度检查：

```bash
cd /root/autodl-tmp/osta_g2_seed2_strict_continuation_v1/OSTA_G2_SEED2_STRICT_CONTINUATION_V1

u=$(python - <<'PY'
import json
from pathlib import Path
p=Path('runs/pilot_seed2/status.json')
if p.exists():
    print(json.loads(p.read_text()).get('update', 0))
else:
    q=Path('runs/pilot_seed2/train_metrics.jsonl')
    if q.exists() and q.stat().st_size:
        print(json.loads(q.read_text().splitlines()[-1]).get('update', 8))
    else:
        print(8)
PY
)
awk -v u="$u" 'BEGIN {printf "G2 seed-2：%d/123 updates（%.2f%%）\n",u,100*u/123}'
pgrep -af 'train_mappo_r1_canonical.py' || echo "训练进程已结束"
tail -n 10 g2_seed2_completion/seed2_train.out 2>/dev/null || true
```

完成核验：

```bash
cd /root/autodl-tmp/osta_g2_seed2_strict_continuation_v1/OSTA_G2_SEED2_STRICT_CONTINUATION_V1
cat g2_seed2_completion/G2_PILOT_VERDICT.json
cat g2_seed2_completion/COMPLETION_MANIFEST.json
ls -lh /root/autodl-tmp/osta_g2_seed2_completion_results.tar.gz*
```

说明：该流程只把 seed-2 从冻结 checkpoint 的 update 8 严格续跑至 update 123，随后进行与 seed-1 配对的 G2 审计。无论 G2 为 GO 或 NO-GO，都会保存判定、打包结果并关机；不会自动进入 5M、专家训练或 OSTA 方法训练。

