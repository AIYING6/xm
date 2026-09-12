# PSCR P4 G1 开发性基线判定

**状态：** `G1_LEARNABILITY_PASS_DEVELOPMENT_ONLY`

## 运行与证据位置

- 冻结配置：`configs/pscr_p4_reliability_baseline_g1_freeze_20260912.json`
- 三条训练轨迹：`results/development/pscr_p4_reliability_baseline_g1_20260912/seed99801` 至 `seed99803`
- 分可靠度终点评估：`results/development/pscr_p4_reliability_baseline_g1_20260912/evaluation_seed*`
- 汇总：`results/development/pscr_p4_reliability_baseline_g1_20260912/diagnostics/provisional_g1_reliability_endpoint`

## 判定

G1 的预设学习性门槛为：至少两个独立训练 seed 在两条可靠度带均出现非零主服务和未来服务。seed `99802` 与 `99803` 满足该条件，因此允许实施已冻结的 RC-PSCR-MAPPO 与匹配控制臂。

该判定**不是**主方法性能结论，且不得与未来正式 cohort 合并。训练时 checkpoint 的内部协议字段沿用了 G0 标识；因此这一批只保留为开发性学习性证据。后续 M1 及正式训练将使用显式 `--run-protocol` 写入对应冻结协议。

## 仍然存在的基线缺口

seed `99801` 在高可靠度带未获得服务；所有三条轨迹的已完成服务链切换计数均为零。因此 Plain-MAPPO 的服务能力尚不稳定，也未表现出可确认的可靠度条件化承诺—释放行为。这是 M1 要检验的缺口，不应提前解释为 RC-PSCR-MAPPO 的有效性。
