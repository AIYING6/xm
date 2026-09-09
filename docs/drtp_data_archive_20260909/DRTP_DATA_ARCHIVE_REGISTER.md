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

原文件未移动、未覆盖、未删除。同一 NTFS 卷上的大文件优先使用硬链接，归档路径与原路径指向同一文件内容；删除任一目录项不会删除仍被另一硬链接引用的内容。

## 2. 证据分层

### 2.1 当前正式证据

`01_CURRENT_FORMAL_EVIDENCE` 仅包含当前论文主证据链：

- 最终冻结 A cohort；
- 最终冻结 B cohort；
- structural held-out / training-excluded evaluation；
- PLR matched A/B 外部定位实验。

PLR 数据用于外部性能定位，不替代 UTR–DRTP 的主要受控因果比较。

### 2.2 支撑性机制证据

`02_SUPPORTING_MECHANISM_EVIDENCE` 保存 non-paired 与 factorial completion 消融。它们可以支持“暴露操纵会改变训练分布与结果”的敏感性分析，但不能单独证明拓扑语义与持续自适应分别具有必要性。

### 2.3 排除或无判别力数据

`03_EXCLUDED_OR_NONINFORMATIVE` 保留但禁止纳入当前论文主结论：

- 6-UAV v1：非 nominal 故障未在 episode 完成前有效注入；
- 6-UAV v2 fault-step=3：UTR ceiling，缺乏方法判别力；
- 6-UAV v3.1 UTR pilot：nominal learnability 未通过。

保留这些数据用于审计失败原因，不能与正式证据混合扩充样本量。

### 2.4 开发诊断

`04_DEVELOPMENT_DIAGNOSTICS` 保存 P3B staged pilot 的有效负向校准结果。它属于开发决策证据，不属于当前论文性能确认结果。

### 2.5 历史与安全快照

- `10_HISTORICAL_RESULT_ARCHIVES`：可读的历史结果包，统一标记为非当前正式证据；
- `20_REPRODUCIBILITY_PACKAGES`：去重后的训练、评估和修复执行包，不是实验结果；
- `30_MIXED_EVIDENCE_SNAPSHOTS`：仓库与历史解压目录的安全网快照，收录不等于证据升级；
- `40_EVIDENCE_GOVERNANCE`：冻结合同、审计和 claim-boundary 文件。

任何历史数据升级为论文证据前，必须重新核对方法版本、训练种子、预算、checkpoint、evaluation tape、故障触发有效性和统计单位。

## 3. 完整性验收

构建后的独立验收结果：

- 当前登记数据集：10；
- 当前数据 SHA256：10/10 一致；
- 当前数据原路径：10/10 仍存在；
- 当前数据硬链接身份：10/10 一致；
- 历史结果包：扫描 39，纳入 39；
- 执行/复现包：扫描 180，按内容哈希去重后纳入 123；
- 零字节相关候选：6，明确列入排除清单；
- 总清单记录：13,246；
- 总清单缺失归档目标：0；
- 归档逻辑数据量：66,868,824,461 bytes（硬链接不代表同等新增物理占用）。

前三次因 Python 兼容性或 Windows 路径长度中止的目录已改名为 `D:\File\ZZ_INCOMPLETE_DO_NOT_USE_DRTP_ARCHIVE_ATTEMPT*`，不得使用。唯一有效版本为 `FINAL_V3`。

## 4. 后续使用规则

1. 论文统计首先读取 `CURRENT_EVIDENCE_REGISTER.csv`，不得从历史目录按文件名猜测正式性。
2. 训练种子是独立统计单位；episode 与 condition 不得充当独立训练重复。
3. 当前正式、支撑性、开发诊断、排除性和历史数据不得合并扩大样本量。
4. 新数据进入归档时应生成新版本目录，不覆盖 `FINAL_V3`，并更新登记、来源与 SHA256。
5. 对外发布前仍需完成匿名化、许可审查、仓库选择与正式 Data Availability 声明。
