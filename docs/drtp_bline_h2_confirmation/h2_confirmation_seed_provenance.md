# H2 confirmation seed provenance audit

候选连续 seed 为 2801–2805。对工作区的源代码、配置、文档、诊断、结果路径、
归档文件名、manifest、checkpoint 名、命令行文本以及可达 Git 历史进行了 seed
语义检索（`seed280x`、`--seed 280x`、JSON `"seed":280x`）。

在冻结前未发现这些 seed 被用于 scientific training、开发/正式/held-out 评价、
算法或超参数选择、性能驱动调试，或结果查看。它们不是 canonical seed，亦不与
2701–2703 B3 seed 重叠。若云端 pre-flight 发现项目包以外的本地历史资产含有科学
结果记录，必须停止并报告；不得静默替换 seed。
