# H2 early-signature definition

该定义在 2801–2805 结果可见前冻结。其三层阈值、方向和 `≥2/5` 门槛见
`H2_CONFIRMATION_FROZEN_CONTRACT.md`。它检验一个时间顺序的**候选机制**，而非
将高 q 偏离、单个 PPO 指标或最终 return 直接等同于病因。

判据设计保留了 H2 的关键反例：B3 seed2703 在早期有较大 q 偏离但未发生
2702 式统一反转。因此没有 paired UTR 相对行为/支持下降时，任何 q 偏离均为
H2-negative。
