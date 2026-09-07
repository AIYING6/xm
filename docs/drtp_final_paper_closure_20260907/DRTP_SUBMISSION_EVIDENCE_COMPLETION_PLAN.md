# DRTP 投稿级证据补齐计划：从“采样策略”到“通信拓扑退化下的鲁棒协同”

**状态：** 分析与证据合同；不授权算法修改或新增大规模训练。  
**冻结范围：** DRTP、UTR、PLR-style、奖励、策略网络、PPO、观测/动作接口、拓扑支持集、A/B seed registry、终点评估协议均保持不变。  
**唯一仍在运行的正式训练：** 6-UAV UTR/DRTP 跨尺度验证。其结果仅在冻结终点聚合完成后使用。

## 1. 投稿叙事与可验证论证链

本文不将通信故障简化为普通噪声，也不把 DRTP 表述为任意采样技巧。需要由现有和已规划证据支撑的中心论点为：

> **通信拓扑退化改变多智能体协同可利用的信息结构；DRTP 通过拓扑语义化的训练暴露分配塑造策略在本文冻结故障接口下的鲁棒协同能力。**

论证链分为五个层次，任何一步缺少数据时必须保留其边界，而不能由叙述代替证据：

```text
通信边/节点/时序退化
        ↓
信息路径、可达性与角色协同约束改变
        ↓
不同故障拓扑的条件困难度不同
        ↓
均匀暴露无法区分其训练需求；DRTP 受约束地重分配既有条件的暴露
        ↓
在固定终点、独立 cohort 与冻结 shift 中检验鲁棒协同结果
```

其中，前两层由问题定义和冻结 topology manifest 说明；第三、四层由机制分析说明；最后一层仅由 A/B、OOD、PLR 和 6-UAV 的正式聚合数据说明。机制图和关联分析可增强解释力，但不能单独证明策略内部因果机制。

## 2. 研究问题—证据—写作边界

| RQ | 审稿人真正的问题 | 证据与当前状态 | 可支持表述 | 禁止扩大为 |
|---|---|---|---|---|
| RQ1 | 拓扑语义化暴露是否改善故障鲁棒性？ | 已完成的 A/B 独立五-seed 固定 10M endpoint，UTR vs DRTP | 在本文评估的拓扑退化设置下，DRTP 展示了相对 UTR 的重复 cohort-level 鲁棒性收益 | 每个 seed 均提升或所有安全指标改善 |
| RQ2 | 是否能迁移到未见故障结构？ | 已完成的冻结 structural/parameter OOD | 在冻结 OOD shift 内保持正向 cohort-level 对比 | 广义 OOD 或真实部署泛化 |
| RQ3 | 这是拓扑语义，还是任意优先采样都能做到？ | 已完成匹配 PLR-style A/B 比较 | DRTP 与 generic prioritization 竞争，且提供 topology-aware allocation | DRTP 全面胜过 PLR-style |
| RQ4 | 结论是否局限于 3-UAV？ | 6-UAV UTR/DRTP 正式终点正在运行 | 仅在完成后报告 cross-scale trend | 用旧中止 run 或中途 checkpoint 主张可扩展性 |
| RQ5 | 为什么该方法会有作用？ | 待从 A/B 归档恢复的 topology manifest、sampler telemetry 和固定 endpoint 条件指标 | 结果是否与“拓扑退化—困难度—暴露”描述链一致 | 后验相关即为唯一根因或严格因果证明 |
| RQ6 | 额外成本是否实际可接受？ | 待进行匹配硬件运行开销测量 | reset-side sampler 的时间/内存成本在给定配置下可量化 | 参数数相同即等于没有运行开销 |

## 3. Priority 1：6-UAV 跨尺度验证（正式结果，正在运行）

### 3.1 目的与锁定比较

6-UAV 是对“同一训练暴露思想能否迁移到更大异构团队”的独立正式检验，而不是替代 3-UAV 的因果对照。唯一比较为 UTR vs DRTP；环境接口、PPO、训练预算与终点评估协议保持匹配。正式聚合应以训练 seed 为独立单位，报告 mean、median、lower tail、paired delta、success、timeout 和 collision。

