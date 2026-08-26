# 17 审稿风险整改与证据边界记录

## 目的

本记录把主要审稿风险、整改动作、证据来源和仍然存在的边界一一对应。它不改变任何已完成训练、冻结裁决或原始指标。

| 审稿风险 | 整改动作 | 可复查证据 | 仍然保留的边界 |
|---|---|---|---|
| 十个 timing/duration/compound 条件的成员在训练支持集中，不能称严格 OOD | 正文、图表、统计合同统一改称“跨扰动条件”；保留机器字段映射 | `main_zh.md` 第 3.4–3.5、6.4 节；`05_terminology_ledger.md` | 不报告严格未见/OOD/generalization superiority |
| DRTP 名称可能被理解为具有 distributionally robust 或 min--max 理论保证 | 中文全称改为“有界自适应拓扑扰动重加权单图 MAPPO”；方法节明确为经验采样控制器 | `main_zh.md` 第 4.3 节；`09_citation_ledger.md` R11–R12 | 不主张一般 DRO、最坏分布求解或理论收敛 |
| UTR--DRTP 消融是否公平 | 明示共同 backbone、参数量、PPO、训练组、50% normal anchor、预算和评估样本带 | `main_zh.md` 第 1.3、4.1–4.5、5.1 节；正式 run manifests | 该消融隔离“均匀 vs 自适应”加权，不隔离动态自适应与任意静态非均匀分布 |
| 终局回报是否掩盖安全代价或 evaluator defect | 新增可重建的逐种子故障安全/风险集表；所有提前终止 episode 保留 | `formal_results/source_data/formal_failure_safety_by_seed.csv`；`main_zh.md` 第 6.5 节 | 平均超时下降不等价于所有安全端点改善；seed2304 碰撞代价保留 |
| 小样本及训练种子可靠性 | 以 training seed 为唯一独立单位；主文报告所有五个 paired seed、mean/median/SD/IQR/MAD/worst；历史 adverse seeds 单独分层 | `formal_results/source_data/paired_seed_results.csv`；`main_zh.md` 第 5.3–5.5、6.3、6.7 节 | n=5 仅支持任务有界的描述性 paired evidence，不支持普适稳定性 |
| 结果是否来自中间 checkpoint 选择或事后排除 | 固定最终 10M checkpoint；附录记录合同、hash、tape、禁止项与原始记录数 | `main_zh.md` 附录B；`14_formal_result_integration_audit.md` | 尚未完成公开代码/数据仓库发布，投稿时需由作者补充地址 |
| 外部 baseline 缺失 | 正文解释外部方法在动作、信息和学习合同上的不可直接比较，而不把它们写成已被击败基线 | `main_zh.md` 第 2.4、7.5 节；外部对照审计 | 当前主结论是内部参数匹配主消融，不是算法排行榜 |

## 唯一仍可能改变“动态自适应”归因的高价值补实验

若作者未来单独授权并接受完整计算成本，唯一建议的新增训练是 **static-nonuniform topology weighting** 对照：网络、PPO、七组、50% normal anchor、训练种子、10M 预算和评估合同与 UTR/DRTP 完全相同；只使用一个在训练开始前固定、且不依赖正式最终 DRTP 权重或回报的静态六组分布。它回答的是“DRTP 的优势来自动态反馈，还是任意固定非均匀暴露已足够”。

该实验不是当前主文证据的一部分。作者已授权冻结独立的训练前合同（`docs/DRTP_STATIC_NONUNIFORM_COMPARATOR_PRETRAINING_CONTRACT.md`），但尚未生成样本带或启动训练；其结果不得预先写入或改变当前 UTR--DRTP 主文结论。
