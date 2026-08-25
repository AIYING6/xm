# 中文投稿稿（Q2 证据链版）

**当前路线：** `PAPER_ROUTE_B — topology reconfiguration and training reliability study`。主结果以 seeds 2401–2405 的 UTR/SNR/DRTP 前瞻性受控比较为准；历史 DRTP 高收益与反向 seed 均作为可靠性证据保留，不能跨合同混合为算法排名。写作前先遵守 [术语与主张边界](00_术语与主张边界.md) 与 [Post-SNR 路线审计](../../docs/PAPER_Q2_POST_SNR_ROUTE_RECONSTRUCTION_AUDIT.md)。

本目录是面向中文投稿的修订稿，依据 `paper/q2_draft/` 的现有证据和冻结 provenance 重组，并吸收 `D:\File\Downloads\论文初稿_v1.14_最终实验与投稿审计_20260820.pdf` 中的结构优点。

## 使用边界

- 只使用当前 DRTP 证据链中的数据，不使用参考 PDF 的数据或结论。
- development 与 held-out 合同分开呈现。
- 保留 development NO-GO、held-out FAIL、seed1902 限制和 seed2002 反转。
- 不把 DRTP 写成稳定、普遍优越或具有一般鲁棒性保证的方法。
- SNR 已进入已核验的前瞻性主结果；DRTP/SNR 均不得写作已被验证的可靠主算法。

## 推荐组稿顺序

摘要 → 引言 → 相关研究 → 问题与范围 → 方法 → 实验合同 → 绝对结果 → 配对 seed 效应 → OOD/安全/机制 → 讨论与局限 → 数据与代码可用性 → 结论。

英文 `paper/q2_draft/` 保留为术语和公式对照源；中文投稿正文以本目录为准。
