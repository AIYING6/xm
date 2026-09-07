# DRTP 6-UAV 正式结果收口协议

## 目的

在 fresh 6-UAV UTR/DRTP 正式训练、固定 10M checkpoint 评估和原始聚合均完成后，生成投稿表格与 Fig. 6。该步骤不启动训练、不再次评估 policy、不访问任何在线 evaluation tape，也不修改已有结果。

## 必经完整性门

汇总器只接受含有 `DRTP_6UAV_CROSS_SCALE_COMPLETE.json` 的结果根目录，并逐项验证：

1. UTR 与 DRTP 各五个 completed 10M run manifest；
2. 每个 run 的 checkpoint SHA 与 endpoint CSV 一致；
3. 每个 seed/arm 具备 7 个冻结条件，每条件 100 个 episode；
4. 每个 endpoint 文件总计 700 行；
5. 输出目录此前不存在，避免覆盖原始或已审计的结果。

任何一项不满足时，停止汇总并保留原始结果，不使用中途 checkpoint 或部分结果作跨尺度论文主张。

## 论文统计口径

以训练 seed 为独立单位。对每个方法报告：

- 名义条件回报；
- 六个非名义条件平均的 perturbed return；
- 最差故障条件回报；
- perturbed success、timeout 和 collision；
- mean、median、training-seed lower tail 和 sample SD；
- 同一训练 seed 上 DRTP minus UTR 的 paired delta。

对 collision/timeout，表中的 `worst seed` 指该风险率最高的训练 seed；对回报/success 指最低的训练 seed。跨尺度结果只用于本文冻结 six-UAV 接口下的趋势判断，不代替 3-UAV A/B 或 OOD 结论，也不要求每个 seed 同方向。

## 执行命令

在完成训练的云端项目根目录执行：

```bash
python scripts/finalize_drtp_6uav_cross_scale.py \
  --output-root results/final_evidence/drtp_6uav_cross_scale_formal \
  --report-dir results/final_evidence/drtp_6uav_cross_scale_formal/diagnostics/submission_final \
  --execute
```

随后仅下载 `diagnostics/submission_final/` 及完整原始结果包。若训练包不含该汇总器，可将本仓库同名脚本复制到其 `scripts/` 目录；不得替换训练、环境、sampler 或评估代码。

## Fig. 6 合同

Fig. 6 为 quantitative paired comparison：左面板展示 perturbed return，右面板展示 perturbed timeout。每条线连接同一个训练 seed 的 UTR/DRTP 终点；原始数值位于 `DRTP_6UAV_PER_SEED_ENDPOINTS.csv`。图不使用 episode 当作独立重复，不做跨 cohort pool，也不以单一指标构成“全面胜出”声明。
