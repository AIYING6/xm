# TGTR-PPO 数学合同（P0 冻结草案）

## 1. 名称与对象

**Topology-Group Trust-Region PPO (TGTR-PPO)**：固定拓扑曝光、ordinary-PPO anchored、逐 topology-group 约束的单模型 actor update。

组集合为

\[
\mathcal G=\{N,F0,TE,TL,DS,DL,CP\}.
\]

critic、GAE、reward、actor observation、图网络与部署接口均保持 matched Sync-UTR 不变。约束只作用于 actor update。

## 2. 固定采集合同

每次 update 由 24 条固定 stream 构成：12 条 nominal；每个 failure group 两条。每条 64 steps，所以每次 update 有 1536 graphs，组质量为 0.5 nominal 与每个 failure group 1/12。

每个 failure group 的两条 stream 在训练前固定为 design stream 与 certificate stream。nominal 的 12 条 stream 固定分为 6/6。组标签和 split 仅是 training-only metadata，不进入 actor/critic observation。

## 3. Ordinary PPO anchor

令旧策略为 \(\pi_{\theta}\)，ordinary Sync-UTR PPO 在同一 design batch 上产生候选 actor displacement \(d_{\mathrm{ppo}}\)。它是默认高收益方向，不因为某个 difficulty score 而改变。

对每个组 \(g\)，定义 design split 上的 clipped actor surrogate ascent gradient

\[
g_g=\nabla_{\theta} S_g^{D}(\theta),
\]

其中 advantage 仍按 matched PPO 的全 batch 规则归一化。不得使用 evaluation return、最终 seed 标签或未来 trajectory。

## 4. 最小修正问题

先在 design split 上评估 ordinary candidate。若所有组均无可检测的负局部变化，且逐组 KL 合法，则 \(d=d_{\mathrm{ppo}}\)。否则只把 design split 中受伤组放入 active set \(\mathcal A\)，求解：

\[
\begin{aligned}
d^*=\arg\min_d\quad &\frac12\|d-d_{\mathrm{ppo}}\|_2^2\\
\mathrm{s.t.}\quad &g_N^\top d\ge 0,\\
&g_g^\top d\ge 0,\quad g\in\mathcal A,\\
&\bar g^\top d\ge 0,
\end{aligned}
\]

其中 \(\bar g=\tfrac12g_N+\tfrac1{12}\sum_{g\ne N}g_g\) 对应冻结的 UTR 质量。零方向总是可行；目标确保修正是相对 ordinary PPO 的最小改变，而不是另起一个 worst-group optimizer。

高维参数不需要进入通用大规模 QP。最优修正在 active gradients 张成的至多 8 维空间中求解；P0 的 synthetic audit 验证了该投影问题的可行性和非扩张性质。

## 5. Certificate split 与实际策略约束

候选参数 \(\theta'=\theta+d^*\) 不立即提交 Adam state。先在未参与 active-set 识别和 QP 求解的 certificate streams 上计算：

1. 每组 clipped surrogate change；
2. nominal 与 pooled-failure surrogate change；
3. 每组完整 categorical distribution 的
   \(D_{KL}(\pi_{\theta}\|\pi_{\theta'})\)，不是只用 sampled action 的近似 KL；
4. finite 参数、logit 与 optimizer transaction。

固定 KL 上界由已有 PPO clip \(\epsilon=0.2\) 推导，不另做 sweep：

\[
\delta_{KL}=-\epsilon-\log(1-\epsilon)=0.02314355\ldots
\]

certificate 规则为：

- nominal 的 held-stream mean surrogate change 不得为负；
- pooled failure 必须非负，且任何单独 failure group 的 held-stream mean surrogate change 不得为负；
- 每组 mean full-categorical KL 不得超过 \(\delta_{KL}\)；
- 所有数值必须 finite。

这是确定性的 held-stream 一致性检查，不把同一轨迹中的时间点误称为独立统计样本，不报告 p 值或置信区间，也不构成单调 return 保证。它可能偏保守，因此 zero-step rate 是 C1 的硬否决项。

## 6. 固定 backtracking 与事务语义

若 full step 不通过 certificate，只允许依次检查

\[
\alpha\in\{1,1/2,1/4,1/8,1/16,1/32,1/64\},\quad
\theta'=\theta+\alpha d^*.
\]

接受第一个通过的最大 \(\alpha\)。若全部失败，本 actor epoch 不提交；critic 仍执行 matched ordinary PPO update。actor 参数与对应 Adam state 必须保持进入该 epoch 前完全一致。

这不是 performance gate，也不使用未来结果。它是每次 actor optimizer transaction 的内部合法性检查。

## 7. 为什么它不是历史方法的重复

- 相比 TCR：从 2 个聚合梯度扩展到具体受伤组，并约束实际 group policy distribution；不以负 cosine 作为充分触发条件。
- 相比 group-weighted PPO：不持续改变 group loss 权重；ordinary update 合法时完全保留。
- 相比 KLR：不把 global KL 超阈值直接等同于坏 update；先做最小修正，再用独立 streams 检查逐组 full KL 和 surrogate。
- 相比 EGTR：组曝光固定，return/difficulty 不控制采样。

## 8. 当前未获授权内容

P0 不授权实现正式算法、不授权 rollout、不授权 PPO update、不授权 fresh-seed pilot，也不授权任何 0.5M/1M/10M 训练。
