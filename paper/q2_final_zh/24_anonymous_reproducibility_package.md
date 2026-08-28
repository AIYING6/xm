# 24 匿名复现包与数据可用性执行清单

**状态：** `PREPARED_FOR_AUTHOR_HOSTING`
**范围：** 本清单只整理现有证据，不运行新训练、不重算 checkpoint、不改变任何训练或评价结果。

## 0. 已完成的本地匿名包构建

本清单现已由 `scripts/build_drtp_anonymous_reproducibility_package.py` 落地为本地匿名审稿 staging package，并由 `scripts/check_drtp_anonymous_reproducibility_package.py` 完整性核验。构建包保留正式 UTR--DRTP 的 12,000 条原始记录、无图 MAPPO 性能参考的 6,000 条原始记录、独立 UTR/SNR/DRTP cohort 的 18,000 条原始记录，以及零训练跨 tape 诊断的 48,000 条原始记录；后者仅作为 cohort-stratified reliability diagnostic，不是新训练证据。包内另含各层 manifest、run provenance、sampler log、合同、代码和图表资产。独立 cohort 仍不得与正式 cohort 合并为 `n=10`。精确命令、归档 SHA256、提取范围和核验条件见文档28。

该状态仅表示“可匿名托管的本地包已生成并自检”；未获得匿名外部链接、许可证和 checkpoint 获取策略前，正文仍不得写为“数据和代码已公开”。

## 1. 投稿前必须完成的两步

1. 作者将本清单对应的文件复制至一个可匿名访问的版本化仓库或数据仓库；匿名审稿阶段使用不暴露作者身份的审稿链接，接收后转换为公开永久记录。
2. 在仓库记录中填写真实的作者、版本、许可证、发布日期、仓库永久标识符（DOI、Handle 或等价标识）和代码版本。以上元数据目前未知，本文档不虚构。

在这两步完成前，主稿只能写“复现包已整理待托管”，不得写“数据和代码已公开”。

## 2. 建议的匿名仓库结构

```text
drtp-relay-failure-reproducibility/
├─ README.md                         # 复现顺序、硬件和许可证说明
├─ CITATION.cff                      # 接收后填写作者和 DOI
├─ LICENSE                           # 由作者选择并确认
├─ contracts/                        # 冻结训练、评价与证据整合合同
├─ configs/                          # 环境、网络、PPO、sampler 配置及哈希
├─ code/                             # 环境、算法、训练、评价、统计和作图脚本
├─ tapes/                            # 490000--490099 与 500000--500099 清单及哈希
├─ source_data/
│  ├─ formal_2301_2305/              # 主 cohort 的 12,000 条记录及汇总
│  ├─ mappo_nograph_2301_2305/       # 无图 MAPPO 性能参考的 6,000 条记录及汇总
│  ├─ independent_2401_2405/         # UTR/SNR/DRTP 18,000 条完整独立重复记录
│  └─ cross_tape_reliability/        # 两 cohort 交叉评价的 48,000 条零训练诊断记录
├─ checkpoints/README.md             # checkpoint/runtime-state 哈希、获取方式与大小
├─ figures/                          # 主图、补充图、矢量源和生成脚本
├─ supplementary/                    # 条件表、安全表、历史 strata 与可靠性说明
└─ manifests/                        # 归档 SHA256、文件 manifest、版本和运行 provenance
```

## 3. 证据到仓库文件的映射

| 论文证据 | 应公开材料 | 当前项目内可核验来源 | 可用性要求 |
|---|---|---|---|
| UTR--DRTP 主因果消融 | 训练/评价合同、tape、12,000 条原始记录、逐条件/逐种子表、统计与作图脚本 | `formal_results/source_data/`、`formal_results/formal_result_tables.md` | 必须完整公开或提供匿名审稿访问 |
| 主 cohort 完整性 | 决策 JSON、tape manifest、正式归档 SHA256、checkpoint/runtime-state 哈希 | `formal_results/source_data/DRTP_UTR_Q2_FORMAL_DECISION.json`、主稿附录B | checkpoint 可受限，但哈希和获取说明必须公开 |
| 无图 MAPPO 性能参考 | 五种子结果、6,000 条记录、安全指标、归档 SHA256 | `formal_results/external_reference_summary.md` | 不得只公开 pooled 结果 |
| 独立三方法反向重复 | UTR/SNR/DRTP 全部 18,000 条记录、三个方法全部种子、端点和安全汇总 | `supplementary/source_data/snr_independent_replication/`、`supplementary/S4_independent_three_arm_replication.md` | 必须整套公开；不得删除不利 seed |
| 跨评价带可靠性诊断 | 两 cohort×两 tape 的 48,000 条 raw records、decision、manifest 和配对汇总 | `results/analysis/drtp_cross_tape_reliability/`、`paper/q2_final_zh/35_cross_tape_reliability_integration_audit.md` | 作为零训练、cohort-stratified diagnostic；不得与 cohort pooling 或新 superiority claim 混用 |
| 方法复现 | 环境、SG 主干、UTR/DRTP sampler、PPO 参数、解析与统计脚本 | `envs/`、`algorithms/`、`configs/`、`scripts/` | 固定到本稿对应 commit；README 给出运行顺序 |
| 图表复现 | SVG/PDF/PNG/TIFF、源数据与作图脚本 | `formal_results/figures/`、`scripts/build_paper_assets.py` | 图号/表号与主稿一致 |