### 3.2 结果进入论文的规则

1. 仅导入新卡 fresh restart 的最终 checkpoint 和对应 evaluation manifest。
2. 不使用停止的旧 6-UAV run，不从训练中途日志估计终点，不按结果增删 seed。
3. 结果不需要“绝对碾压”；应并列呈现回报、lower tail、配对方向和安全/超时取舍。
4. 若结果较弱，正文只能说跨尺度证据受限，不倒推修改 DRTP 或重定义协议。

**交付物：** `Table 6`、`Fig. 6`、每 seed endpoint 表和运行/evaluation manifest。6-UAV 未完成前，摘要、结论和标题不得含“已验证跨尺度迁移”的断言。

## 4. Priority 1：运行开销与计算可行性（低成本、独立于性能终点）

### 4.1 不可替代的测量问题

DRTP 不改变 actor、critic 或 PPO，并不等于没有额外计算成本。投稿表中必须以测量值回答 sampler 更新、整体 wall-clock 与峰值显存的实际代价；历史 telemetry 模块的开销或异构硬件上的训练时长不可直接替代该比较。

### 4.2 两阶段执行合同

**阶段 A：归档读取。** 先从正式 UTR、DRTP、PLR-style run manifest 和日志提取开始/结束时间、GPU 型号、CPU 线程、并发数、软件版本与训练步数。仅当三者硬件、并发和步数完全可比时，才可将其作为端到端训练时间的补充描述。

**阶段 B：匹配微型测量。** 若阶段 A 不可比，在同一台 GPU、相同 CPU 线程、相同并发策略、相同环境数、相同随机种子和相同软件版本上，分别执行 UTR、DRTP、PLR-style 的固定短窗口测量。短窗口只记录 profiler 数据，不进行终点评估、不做模型筛选、不改变任何方法超参数；建议报告三个独立重复的 median 与范围。记录：

- 每环境步和每 PPO update 的 wall-clock；
- reset 条件选择与 `q` 更新的累计时间及其占比；
- `torch.cuda.max_memory_allocated()` 峰值显存；
- 配置、硬件、并发与软件版本。

该微型测量可包含固定数量的训练 update 以覆盖真实 sampler 调用，但不是新的算法性能实验；其产物不能用于增补或替换主终点性能结论。

### 4.3 论文呈现

`Table 5` 仅填可复现的测量值：方法、wall-clock、sampler/reset overhead、峰值 GPU memory、测量配置。没有测量值时保留 `TBD`，不得根据参数数量相同写“零开销”。

## 5. Priority 2：Topology Difficulty Mechanism Analysis（只读分析）

### 5.1 分析问题

机制分析回答的是：“不同通信拓扑退化是否具有可量化的结构差异，并且 DRTP 的暴露变化是否与相对名义困难度相一致？”它不是寻找某一坏 seed 的根因，也不是启动新训练线。

### 5.2 最终资产门

只有下列**正式 A/B 归档资产**全部存在时才输出可用于正文的 RQ5 图表：

| 资产 | 最低内容 | 作用 |
|---|---|---|
| 冻结 condition/topology manifest | 组成员、名义/故障标签、失效对象、开始时刻、持续时间和图定义 | 重建条件结构语义 |
| 每个 DRTP seed 的 sampler CSV/manifest | update 或 interval 对应的 `q`、difficulty/deficit、实际采样或 exposure count | 生成暴露与 `q` 轨迹 |
| 训练 log 与 run manifest | 完整步数、seed、版本和完成状态 | 审计数据来源、排除中断 run |
| 固定 endpoint per-condition metrics | return/J、success、timeout、collision、condition、seed、cohort | 将拓扑特征和结果对齐 |

当前本机材料表明这些 sampler 文件曾在云端训练归档中保存，但未包含在当前论文资产目录。该缺口是**资产待恢复**，不是科学上的 NO-GO；在资产恢复前不能用旧 1M/开发期日志代替最终 A/B 机制证据。

