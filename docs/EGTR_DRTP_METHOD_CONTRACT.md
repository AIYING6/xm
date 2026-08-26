# EGTR-DRTP-SG-MAPPO 方法合同

**状态：** `P1 FROZEN — P2 PASS — NO TRAINING AUTHORIZED`  
**日期：** 2026-08-26

## 1. 历史边界

当前 scalar-`min` R-DRTP 仅作为已实现、已审计但未进入长训练的 archived design candidate。其 P2 PASS 不转移到 EGTR。EGTR 必须重新执行独立 P2 技术审计。

DRTP 的历史结果、SNR 内部证据、catastrophic seed 和历史 FAIL 结论全部保持不变。EGTR 不得使用历史结果选择公式、阈值、seed 或预算。

## 2. 固定不变项

EGTR 必须保持：

- matched Single-Graph actor/critic，116,728 trainable parameters；
- 原 PPO、critic、learning rate、rollout 和 optimizer；
- S2 environment、reward、failure semantics；
- actor information boundary；
- 七个 topology-condition groups；
- 50% nominal exposure anchor；
- 原 DRTP 的 EMA、difficulty、temperature、smoothing、bounded simplex floor/cap；
- 不新增 encoder、RNN、critic branch、auxiliary loss、reward term 或 policy-side trust region。

EGTR 只允许改变 training-time failure-group sampler update。

## 3. 三层更新定义

更新顺序严格固定为：

\[
\text{window returns}
\rightarrow \text{return EMA}
\rightarrow \text{robust gap reliability}
\rightarrow \text{confidence EMA}
\rightarrow d_k
\rightarrow q^E
\rightarrow q^A
\rightarrow \Pi_{\mathcal Q}
\rightarrow \text{L1 trust region}.
\]

### 3.1 Evidence gate

对 nominal 与每个 failure group 的当前窗口完成回报定义：

\[
m_{N,u}=\operatorname{median}(Y_{N,u}),\qquad
m_{k,u}=\operatorname{median}(Y_{k,u}),
\]

\[
s_{g,u}=\frac{1.4826\operatorname{MAD}(Y_{g,u})}
{\sqrt{\max(n_{g,u},1)}}.
\]

正向 nominal-relative deficit：

\[
g_{k,u}=\max(m_{N,u}-m_{k,u},0).
\]

样本充分性：

\[
a_{k,u}=\min(1,n_{N,u}/8)\min(1,n_{k,u}/8).
\]

单窗口 evidence：

\[
r_{k,u}=a_{k,u}
\frac{g_{k,u}}
{g_{k,u}+\sqrt{s_{N,u}^2+s_{k,u}^2}+10^{-8}}.
\]

若某 failure group 当前窗口没有完成样本，则该组 `r_{k,u}=0`，并将其 stale duration 作为 telemetry；不得额外引入 stale penalty。

confidence EMA 固定为：

\[
\bar r_{k,u}=0.8\bar r_{k,u-1}+0.2r_{k,u}.
\]

### 3.2 Adaptive target

沿用原 DRTP difficulty `d_{k,u}`，但只使用可靠 difficulty signal：

\[
h_{k,u}=\bar r_{k,u}d_{k,u},qquad
\tilde h_{k,u}=h_{k,u}-\frac16\sum_jh_{j,u}.
\]

\[
q^E_{k,u+1}=\frac{q_{k,u}\exp(\eta\tilde h_{k,u})}
{\sum_jq_{j,u}\exp(\eta\tilde h_{j,u})}.
\]

总体 evidence：

\[
\rho_u=\frac16\sum_k\bar r_{k,u},qquad
q^A_{u+1}=(1-\rho_u)q^{uniform}+\rho_u q^E_{u+1}.
\]

保留原 DRTP inertia：

\[
z_{u+1}=(1-\beta)q_u+\beta q^A_{u+1}.
\]

### 3.3 Bounded simplex 与 L1 trust region

先得到可行目标：

\[
q^*_{u+1}=\Pi_{\mathcal Q}(z_{u+1}),
\qquad
\mathcal Q=\{q:\sum_kq_k=1,\ 0.05\le q_k\le0.35\}.
\]

再施加唯一新增 sampler hyperparameter：

\[
\delta_q=0.10.
\]

\[
D_u=\lVert q^*_{u+1}-q_u\rVert_1,qquad
\gamma_u=\min\left(1,\frac{0.10}{D_u+10^{-8}}\right),
\]

\[
q_{u+1}=q_u+\gamma_u(q^*_{u+1}-q_u).
\]

trust region 必须放在最终 bounded-simplex projection 之后。由于 `q_u` 和 `q*` 都属于凸集，最终 q 自动保持 floor、cap 和总质量；同时严格满足：

\[
\lVert q_{u+1}-q_u\rVert_1\le0.10.
\]

## 4. 必须持久化的状态

checkpoint 必须保存：

- q、原 DRTP EMA/difficulty；
- 六个 confidence EMA；
- 当前 adaptation index 与 update；
- 当前 window 每组 raw completed returns；
- 每组 sample count 与 stale duration；
- warm-up、smoothing 和 sampler state；
- 所有既有 runtime/RNG/environment state。

只保存 count 不足以恢复 median/MAD，因此 raw window returns 必须持久化。

## 5. 必须记录的 telemetry

每个 adaptation boundary 至少记录：

- `n_N`、`n_k`、`m_N`、`m_k`、`s_N`、`s_k`；
- `g_k`、`r_k`、`confidence_ema_k`；
- `d_k`、`h_k`、`rho`；
- `q_uniform`、`q_E`、`q_A`、`q_star`、最终 q；
- `|q_u-q_uniform|_1`；
- `|q_{u+1}-q_u|_1`；
- trust-region active flag/fraction；
- stale duration、实际 episode exposure、nominal anchor exposure。

## 6. 当前停止条件

本合同只冻结 EGTR 方法定义，不授权实现后的长训练。必须先完成新的 P2 audit。未经单独授权，不得生成 development tape、使用新 seeds、启动 1M/3M/10M、held-out 或 canonical 实验。
