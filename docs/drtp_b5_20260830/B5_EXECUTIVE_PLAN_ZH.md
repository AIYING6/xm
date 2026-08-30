# B 线后续执行方案（B5）

## 当前判断

原始 DRTP 的高收益能力是真实存在的，但截至目前没有一个稳定化版本同时跨独立 cohort 保住高收益和下尾可靠性。TR、uniform anchor、KL rollback/backtracking、paired probe 与 population selector 均已提供有效反例，因此不再做参数微调或第三个局部补丁。

## 已完成

- 对 10 份关键结果包完成 SHA256、内部裁决文件和决策一致性审计；
- 建立跨 cohort 的干预—分叉—结果证据矩阵；
- 冻结唯一剩余可检验假设：故障组条件下的 credit assignment / gradient interference；
- 保留通用 MAPPO optimization-basin sensitivity 作为零假设；
- 明确本阶段未改算法、未训练、未触碰主线 A。

## 下一阶段门控

1. 先实现只读的 group-conditioned value/advantage/gradient telemetry，并完成 trajectory equivalence、RNG、save/resume 和开销验收。
2. 技术验收通过后，才允许另行人工授权云端 `UTR / Original DRTP × 5 clean paired seeds × 1M` 观测 cohort。
3. 只有完整机制链在至少 2/5 个不利 DRTP seed 中重复、且 paired UTR 不存在同等模式，才允许设计一个最小新算法。
4. 若 1M 仍无完整机制链，B 线算法开发永久停止；不再以新 gate、阈值或 seed 重跑延长项目。
5. 即使 B 线成功或失败，主线 A 的论文证据和投稿时间表均保持独立。