### 5.3 冻结指标与计算方式

对每个条件 (c)，从名义图 (G_0) 和故障图 (G_c) 只读计算以下描述符，不人为挑选“最支持方法”的单一指标：

- **断边比例**：\(d_E(c)=1-|E_c|/|E_0|\)；
- **可达对损失**：\(d_R(c)=1-R(G_c)/R(G_0)\)，其中 \(R\) 为角色相关或全图可达有序对数量；
- **平均可达路径变化**：在可达对上计算平均最短路径，并将失连状态单列，而非把无穷距离任意截断；
- **连通分量与角色路径标记**：分量数、关键 scout–relay–terminal 路径是否存在；
- **图退化向量**：\(\mathbf d(c)=[d_E,d_R,\Delta L,\text{components},\text{role-path flag}]\)。

不应在看结果后把该向量压缩成一个新权重或修改 DRTP。若论文需要一个便于读图的“graph degradation degree”，必须预先给出固定归一化公式，并同时保留上述分量表。

### 5.4 只读分析与报告规则

1. cohort A、B 分开；训练 seed 为独立单位，评估 episode 不当作独立重复。
2. 对每个 topology group 报告 endpoint return degradation、success、timeout、collision 与相对名义缺口。
3. 对每个 DRTP seed 绘制 `q_t`、实际 exposure share 和记录的 difficulty/deficit；在组内先对齐 update 比例，再分别汇总 A/B。
4. 报告 topology descriptor 与条件表现、difficulty 与 exposure 的描述性关联及区间；不以少量 seed 的显著性阈值替代效应大小与图形。
5. 机制结论只能使用下列三个标签之一：
   - `MECHANISM_ALIGNMENT_REPEATED`：A、B 均显示方向一致的 topology–difficulty–exposure 描述链；
   - `MECHANISM_ALIGNMENT_COHORT_DEPENDENT`：至少一批的方向或量级不一致；
   - `MECHANISM_ASSETS_BLOCKED`：正式资产不完整，无法作最终机制图。

即使得到第一类标签，措辞也只能是“与 topology-aware robustness shaping 的预期一致”，而不是“证明唯一因果机制”。

### 5.5 图表交付

- **Fig. 1（问题图）**：正常/退化通信图、信息路径损失、协同风险；先解释问题，后引入方法。
- **Fig. 2（方法图）**：topology failure library → groups → nominal-relative difficulty → bounded `q` → MAPPO；明确 actor/critic/PPO/reward/observation/action/transition 不改变。
- **Fig. 3（机制图）**：左侧 UTR/PLR-style/DRTP exposure mechanism，右侧导入的 `q_t` 与实际 exposure；仅使用正式 A/B sampler CSV。
- **Supplementary Table S1（难度表）**：条件/组、图描述符、名义相对性能缺口、最终曝光量、A/B 分别汇总。

## 6. Priority 2：Sampling Probability Evolution（只读图，不是性能曲线）

`q_t` 图必须满足：

- 显示六个非名义组及固定名义质量，标注各组的概率下界/上界；
- 使用真实 logged `q` 和 actual exposure，而非从最终条件表现反推；
- A、B 分面展示，不以 pooled n=10 图掩盖 cohort 差异；
- 明确这是训练分布过程证据，不是在线 evaluation 曲线，也不参与 checkpoint 选择。

UTR 的对照为固定均匀非名义分配；PLR-style 只展示其在 matched protocol 中可审计的通用 priority 分配逻辑，不虚构不存在的 topology-group `q`。

## 7. Priority 3：可选 Difficulty-signal 消融（默认不启动）

若且仅若 6-UAV、运行开销与资产恢复均完成，而论文仍被目标期刊的机制新颖性门槛卡住，可预注册一项小规模开发性消融：UTR、DRTP full、去 difficulty-signal 的固定/均匀版本、随机自适应版本。它的目的仅是分辨“拓扑语义困难信号”与“任意动态采样”。

此项当前**没有授权、没有 seed、没有训练预算，也不是投稿前置条件**。不得在 6-UAV 或主结果不理想时作为结果驱动补救。

