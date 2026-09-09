# P1E：最小可训练任务合同零训练审计

## 结论

`P1E_TRAINABLE_CONTRACT_AUDIT_PASS`

最小两阶段任务通过接口、信息边界、固定 tape、端点还原和常数策略非支配审计。该结果允许继续设计 PPO 接口和校准目标，但仍不授权性能训练。

## 冻结任务结构

一个 episode 包含两个决策阶段：

1. **公开线索阶段**：三架 UAV 均观察到链路可靠度上下文，但不知道本回合消息是否会送达；该阶段动作不产生任务决策。
2. **私有投递与承诺阶段**：发送方知道自己已发送任务令牌但不知道是否送达；接收方私有地知道是否收到；各方选择 commit、defer 或 fallback，随后执行 16 步 3DOF 轨迹。

如果接收方未收到任务令牌却选择 commit，其本地计划被视为与发送方任务窗口不兼容，并执行无支持轨迹。该语义避免“双方无条件 commit 即可绕过通信不确定性”的退化解。

## 固定 tape

- 评价回合：300；
- low / middle / high 三个可靠度上下文各 100 回合；
- 冻结投递率分别为 0.15、0.45、0.85；
- 拟定 pilot 训练 seeds：98101、98102、98103；
- tape 中的 episode 是评价样本，不作为独立训练重复。

## 脚本可解性与非支配结果

| 策略 | 平均任务价值 |
|---|---:|
| 上下文自适应脚本 | 4.033 |
| always-commit | 0.700 |
| always-defer | 2.933 |
| always-fallback | 2.000 |

上下文自适应脚本同时优于三个常数模式，说明任务不是由 always-commit、always-defer 或 always-fallback 支配。该比较只是解析脚本审计，不是算法性能比较。

## 信息边界

- 公开线索阶段，送达/丢失两种潜在状态下所有 actor 观测完全一致；
- 决策阶段，发送方和中继观测仍完全一致；
- 只有接收方的私有 `received` 字段不同；
- centralized critic 的输入只由合法局部观测的并集组成，没有额外追加全局 delivery 真值；
- `info` 中的 delivery 字段仅用于评价遥测，不进入 actor observation。

## 端点闭环

固定 tape 覆盖：兼容双边承诺、单边/不兼容承诺、协同延迟和安全降级。每回合任务价值可由原始 `info` 逐项重构，并同时记录碰撞、约束违规、能耗、fallback、defer 和 stale-token commit。

## 证据边界与下一步

P1E 证明任务接口合法、可脚本求解且不被常数策略支配。它没有证明 neural policy 可学习，也没有解决区间估计如何校准、稳健决策如何形成可训练概率分布、PPO 如何保持容量与损失公平。下一步只能做 P1F 的损失与采样接口审计，不能直接运行 15M pilot。

## 可追溯文件

- 环境：`envs/epistemic_commitment_trainable_env.py`
- 审计：`scripts/audit_epistemic_commitment_p1e_trainable_contract.py`
- 测试：`tests/test_epistemic_commitment_p1e_trainable_contract.py`
- 机器结果：`docs/strong_q2_clean_sheet_p0_20260909/P1E_RESULT.json`
