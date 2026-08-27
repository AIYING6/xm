# 补充材料 S2｜训练、PPO 与采样器诊断

## S2.1 范围

本材料仅用于核验优化过程、训练日志完整性、PPO 数值诊断和 sampler 的实际活动。它不用于 checkpoint 选择、最佳阶段晋升，亦不用于替代共同 10M final checkpoint 的性能结论。

## S2.2 训练与 PPO 源数据

- `../formal_results/source_data/formal_training_monitor_binned.csv`：十条正式训练轨迹按 500 updates 分箱的训练平均回报、approximate KL 和 clip fraction。
- `../formal_results/source_data/sampler_telemetry_summary.json`：DRTP 六组权重、实际样本计数、EMA/difficulty 的汇总与完整性信息。
- 主稿附录B：共同 PPO 超参数、10M 终点、运行 manifest 与 runtime-state 完整性规则。

## S2.3 补充图S2｜训练过程

![补充图S2｜训练过程诊断](../formal_results/figures/figS1_training_diagnostics.png)

**图S2｜正式五种子训练过程诊断。** 细线为各训练种子经 500 updates 分箱后的日志，粗线为五种子均值，阴影为种子最小—最大范围。该图不用于方法性能比较或 checkpoint 选择。

## S2.4 解释边界

DRTP 与 UTR 的训练期场景权重按定义不同，训练 batch return 并非共同测试分布的最终性能估计。因而本材料最多说明训练过程没有使用中途表现进行终点替换，或 sampler 确实修改了故障组暴露；不能证明权重轨迹对某个最终策略行为存在单独因果作用。
