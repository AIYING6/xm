# P8E ACFID 时序恢复环境预检

## 结论

`ACFID_SEQUENTIAL_PREFLIGHT_PASS`

标准时序恢复环境通过训练前语义、组合隔离、反事实可复现性和动作可区分性检查。当前授权训练 runner 的实现和极短 dry-run，不授权 1M pilot。

## 时序语义

每个 episode 固定为：任务开始 → primitive fault 发生 → 检测延迟 → 一次团队级恢复决策 → 固定底层控制器执行 → 延迟任务结局。故障发生前和检测完成前，策略看不到 active fault signatures；检测后只看到 primitive degradation signatures，不输入组合类别 ID。

## 检查结果

| 检查 | 结果 |
|---|---|
| train/test 故障组合不重叠 | PASS |
| 检测前隐藏故障 | PASS |
| 检测后仅暴露 primitive signatures | PASS |
| 反事实 runtime clone 精确 | PASS |
| 五类恢复动作均有最优区域 | PASS |
| 单故障非全易、非全崩溃 | PASS |
| held-out 组合非全成功、非全失败 | PASS |
| 恢复动作能改变任务结局 | PASS |

训练支持为 nominal、6 个 single 和 6 个冻结 pair，共 13 个组合；测试支持为其余 9 个 pair、20 个 triple 和 15 个 quadruple，共 44 个组合。

## 量化结果

- 单故障 oracle value 均值：1.3396；
- held-out 组合 oracle success：6.99%；
- 动作间平均价值跨度：0.5943；
- 400 个上下文及全部组合中，五类动作的最优次数分别为：continue 7129、relay reposition 5061、role reassign 3788、target reassign 3844、safe abort 2978。

## 风险边界

held-out oracle success 仅略高于冻结的 5% 下限，说明测试集合偏难。不能在看到 pilot 后修改成功阈值或删减高阶组合；pilot 的主要判断必须联合 recovery-action regret 与 mission success。该环境仍是宏观高层恢复资格任务，不是最终 3DOF 或硬件证据。

## 下一步

实现统一 PPO runner，并执行不超过数千 transition 的 dry-run，审计：

1. 三方法训练采样序列逐 episode 一致；
2. held-out fault sets 从训练、归一化和 checkpoint 选择路径中不可达；
3. 三方法均产生有限梯度且参数实际更新；
4. evaluation 仅加载固定最终 endpoint；
5. action regret 使用同一 cloned context 与 common noise 计算。