## 8. 最终图表与主稿落位

| 图/表 | 审稿目的 | 数据状态 |
|---|---|---|
| Fig. 1 Topology degradation problem overview | 解释为何结构性信息变化是问题本身 | 可现在绘制，基于冻结图定义 |
| Fig. 2 DRTP framework | 显示 reset-side allocation 与不变的学习器 | 可现在绘制 |
| Fig. 3 Mechanism validation | 说明 topology–difficulty–exposure 描述链 | 待 A/B sampler assets 恢复 |
| Fig. 4 A/B paired endpoint comparison | 支撑重复 cohort-level UTR 对比 | 已有正式聚合；逐 seed 图需 CSV |
| Fig. 5 Frozen OOD topology shift | 界定未见结构上的结果 | 已完成正式聚合 |
| Fig. 6 6-UAV cross-scale | 回答团队规模迁移 | 等待正式终点 |
| Table 5 Runtime overhead | 回答工程成本 | 待匹配测量 |
| Table 6 6-UAV endpoint | 报告跨尺度边界 | 等待正式终点 |

## 9. 来自优秀 UAV/RL 论文的写作取向

所提供的有人/无人协同、无人集群仿真与空战强化学习文献呈现出一致的投稿级组织方式：先建立系统能力为何受限，再说明该限制如何转化为可控的学习问题，随后以最小而可审计的方法改动和多层验证回答问题。DRTP 主稿应遵循这一顺序：

1. 通信拓扑退化改变角色间信息路径，而非仅增加一个场景标签；
2. 训练暴露分配是固定策略学习器下可被精确隔离的干预变量；
3. DRTP 是这一变量的 topology-aware robustness shaping，而不是为采样规则重新命名；
4. A/B、OOD、PLR、6-UAV、机制图和成本表各回答不同审稿问题，避免把所有结果堆成同一“胜负表”。

这是一种强化问题价值的组织，不改变任何现有结论，也不掩盖 PLR 的 cohort-dependent 竞争性。

## 10. 执行清单与终止条件

1. **等待并回收 6-UAV 正式终点包**；验证 SHA256、manifest、每 seed 完整性后生成 Table 6/Fig. 6。
2. **从 A/B 云端完整归档恢复 mechanism asset bundle**；只读检查第 5.2 节资产门，随后生成 Fig. 3/S1 或诚实输出 `MECHANISM_ASSETS_BLOCKED`。
3. **完成匹配运行开销测量**；若归档硬件可比则直接生成 Table 5，否则按第 4.2 节做短窗口 profiler，不作性能比较。
4. **统一重构中文主稿**；6-UAV、机制与成本数据均可追溯后，才填入图表和正文，不重新开发算法。
5. **最终投稿门**：每一主张可追溯至冻结 artifact；6-UAV 与 runtime 不留未标注空白；所有跨 cohort 报告分开呈现；不存在“全 seed”“全面胜出”“实飞有效”这类越界措辞。

## 11. 审稿风险与预置回答

| 可能质疑 | 预置证据/回答 |
|---|---|
| “这只是普通 curriculum 或 PLR。” | Fig. 2 与 PLR matched A/B：DRTP 的对象是冻结的拓扑故障组，有名义参考和有界单纯形约束；承认 PLR 竞争性而不虚构全面胜出。 |
| “为什么应该关注 topology，而不是一般扰动？” | Fig. 1 + 图描述符：拓扑直接改变角色间可达信息与协同路径，区别于不改变信息结构的一般状态噪声。 |
| “效果为什么可信？” | independent A/B、固定 endpoint、OOD、按 seed 报告与协议/manifest。 |
| “机制只是事后解释。” | RQ5 明确标为只读描述链、A/B 分开、不得作唯一因果归因；若资产缺失则不作该主张。 |
| “动态分配是否太贵？” | Table 5 的匹配 profiler，而非参数量推断。 |
| “能否扩展到团队规模？” | 仅由 fresh 6-UAV 终点回答；完成前不写跨尺度结论。 |

