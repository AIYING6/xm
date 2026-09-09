# CEC-MAPPO 数学与因果对照冻结 V1

## 1. 问题变量

对智能体 (i)，执行期可用信息仅为合法本地历史

\[
h_{i,t}=(o_{i,0},a_{i,0},\ldots,o_{i,t}),
\]

其中包含本地发送/接收事件、计划与 ACK 版本、消息年龄、公开链路上下文和剩余任务窗口。
evaluator 的全局交付真值不得进入 actor、critic 或执行期一致性估计器。

令潜在一致性状态

\[
z_t\in\mathcal Z=\{z^{\rm joint},z^{\rm unconfirmed},z^{\rm absent},z^{\rm stale}\},
\]

分别表示当前计划已共同可执行、计划已接收但 ACK 未确认、计划未共享和共享计划过期。

## 2. 校准一致性集合

估计器 (f_\phi(h_{i,t})) 输出 (p_\phi(z\mid h_{i,t}))。以

\[
s_\phi(h,z)=1-p_\phi(z\mid h)
\]

作为 nonconformity score。在与优化轨迹隔离的 calibration split 上，按公开链路上下文与紧迫度
进行 Mondrian 分组，冻结 (1-\alpha=0.9) 分位阈值 (q_{1-\alpha,g})，得到

\[
\Gamma_{i,t}=\{z\in\mathcal Z:s_\phi(h_{i,t},z)\le q_{1-\alpha,g(t)}\}.
\]

经验论文只能报告实际 marginal/分组覆盖率，不能在不满足交换性或样本量条件时写成普遍保证。

## 3. 状态条件期权价值

对高层动作 (m\in\{\mathrm{commit},\mathrm{defer},\mathrm{fallback}\})，学习

\[
Q_\psi(h_{i,t},m,z)=\mathbb E[G_t\mid h_{i,t},m,z].
\]

`defer` 的回报必须包含后续新本地证据到达后再选择 commit 或 fallback 的真实闭环收益，不能
用固定等待奖励代替。集合内 posterior 重新归一化后，期望期权价值为

\[
\bar Q(m)=\sum_{z\in\Gamma_{i,t}}\tilde p_\phi(z\mid h_{i,t})Q_\psi(h_{i,t},m,z),
\]

支持集下行值为

\[
\underline Q(m)=\min_{z\in\Gamma_{i,t}}Q_\psi(h_{i,t},m,z).
\]

## 4. 认知承诺门

立即承诺只有在以下两个条件同时满足时才可行：

\[
\underline Q(\mathrm{commit})\ge \underline Q(\mathrm{fallback}),
\qquad
\widehat P_\phi(\mathrm{unsupported}\mid h_{i,t},\mathrm{commit})\le\epsilon,
\]

其中 (epsilon=0.1) 在任何性能结果产生前冻结。`defer` 与 `fallback` 始终可行。最终动作在
可行集合 (mathcal A^{\rm adm}_{i,t}) 上按

\[
m^*_{i,t}=\arg\max_{m\in\mathcal A^{\rm adm}_{i,t}}\bar Q(m)
\]

选择。该规则在 Q0B 的 ACK 前状态排除危险 commit，并因 defer 的期望期权价值 8 高于
fallback 的 3 而选择 defer；ACK 到达后集合收缩，commit 重新变为可行。它不是 pure maximin。

## 5. MAPPO 训练

环境动作、PPO clipped objective、集中价值损失和执行接口保持不变。门控后的分类策略为

\[
\pi^{\rm gate}_\theta(m\mid h)\propto
\pi_\theta(m\mid h)\mathbf 1[m\in\mathcal A^{\rm adm}(h)].
\]

总训练目标由标准 PPO actor loss、critic loss、熵正则和一致性估计辅助损失组成。为避免额外
监督成为替代解释，四个 factorial cell 都训练容量匹配、与 actor encoder 分离的一致性估计器，
都接收完全相同的训练期标签；区别只在估计器输出是否进入 actor，以及承诺门是否生效。

## 6. 四格关闭规则

| 方法 | set 输入 actor | gate | 其他训练监督 |
|---|---:|---:|---|
| Recurrent MAPPO | 否 | 否 | 与其余方法相同的 detached 辅助估计器 |
| Point-belief Commitment | 否 | point posterior gate | 相同 |
| Information-set Direct | 是 | 否 | 相同 |
| CEC-MAPPO | 是 | support-aware gate | 相同 |

参数容量差异必须通过匹配的 inactive adapter 控制在冻结容差内；PPO、优化器、episode tape、
训练 cell、物理步数和评估端点完全相同。

## 7. 预先规定的证伪条件

- 校准集合在冻结 calibration test 上达不到目标覆盖：set 模块失败，不进入性能训练；
- Q0B 上 full gate 不能完成 `defer -> commit/fallback` 的方向切换：实现失败；
- Point-gate 与 CEC-MAPPO 相当：不能主张 set representation 必要；
- Set-direct 与 CEC-MAPPO 相当：不能主张 commitment gate 必要；
- CEC-MAPPO 与 recurrent MAPPO 相当：冻结任务内不存在经验增量价值；
- 得分改善但 unsupported commit 增加：只报告收益—可靠性权衡。

该冻结定义解决“实验以后才决定方法到底是什么”的问题。下一步只允许实现四格模块和零训练
单元审计，不允许启动 Q1。
