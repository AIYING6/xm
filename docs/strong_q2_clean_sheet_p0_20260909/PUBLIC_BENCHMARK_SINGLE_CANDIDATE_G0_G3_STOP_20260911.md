# 公开基准唯一候选：G0/G3 零训练审计与停止

## 决定

`ECR-MRTA_STOP`。不授权克隆、改造、实现、短试或云端训练。

这不是工程失败；这是三重筛选在训练前正确阻止了一个不具备论文新颖性与公共资产条件的候选。

## G0：公开资产与任务基础 —— STOP

审计对象：Xiao 等人的 Extended Team Orienteering Problem 多 UAV 任务分配仓库。

### 可核验事实

1. 项目公开提供了 GA、ACO、PSO 与 `evaluate.py`，并明确指出 RL `step` 接口“仍在开发中”，没有可运行的 RL demo。[仓库说明](https://github.com/robin-shaun/Multi-UAV-Task-Assignment-Benchmark)
2. `evaluate.py` 的公开实现将每个动作直接折算为飞行时间加固定任务执行时间，随后更新剩余时间与任务收益；它没有任务中途的事件到达、执行进度状态、释放/保留承诺状态或异步再决策接口。[源文件](https://raw.githubusercontent.com/robin-shaun/Multi-UAV-Task-Assignment-Benchmark/master/evaluate.py)
3. 2026-09-11 对仓库根目录的许可证路径检查返回 404；仓库页面的文件表也未列出许可证文件。因此该资产可作**阅读与概念参照**，但在未获得明确许可前不应直接纳入可再发布研究代码。

### 判断

为了让候选产生所需的“承诺—保留—释放”行为，必须实质性重写状态、转移与决策时间轴。这样不再是“基于成熟公开基准”，而是又一次自定义任务构造；同时许可证不清。G0 不通过。

## G3：机制新颖性 —— STOP

候选的核心命题是：在动态不确定任务中保留未来重分配能力，而非过早承诺。文献检索表明这不是尚未被命名或识别的机制空缺。

| 最近邻工作 | 已覆盖内容 | 对候选的影响 |
|---|---|---|
| Dai et al., *On the Value of Commitment Flexibility in Dynamic Task Allocation* | 明确研究任务承诺、解约成本与承诺灵活性的价值 | 直接覆盖“何时保留而非承诺”的核心思想。[论文](https://www.cs.cmu.edu/~softagents/papers/msdm09_dai.pdf) |
| Zhang et al., Adaptive Cross-Path CBBA | 动态任务出现、时间衰减收益与“未来承诺释放”机制 | 直接覆盖事件触发的未来任务释放。[检索记录](https://eurekamag.com/research/108/295/108295510.php) |
| Choudhury et al., *Dynamic multi-robot task allocation under uncertainty and temporal constraints* | 执行不确定性与时间约束下的动态分配 | 覆盖候选的时长不确定性问题层。[公开稿](https://iliad.stanford.edu/pdfs/publications/choudhury2022dynamic.pdf) |
| Huang et al., RL-TAPU | 异步完成下的实时分配、局部信息与不确定环境 | 覆盖候选的 MARL/异步执行动机。[论文](https://doi.org/10.1111/mice.13535) |
| Li et al., *Multi-UAV cooperative task reallocation in dynamic environments* | 事件触发 UAV 任务重分配、能量/移动性/时限/通信约束 | 覆盖 UAV 情景中的在线重分配。[论文](https://doi.org/10.1016/j.aei.2026.105107) |

即使加入 MARL、异构速度和一个 `reserve` 动作，也只能构成已有“承诺灵活性 + 动态重分配 + 不确定执行”的组合变体。它没有通过“不只是既有机制换名组合”的预设要求。

## 不执行的 G1/G2/G4/G5

G0 与 G3 任一失败已足以停止。因此不制作反例、不设计新的 `reserve` 动作、不改公共基准、不跑可学习性试验，也不估算正式预算。这避免将资源投入一个在论文贡献层面已失败的候选。

## 对主线的约束

1. 该候选永久关闭，不创建 ECR v2、v3 或同义重命名版本。
2. 不将这一停止结果解释为“所有公开基准都不可用”。它只否定“执行时长不确定性下的承诺灵活性”作为当前新机制主张。
3. 下一次候选必须先在**机制层**同时通过：公开基准适配、直接近邻排除、可识别性，再允许任何代码改动。

## 证据可信度

- 公开仓库与原始源文件：一级资产证据。
- DOI/原始公开论文：一级文献证据。
- 检索结果中的摘要信息：用于发现近邻；正式写作前仍需逐篇全文核验。
