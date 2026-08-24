# DRTP 静态非均匀对照：决策备忘录（不授权训练）

## 当前结论

正式 UTR--DRTP 五种子实验已证明，在相同 SG backbone、PPO、七个训练组、50% normal anchor、训练预算和共同评估合同下，DRTP 的有界自适应加权相对 UTR 的均匀加权呈现正向的正式 paired 效应。该结论有效且已经进入中文稿。

但这一主消融只隔离了 **uniform weighting vs adaptive weighting**。它没有单独排除另一种解释：某个静态非均匀的六组暴露比例，可能也能带来部分或全部收益。因此，不能把当前结果写成“动态反馈本身已被唯一证明为必要”。

## 唯一建议的可选高价值补实验

未来若单独授权，训练一个 **SNR-SG-MAPPO（static-nonuniform reweighting）** 控制方法：

- 与 UTR/DRTP 使用完全相同的 116,728 参数 SG actor/critic、PPO、环境、奖励、故障语义、actor information boundary、七组定义和 50% normal anchor；
- 六个故障组权重必须在训练前固定，训练期间不可由 return、EMA、difficulty、checkpoint 或评价表现更新；
- 权重的构造必须不依赖正式 2301–2305 最终 DRTP 的 q 轨迹、最终回报或任何结果导向选择；
- 必须使用全新、训练前冻结的 paired seeds、严格连续共同预算及最终 checkpoint；
- UTR、SNR、DRTP 必须同预算、同评价样本带，并保留全部 seed；
- 主要问题限于：DRTP 相对 SNR 的差异是否支持动态自适应重加权的额外价值。

## 禁止的捷径

- 不得把正式最终 q 均值直接复制为“静态最优”权重；
- 不得根据主结果挑选静态分布或针对某一 seed 调整权重；
- 不得用旧 checkpoint 再训练或补跑为正式对照；
- 不得用一个低预算 pilot 替代同预算主比较；
- 不得将该备忘录理解为已授权训练。

## 当前状态与下一步

中文稿的术语、逐种子安全性和可复现性整改已完成。作者随后授权冻结该机制对照的**训练前合同**，见 `docs/DRTP_STATIC_NONUNIFORM_COMPARATOR_PRETRAINING_CONTRACT.md`；该合同以不依赖历史结果的结构严重度规则定义 SNR 静态权重，并仍明确标记为 **NO TRAINING STARTED**。

是否承担三方法、五种子、共同 10M 的实际训练成本，仍须由作者针对该独立合同单独启动；这不影响当前 UTR--DRTP 主消融的有效性，但会决定能否把“动态反馈”的归因进一步加强。
