# R-DRTP P2 技术审计合同

**状态：** `IMPLEMENTATION-AUDIT-ONLY / NO TRAINING AUTHORIZED`  
**日期：** 2026-08-26

## 1. 绑定范围

本合同绑定 `R_DRTP_ROUTE_B_PROJECT_PLAN.md` 和 `R_DRTP_STABILITY_MECHANISM_DESIGN_CONTRACT.md`。R-DRTP 只允许改变 failure-group sampler 的更新幅度；SG backbone、116,728 参数、PPO、critic、S2 environment、reward、failure semantics、actor information boundary、七组拓扑集合和 50% nominal anchor 全部不变。

## 2. 预先冻结的可靠性统计量

每个 adaptation window 对每个 failure group `k` 记录已完成 episode returns `Y_{k,u}`。定义：

\[
m_{k,u}=\operatorname{median}(Y_{k,u}),\qquad
v_{k,u}=\min\left(1,\frac{\operatorname{MAD}(Y_{k,u})}{|m_{k,u}|+10^{-8}}\right).
\]

若窗口没有完成样本，则 `v_{k,u}=1` 且该组可信度为 0。否则：

\[
c_{k,u}=\frac{n_{k,u}}{8+n_{k,u}}\exp(-v_{k,u}),
\qquad c_u=\min_k c_{k,u}.
\]

固定常数为：`n_0=8`、`lambda_v=1`、`v_max=1`、`alpha_max=1`。不得根据任何 R-DRTP 性能结果修改。

## 3. 更新合同

先按原 DRTP 合同得到 `q^{cand}_u`，再使用：

\[
\alpha_u=c_u,\qquad
q^R_{u+1}=(1-\alpha_u)q^{uniform}+\alpha_u q^{cand}_u.
\]

最终仍执行原有 bounded-simplex projection，保持每个 failure-group 概率在 `[0.05,0.35]` 且总和为 1。nominal mass 固定为 0.50。

## 4. 必须通过的技术门

- R-DRTP/DRTP/UTR 参数、状态字典和 actor information boundary 相同；
- 七组 exposure、成员定义、nominal mass 和 failure semantics 一致；
- `alpha=0` 时输出恰为 uniform；
- `c=1` 时输出恰为原 DRTP candidate update；
- 任一组样本减少或 MAD 增大时，该组可信度不增加，整体 `alpha` 不增加；
- q 的 floor/cap/simplex 断言通过；
- selection、update、logging deterministic replay；
- checkpoint save/reload/next-update exact continuation；
- 打开或关闭日志不改变 checkpoint 与 sampler state；
- one-update CPU finite-value smoke 通过。

## 5. 停止边界

本合同只授权实现和技术审计，不授权 evaluation tape、development training、held-out、canonical seeds 或任何长训练。任何技术门失败都输出 `REVISE` 或 `FAIL` 并停止。
