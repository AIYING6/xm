# 投稿 Release Gate（作者动作前置）

**当前状态：** `TECHNICAL_READY_AUTHOR_ACTION_REQUIRED`

本文件将本地已完成的科学证据、可复现资产与投稿前的作者动作分开。它不触发训练、重评估或修改已冻结的 DRTP 结论。

## 1. 已由项目完成并可自动核验

| Gate | 当前证据 | 状态 |
|---|---|---|
| 主文证据链 | `scripts/check_q2_final_zh_manuscript.py` | PASS |
| 三层 cohort 保留 | 主 cohort、无图 MAPPO 性能参考、独立 UTR/SNR/DRTP cohort 均在证据 manifest 中 | PASS |
| 不跨 cohort 合并 | manifest 与主文均禁止将 2301--2305 与 2401--2405 合并为 `n=10` | PASS |
| 主张边界 | claim audit 禁止 strict OOD、一般 DRO、跨 cohort 稳定优越与 adaptive necessity | PASS |
| 中文终稿 PDF | `paper/q2_final_zh/output/DRTP_SG_MAPPO_中文论文终稿_投稿前审稿版.pdf` | PASS |
| 匿名复现包 staging | `output/drtp_relay_failure_anonymous_reproducibility_v1/` 与其 checksum 核验器 | PASS |

## 2. 仍须作者完成，不能由本地代码代替

1. 选择目标中文期刊和文章类型；
2. 创建真实匿名审稿仓库链接，并在外部环境下载、校验与重建；
3. 决定公开许可证、正式公开仓库永久标识符，以及 checkpoint/runtime-state 的访问策略；
4. 填写作者、单位、通讯作者、基金、CRediT 和利益冲突；
5. 依目标期刊模板迁移终稿并完成人工视觉核验。

这些字段应从 `submission_release_metadata.template.json` 复制为一个**不提交到匿名仓库**的本地 metadata 文件后填写。个人信息和匿名链接不应写入公共源码历史。

## 3. 统一核验命令

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe `
  scripts/check_drtp_submission_release_gate.py
```

该命令在当前状态应输出 `TECHNICAL_READY_AUTHOR_ACTION_REQUIRED`：表示科学证据、PDF 与本地匿名包均已就绪，但作者元数据与外部托管尚未完成。

当作者完成外部动作后，传入其私有 metadata 文件并要求完全发布状态：

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe `
  scripts/check_drtp_submission_release_gate.py `
  --release-metadata C:/secure/submission_release_metadata.json `
  --require-author-completion
```

只有这条命令输出 `SUBMISSION_RELEASE_READY`，才可将本稿称为“可提交版本”。

## 4. 明确不做

- 不因该 release gate 新增训练、种子、外部 baseline 或稳定化算法；
- 不删除独立反向 cohort，也不将其与正式 cohort 合并为 `n=10`；
- 不用“本地包已构建”代替真实匿名仓库可访问性；
- 不在未选期刊前伪造模板、作者或 DOI 信息。
