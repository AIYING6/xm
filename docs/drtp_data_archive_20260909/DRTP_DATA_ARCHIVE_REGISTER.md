# DRTP 实验数据归档登记（2026-09-09）

## 1. 唯一有效归档入口

- 归档根目录：`D:\File\DRTP_RESEARCH_DATA_ARCHIVE_20260909_FINAL_V3`
- 构建脚本：`scripts/archive_drtp_research_data_20260909.py`
- 总清单：`00_INDEX/MASTER_FILE_MANIFEST.csv`
- 当前证据登记：`00_INDEX/CURRENT_EVIDENCE_REGISTER.csv`
- 当前证据哈希：`00_INDEX/SHA256SUMS_CURRENT_EVIDENCE.txt`
- 历史结果审计：`00_INDEX/HISTORICAL_ARCHIVE_AUDIT.csv`
- 执行包审计：`00_INDEX/REPRODUCIBILITY_PACKAGE_AUDIT.csv`
- 零字节候选：`00_INDEX/ZERO_LENGTH_CANDIDATES.csv`
- 构建报告：`00_INDEX/ARCHIVE_BUILD_REPORT.json`

归档以非破坏方式从以下三个位置建立：

1. `D:\File\Downloads`
2. `D:\File\MyFile\Temp`
3. `D:\Code\Codex\ri_gmappo_uav`

最终收口后，`Downloads` 仅恢复并保留 6 组有效论文数据及其校验文件；无效实验没有恢复。`Temp` 与仓库原始结果未在本次清理中修改。同一 NTFS 卷上的大文件使用硬链接，归档路径与 `Downloads` 保留路径指向同一文件内容。

## 2. 论文收口归档内容

### 2.1 当前正式证据

`01_CURRENT_FORMAL_EVIDENCE` 仅包含当前论文主证据链：

- 最终冻结 A cohort；
- 最终冻结 B cohort；
- structural held-out / training-excluded evaluation；
- PLR matched A/B 外部定位实验。

PLR 数据用于外部性能定位，不替代 UTR–DRTP 的主要受控因果比较。

### 2.2 支撑性机制证据

`02_SUPPORTING_MECHANISM_EVIDENCE` 保存 non-paired 与 factorial completion 消融。它们可以支持“暴露操纵会改变训练分布与结果”的敏感性分析，但不能单独证明拓扑语义与持续自适应分别具有必要性。

### 2.3 已从收口归档删除的数据

下列数据已从收口归档删除，并且没有恢复到已清空的 `Downloads`；`Temp` 与仓库中的其他历史来源未在本次清理中继续处理：

- 6-UAV v1：非 nominal 故障未在 episode 完成前有效注入；
- 6-UAV v2 fault-step=3：UTR ceiling，缺乏方法判别力；
- 6-UAV v3.1 UTR pilot：nominal learnability 未通过。

这些实验不能与正式证据混合扩充样本量。

### 2.4 已删除的开发诊断

P3B staged pilot 属于新支线开发决策证据，不属于当前 DRTP 论文性能确认结果，已从收口归档删除。

### 2.5 复现与治理材料

- `20_REPRODUCIBILITY_PACKAGES`：仅保留 7 个直接对应 A/B、held-out 和消融的训练、评估或修复包；
- `40_EVIDENCE_GOVERNANCE`：仅保留 21 个当前冻结合同、公平性审计和 claim-boundary 文件。

历史结果、安全快照、无关执行包和旧支线治理文件已从收口归档删除。

任何历史数据升级为论文证据前，必须重新核对方法版本、训练种子、预算、checkpoint、evaluation tape、故障触发有效性和统计单位。

## 3. 完整性验收

构建后的独立验收结果：

- 当前保留数据集：6；
- 当前数据 SHA256：6/6 一致；
- 当前数据原路径：6/6 仍存在；
- 当前数据硬链接身份：6/6 一致；
- 历史结果包：0；
- 执行/复现包：7；
- 零字节相关候选：6，明确列入排除清单；
- 清理后文件总数：278；
- 总清单缺失归档目标：0；
- 清理后逻辑数据量：约 1.42 GB（硬链接不代表同等新增物理占用）。

前三次因 Python 兼容性或 Windows 路径长度中止的半成品目录均已删除。唯一有效版本为 `FINAL_V3`。

## 4. 后续使用规则

1. 论文统计首先读取 `CURRENT_EVIDENCE_REGISTER.csv`，不得从历史目录按文件名猜测正式性。
2. 训练种子是独立统计单位；episode 与 condition 不得充当独立训练重复。
3. 当前正式、支撑性、开发诊断、排除性和历史数据不得合并扩大样本量。
4. 新数据进入归档时应生成新版本目录，不覆盖 `FINAL_V3`，并更新登记、来源与 SHA256。
5. 对外发布前仍需完成匿名化、许可审查、仓库选择与正式 Data Availability 声明。
