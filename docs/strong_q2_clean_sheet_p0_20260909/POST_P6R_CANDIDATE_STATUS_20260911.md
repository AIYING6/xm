# P6R 停止后的候选状态（2026-09-11）

## 结论

当前不应把任何已有候选冻结为“强二区算法主线”。这不是缺少训练预算，而是截至目前没有一条候选同时满足：可识别的决策冲突、非退化的容量匹配基线、可分离的算法干预，以及未被近邻工作直接覆盖。

P35/P35B 已因容量反事实不承重而停止；P6R 已因唯一响应专门化不成立而停止。二者均未进入 PPO 训练。先前的候选重排文件将 P35 列为 Tier A，现已过时，不可再据此启动工作。

## A0 的更新定位

`A0_OC_MAPPO` 是现有资产中**最接近可完成 Q2 闭环**的一条：其观测几何、执行信息边界、MAPPO 学习门、真实边际量、shuffle 与 zero 消融都已预先定义，工程风险低。

但它不能自动成为强二区算法题：

1. 多 UAV 主动感知、概率估计驱动的协同控制已是成熟问题；
2. 以个体边际贡献改善团队学习信号直接邻接 difference rewards、COMA 与反事实信用分配；
3. 因而“使用 log-det 边际量重加优势”本身不足以支撑宽泛算法创新主张。

它最多可作为一个**条件性 Q2 备选**。只有在下一份机制差异合同能证明下列命题时才允许做开发性训练：

> 公开 belief 下的量测互补性归因，能区分一般回报反事实无法区分的、由几何冗余导致的协同行为误配；并且这种差异可由真实边际量、保分布 shuffle 与容量匹配 COMA/difference-reward 参考分离。

如果这一命题不能成立，A0 也应停止，而不是把它包装成“新信用分配算法”。

## 不允许的错误下一步

- 不因 P6R 停止而直接租卡训练 A0；
- 不重启 P35/P35B 或 P6R 并调整阈值、成本或响应库使其通过；
- 不将旧 OSTA、DRTP 或历史 UAV 实验迁移为 A0/P6R 的证据；
- 不以“UAV 应用”“图网络”“GRU”或额外奖励项制造表面差异。

## 唯一推荐下一步

对 A0 做一份**近邻机制差异与主比较合同**，而不是启动训练。合同必须逐项对比：

| 对比对象 | A0 必须能排除的解释 |
|---|---|
| 团队回报 MAPPO | 不是单纯多加一个估计奖励 |
| COMA / difference reward | 不是一般动作反事实或默认动作差分 |
| 公开 belief 的一般信息增益奖励 | 不是把总不确定性降低重新分摊给 agent |
| 图/循环表示增强 | 不是额外表达能力造成的收益 |

该合同若通过，才可执行已冻结的 `OC-MAPPO / Shuffled-OC / Zero-OC` 开发门；若不通过，现有候选池应正式清空，转为基于成熟公开基准的新选题发现，而不是继续在当前资产中改名。

## 证据与检索边界

本决定基于本地 A0 合同与学习门，以及多源检索到的 COMA、反事实信用分配和多 UAV 主动感知近邻。检索用于限制主张，不构成对全部文献的穷尽证明。

可核验来源：

- `docs/strong_q2_clean_sheet_p0_20260909/A0_OBSERVABILITY_ACTIVE_PERCEPTION_CANDIDATE_20260911.md`
- `docs/strong_q2_clean_sheet_p0_20260909/A0_OC_MAPPO_METHOD_AND_ABLATION_CONTRACT_20260911.md`
- `docs/strong_q2_clean_sheet_p0_20260909/A0_PLAIN_MAPPO_LEARNABILITY_RESULT_20260911.md`
- `docs/strong_q2_clean_sheet_p0_20260909/P35B_DECISION_SWITCHING_VERIFICATION_NOVELTY_CONTRACT_20260911.md`
- `docs/strong_q2_clean_sheet_p0_20260909/P6R_RESPONSE_INDUCED_OPEN_TEAM_CANDIDATE_20260911.md`
