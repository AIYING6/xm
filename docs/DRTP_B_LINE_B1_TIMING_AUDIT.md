# DRTP B线 B1：历史分叉时间审计

状态：`TIMING_UNRESOLVED_FROM_EXISTING_LOGS`

本审计服务于独立的 B 线，不改变 A 线论文的算法、主结果或投稿节奏。

已复核的历史材料包含正式 cohort 2301--2305 与独立 cohort 2401--2405 的训练日志、DRTP sampler 日志及既有零训练 forensic 汇总。现有资产有 781,260 条 PPO 记录和 1,580 个 sampler window。它们可以描述 cohort 末期的 PPO 指标、EMA/difficulty 与采样权重差异，但没有与同一 episode 时间轴同步的动作、角色几何、信息路径、任务支持和终止前兆记录。

因此，历史日志不能可靠回答“哪一个行为变量最先分叉”，也不能把相关性的末期差异升级为 sampler 的因果失败机制。此前 2601--2603 的 Mechanism V1 云端运行还存在 runner `config.seed` 与请求 seed 不一致的问题；该资产永久标记为 `TECHNICAL_INVALID`，不得作为 B 线证据。

结论：B1 不授权 Stable-DRTP、算法修改或新的长训练。下一道唯一 gate 是 B2：证明新增行为遥测在随机策略、PPO 更新和运行态恢复下完全不改变训练轨迹。