## 4. 固定的版本与完整性标识

| 资产 | 身份/哈希 | 说明 |
|---|---|---|
| 正式 UTR--DRTP 归档 | `cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd` | 种子 2301--2305，主 cohort |
| 正式 evaluation tape | `84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2` | episode ID 490000--490099 |
| 无图 MAPPO 性能参考归档 | `2f8b5f1e3025221e70652a6c4d0bcaa05d239cc81f5c70d59301d4f9e66afad5` | 五种子、共同 10M 终点和主 tape |
| 独立三方法重复归档 | `86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1` | 种子 2401--2405，UTR/SNR/DRTP |
| 独立重复 evaluation tape | `c89f63bc5a11e3def88fa677356796ea681ca227d31e47dc584764a3a3084fc2` | episode ID 500000--500099 |
| 跨 tape 诊断 evaluation tapes | `84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2` / `c89f63bc5a11e3def88fa677356796ea681ca227d31e47dc584764a3a3084fc2` | tape490 与 tape500 交叉使用；raw rows=48,000 |

## 5. README 最低内容

- 说明主稿的三层证据：正式主 cohort、无图 MAPPO 性能参考、独立三方法可靠性重复；明确三层不可合并为 `n=10`。
- 列出 Python、PyTorch、CUDA、GPU、操作系统和关键依赖的实际版本；缺失时用 `requirements` 或环境导出文件补齐，不能凭记忆填写。
- 写明从原始/汇总数据到每张主图、补充图和表格的脚本入口。
- 说明运行完整 10M 训练的成本及只复现评价/图表的低成本路径。
- 将 `J_OOD_mean`/`J_OOD_worst` 的归档字段映射解释为论文中的 `J_pert,mean`/`J_pert,worst`，并明确其不是 strict OOD。
- 明确所有种子、包括历史不利种子和独立 cohort 的反向结果，都保留在数据中。

## 6. 发布前 FAIR 检查

- [ ] 数据仓库已有可解析的永久标识符或匿名审稿链接；
- [ ] 每个文件具有描述性名称、格式、大小和 SHA256；
- [ ] README/数据字典说明列名、单位、缺失值与从 raw metrics 到汇总表的变换；
- [ ] 仓库页面含许可证、版本、关键词、方法摘要及与代码/论文的关联；
- [ ] 主图和表格可追溯到确切 source data 文件；
- [ ] checkpoint 若不公开，仍公开 SHA256、模型 schema、runtime-state schema 和可申请/获取路径；
- [ ] 作者在外部环境中测试匿名链接、下载、checksum 与图表重建；
- [ ] 发表后将匿名链接替换为公开永久链接，并在主稿数据可用性声明中更新 DOI/标识符。

## 7. 可直接使用但尚未填完的投稿声明

**Data Availability（投稿前需替换方括号）：**
`The reproducibility package supporting the formal paired UTR--DRTP cohort, the Non-Graph MAPPO performance reference, and the complete independent three-arm replication cohort will be available to reviewers through an anonymous repository at [anonymous reviewer link]. The package contains frozen contracts, configurations, evaluation-tape manifests, raw episode-level metrics, processed seed-level summaries, figure source data, scripts, and SHA256 manifests. Checkpoint and runtime-state files are [publicly deposited at / available through] [persistent identifier or access route]; their hashes and schemas are included in the package. Upon publication, the package will be released under [licence] at [repository DOI or persistent identifier].`

**中文核对：**
该声明是“已整理、待托管”的准确说法。作者仍需确认匿名仓库地址、正式仓库/DOI、许可证，以及 checkpoint 是否公开和如何获取。
