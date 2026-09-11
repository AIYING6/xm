# DRTP 证据保留清单（2026-09-11）

## 目的与边界

本清单用于将当前 DRTP 论文可追溯证据与历史开发材料分开管理。它只登记已经核验的归档；不把早期探索、旧协议或未核验材料升级为正式结论。除非后续有独立的报告—合同核对，本清单不对任何数值或论文主张作新的解释。

## 一级：论文主证据，必须保留

| 资产 | 本地位置 | SHA-256 | 已核验内容 | 保留理由 |
|---|---|---|---|---|
| 最终正式 A 队列 | `D:\\File\\MyFile\\Temp\\drtp_stabilization_A_complete_results.tar.gz` | `429f13444c4ed10327abd62a13a0d9bf8ee737cedb6b6448353fd9087bcb275f` | 冻结配置、种子清单、10M 端点评估、逐 seed 端点、配对差与重汇总报告 | UTR–DRTP 的正式 A 队列证据 |
| 最终正式 B 队列 | `D:\\File\\MyFile\\Temp\\drtp_stabilization_B_complete_results.tar.gz` | `d5c4adbe4f0004f0f415ba38e2b03232c55cb46c7d5dc7c7b1031eef7c1eef73` | 冻结配置、独立种子、10M 端点评估、逐 seed 端点、配对差与重汇总报告 | A 队列的独立确认 |
| 固定端点 held-out/OOD | `D:\\File\\MyFile\\Temp\\drtp_final_evidence_heldout_ood_results.tar.gz` | `68ae5c54da53b64f0ac3e8ecba909f9cd5af38920b16543be777b570eef0bf1` | A/B 冻结输入、评估 manifest、逐 seed 端点、cohort 汇总和配对差 | 正式端点的 held-out/OOD 支持证据；具体 OOD 定性仍以训练支持审计为准 |
| PLR-style 外部定位 | `D:\\File\\MyFile\\Temp\\drtp_plr_matched_ab_results.tar.gz` | `a9ce5eeb977bfe024f98277d69e443e06bb8b59b60403ed277442f218da965f4` | A/B 各自 tape、PLR 训练清单、端点评估、逐 seed/配对/cohort 报告 | 外部参考定位；不能取代 UTR–DRTP 的受控主比较 |

## 二级：有效支持/机制与跨规模材料，必须保留但不可替代主证据

| 资产 | 本地位置 | SHA-256 | 已核验内容 | 使用边界 |
|---|---|---|---|---|
| 6-UAV v2（fault-step=3） | `D:\\File\\MyFile\\Temp\\drtp_6uav_v2_faultstep3_results.tar.gz` | `878deacda7fbcb1fb43039ce87a49d8062fad1e59c269fbbf63bab9b73cfedf3` | 10 个训练 run manifest、固定端点评估、最终报告与完成标记 | 仅此修复故障时序版本可作为 6-UAV 材料；旧 fault-step=9 版本永久不用于论文结果 |
| 非配对机制消融 | `D:\\File\\MyFile\\Temp\\drtp_semantic_ablation_nonpaired_10m_results.tar.gz` | `f088e5aae92c695d5acabdfb703fe49e0dda82b55c3f2be407c773d652b86ce9` | preflight、10M endpoint、机制端点和完成标记 | 机制敏感性证据，不单独证明语义或自适应分量的必要性 |
| 全因子补全消融 | `D:\\File\\MyFile\\Temp\\drtp_semantic_ablation_factorial_completion_10m_results.tar.gz` | `2675bb25040386aea504c79ebed748b77534ce453df51614f1344a0cdaE9EDEE` | 端点评估、全因子补全报告与完成标记 | 保留为消融结果的完整来源；论文解释须按报告和统计重算收口 |

> 注：哈希在后续机器可统一转为小写；哈希匹配不受大小写影响。

## 三级：历史/旧协议材料，只归档，不得作为当前主结论

- `D:\\File\\MyFile\\Temp\\backup\\drtp_heldout_v2_results.tar.gz`：SHA-256 `fcfd308fe84bb5214c6adc7cad98a562d7e1df86497bebde6e8b57f78acc7949`。与当前正式 held-out/OOD 包不是同一文件，保留作历史审计，不进入主表。
- 任何 6-UAV `fault-step=9` 运行：故障注入发生在 episode 完成后，故不作为性能证据；仅保留其 Q0/失效诊断报告。
- 早期开发 cohort、EGTR/GA-EGTR 等探索线以及中途 repair 包：只保留其冻结合同、最终报告和必要的复现实物；不得混入 A/B 正式统计单位。

## 清理执行规则

1. 上表的归档及其对应 `.sha256` 文件不得删除、覆盖或以“重复”名义替换。
2. `.audit_*` 目录不接受文件名自动判定；必须先链接到上述资产或确认其为可再生缓存。
3. 其他大文件先执行内容哈希去重；只有相同 SHA-256 且至少保留一个已登记副本时，才可以进入删除清单。
4. 删除清单应逐路径列出，并在执行前再次征得用户确认。

## 已执行的仓库内归档（不改变证据等级）

- 原仓库根目录下的 171 个未跟踪历史云端包及其校验文件，已移至
  `archival/cloud_packages/legacy_20260911/`。这些是可重放或历史阶段包，
  不替代上表列出的正式结果归档。
- 原 `tmp/` 工作区（约 6.18 GiB）已整体移至
  `archival/workspaces/20260911_tmp_workspaces/`。其内容保留供历史审计；
  历史文档中出现的旧 `tmp/` 路径应被理解为该归档位置的前身，不能据此把
  对应结果升级为当前正式证据。
- `output/drtp_relay_failure_anonymous_reproducibility_v1` 至 `v9`（合计约
  3.56 GiB）已移至
  `archival/paper_outputs/retired_reproducibility_20260911/`。这些包使用
  退役的 2301–2405 cohort，只作为历史论文输出保留，不得和最终 A/B cohort
  的论文表格或统计单位混用。
