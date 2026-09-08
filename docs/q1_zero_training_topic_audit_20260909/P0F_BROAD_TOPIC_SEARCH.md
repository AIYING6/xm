# P0F：强二区广域选题审查

**日期：** 2026-09-09  
**裁决：** `P0F_NO_GO_FOR_ALL_THREE_AS_PRIMARY_ALGORITHM`

## 1. 候选一：有限故障数据下的离线受约束适应

### 可发表问题

部署系统不能反复制造故障并在线试错时，能否只利用既有多智能体故障轨迹，使策略适应新拓扑，同时限制任务性能和安全代价的下降？

### 最近邻压力

- [Conservative Offline Policy Adaptation in Multi-Agent Games](https://proceedings.neurips.cc/paper_files/paper/2023/hash/a31253f4871694f09541122d6b6f5ad1-Abstract-Conference.html) 已直接研究多智能体离线策略适应、distribution shift 与保守偏离。
- [Conservative Data Sharing for Multi-Task Offline RL](https://papers.nips.cc/paper/2021/hash/5fd2c06f558321eff612bbbe455f6fbd-Abstract.html) 已覆盖跨任务数据共享造成的分布偏移及保守路由。
- [Cooperative Policy Agreement](https://ojs.aaai.org/index.php/AAAI/article/view/34465) 已处理多来源 offline MARL 数据的 policy mismatch。
- [DARA](https://arxiv.org/abs/2203.06662) 已研究少量目标数据下的 offline dynamics adaptation。
- [Counterfactual Data Augmentation](https://arxiv.org/abs/2007.02863) 已利用局部因果分解生成离线反事实经验。

### 本地数据充分性审查

`algorithms/ri_gmappo/failure_aware_telemetry.py` 记录故障窗口内的物理位置、合法图边、动作、即时奖励、终止与安全字段。这些数据适合机制诊断，但不构成标准 offline MARL 数据集：

- 未保存完整 actor observation、node/edge feature 与 centralized critic input；
- 只覆盖故障相对窗口，而非完整 episode；
- 未保存 behavior action probability；
- PPO rollout buffer 没有作为可复用数据集持久化；
- 历史运行来自不同开发合同，不能无条件合并。

因此，使用现有资产训练 offline policy 会引入不可审计的数据重建和支持度问题。若重新采集完整数据，则“最大复用历史实验”的成本优势基本消失。

### 裁决

`NO_GO_DATASET_ABSENT_AND_DIRECT_OVERLAP`。不授权把现有诊断遥测包装成 offline MARL 数据集。

## 2. 候选二：拓扑退化下的有限样本风险校准

### 可发表问题

能否在部署前根据校准数据识别策略在拓扑退化条件下的失效风险，并给出有限样本控制？

### 最近邻压力

- [Conformal Risk Control](https://arxiv.org/abs/2208.02814) 已提供分布无关的有限样本风险控制框架。
- [Conformal Policy Learning under Distribution Shifts](https://arxiv.org/abs/2311.01457) 已将 conformal quantile 用于策略切换和传感运动控制。
- 2025 年后已有 offline safe RL 与 constraint-adaptive policy switching 等直接邻域。

### 统计可行性

本项目的独立统计单位是训练 seed，而不是同一 checkpoint 下的 episode。正式 cohort 每个方法只有 5 个训练 seed；即使合并两个合同匹配 cohort，也不能把 14,000 个 episode 当成 14,000 个独立部署样本。如此小的独立样本量难以产生非平凡、稳定且可审稿的有限样本风险界。

此外，策略切换、拒绝或 fallback 与用户追求的“单模型自身稳定算法”目标不一致。

### 裁决

`NO_GO_AS_PRIMARY_ALGORITHM`。可作为未来部署附加研究，但不能补足当前核心算法创新。

## 3. 候选三：跨任务、跨平台拓扑鲁棒性基准

### 可发表问题

现有 MARL benchmark 是否系统性低估通信拓扑退化带来的策略脆弱性？

### 最近邻与资产审查

- Offline MARL 已出现 Off-the-Grid MARL、D4MARL、MangoBench 等数据与基准工作。
- 通信鲁棒 MARL 已形成动态拓扑、噪声、带宽和 agent dropout 等评价体系。
- 仓库虽然包含 2D、3DOF 和 6-UAV 资产，但它们来自不同项目阶段、任务语义和冻结合同，不能直接拼接为统一 benchmark。
- 要形成可信 benchmark，至少需要第二个外部标准环境、统一故障算子、数据格式、基线复现和公开数据合同。

### 裁决

`NO_GO_AS_HIGH_RETURN_ALGORITHM`。它可能成为独立 benchmark 论文，但不满足当前“高收益稳定算法”的首要目标。

## 4. 排名

| 候选 | 新颖性潜力 | 现有资产复用 | 成本 | 成为高收益稳定算法的概率 | 结论 |
|---|---:|---:|---:|---:|---|
| 离线受约束适应 | 中 | 低（缺完整数据） | 高 | 低—中 | 不启动 |
| 风险校准 | 中 | 高 | 低 | 低 | 仅附加研究 |
| 跨平台 benchmark | 中—高 | 中 | 很高 | 不适用 | 非算法主线 |

## 5. P0F 总结

在“最大复用现有资产、容易出成果、单模型训练后稳定、强二区创新”四项同时成立的约束下，本轮三个广域候选均不通过。问题不在于缺少一个巧妙模块，而在于现有资产是为 on-policy DRTP 采样问题生成的；它不能自然支撑另一类高创新问题而不付出新的数据或环境成本。

