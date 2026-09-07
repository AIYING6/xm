# DRTP 投稿证据补齐状态更新（2026-09-07）

本更新只补充机制与计算可行性证据；不修改 DRTP、UTR、PLR-style、环境、训练预算、A/B seed 或终点评估协议。

## RQ5：为什么 DRTP 合理且可能有效？

**状态：可形成受边界约束的描述性过程证据。**

从 SHA256 已验证的 A/B 最终归档中只读恢复了十个 DRTP seed 的 sampler telemetry、固定 endpoint 条件指标和组定义。新增交付：

- `mechanism_assets_final_ab/DRTP_FINAL_TOPOLOGY_DIFFICULTY_SUMMARY.csv`：A/B 分开的组级名义相对回报缺口、success、timeout、collision、实际 exposure 和最终 `q`；
- `mechanism_assets_final_ab/DRTP_FINAL_Q_ALLOCATION_SUMMARY.csv`：十个 seed 的最终 `q` L1 距离、最大实际 exposure 组和最大最终 `q` 组；
- `figures_v3/Fig3b_topology_group_difficulty_vs_exposure.*`：组级 endpoint difficulty 与训练期实际 exposure 的 A/B 分面描述图。

可支持的写法是：DRTP 在所有十个最终 seed 中均产生非均匀、受约束的训练暴露分配；A/B cohort 内部的困难度—暴露关系总体与 topology-aware allocation 的预期一致，但存在 cohort 与 seed 依赖的差异。

不可支持的写法是：图统计特征已经被完全量化、所有 seed 向同一最难组分配最多样本，或该后验过程分析证明了唯一因果机制。

原因是冻结 sampler manifest 提供 failure-group 与时序语义，却未包含可直接计算的邻接矩阵、边列表或图距离定义。因此，broken-edge、connectivity 和 shortest-path 数值不能由组名虚构。若日后找回精确图定义 artifact，再补 Supplementary Table S1；不应为此启动新训练。

## RQ6：DRTP 是否轻量？

**状态：实际测量被正确阻止，不能填表。**

最终冻结 manifest 指向的 learner 源码与当前工作树不匹配。sampler 与环境文件均精确匹配，但 learner 的 SHA256 不匹配。因此，当前机器上的任何时间、显存或 sampler-overhead 数字都不具备正式可追溯性。

论文中保留 Table 5 占位，并写为：`TBD: exact frozen-source profiler pending`。恢复精确最终确认源代码后，按 `DRTP_RUNTIME_PROFILER_PROTOCOL.md` 在单一匹配硬件上进行固定短窗口三次重复测量；该测量不属于新性能实验，不会改算法或改变主结论。

## 当前终止条件

1. 不对中途或历史停止的 6-UAV run 作正式结论；只等待 fresh restart 的冻结终点。终点完成后，使用 `DRTP_6UAV_FINALIZATION_PROTOCOL.md` 和只读汇总器生成 Fig. 6 及主表所需的 mean、median、lower tail、success、timeout、collision 与 paired delta。
2. Semantic ablation 不是当前投稿证据的前置条件，也不能作为结果驱动补救。若最终源码恢复且资源与 fresh seed 注册表另行冻结，可按 `DRTP_SEMANTIC_ABLATION_PROTOCOL.md` 实施唯一的 full DRTP versus Random-DRTP 机制消融；否则不启动、不补跑、不调参。
3. 主稿可先导入 RQ5 的过程图和边界描述；待 6-UAV 与匹配 profiler 均可追溯时，再填对应的最终图表与表格。
