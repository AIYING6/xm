# 6-UAV v2（fault-step=3）正式证据资格审计

## 审计对象与完整性

- 归档：`D:\File\Downloads\drtp_6uav_v2_faultstep3_results.tar.gz`
- SHA256：`878deacda7fbcb1fb43039ce87a49d8062fad1e59c269fbbf63bab9b73cfedf3`（与伴随 `.sha256` 文件一致）
- 协议：`DRTP-6UAV-CROSS-SCALE-FORMAL-TRAINING-V2-FAULTSTEP3`
- 训练臂：UTR 与 DRTP，各 5 个新训练 seed（69021--69025）
- 训练：每条从零开始，`10,000,128` 环境步、`39,063` 更新；无 resume、early stopping、checkpoint promotion 或训练中评价。
- 评价：每个方法 5 个训练 seed × 7 个组 × 每组 100 episode，共 3,500 episode；总计 7,000 episode。

## 故障触发有效性

`fault_step=3`。对每个方法和训练 seed，6 个非名义组各有 100 个 episode，均记录 `fault_injected=1`；即每条训练 seed 有 600/700 个 episode 注入故障，方法内共 3,000/3,500 个 episode 注入故障。非名义组的 `active_edges_after` 小于 `active_edges_before`，而 nominal 组不注入故障。故障触发的技术前提成立。

## 端点可判别性

尽管故障正确注入，端点不具备可用于跨规模比较的区分度：

| 方法 | 训练 seed | 所有 7 个组的平均 score | success | timeout |
|---|---:|---:|---:|---:|
| UTR | 69021--69025（各 seed） | 2.0 | 1.0 | 0.0 |
| DRTP | 69021--69024（各 seed） | 2.0 | 1.0 | 0.0 |
| DRTP | 69025 | 1.0 | 0.0 | 1.0 |

按训练 seed 汇总，UTR 为 `score=2.0±0.0`、`success=1.0`、`timeout=0.0`；DRTP 为 `score=1.8±0.4472`、`success=0.8`、`timeout=0.2`。前述标准差仅描述五个独立训练 seed 的离散度，不构成额外重复或显著性检验。

## 资格结论

`TECHNICALLY_VALID_BUT_NOT_ADMISSIBLE_FOR_CROSS_SCALE_PERFORMANCE_CLAIM`

该运行纠正了 v1 的晚故障注入问题，却出现 UTR 全条件满分的天花板效应；因此无法检验“改变训练暴露分配是否改善 6-UAV 拓扑退化表现”。DRTP 的一个失败 seed 也排除了将其叙述为支持性跨规模趋势的可能性。

该结果不得进入主文的跨规模性能表、性能图或结论。它可保留在证据审计与补充材料中，作为设计教训：故障注入发生并不自动意味着所选任务端点对方法差异具有足够测量灵敏度。旧 `fault-step=9` v1 仍永久排除，不能与本审计混合。
