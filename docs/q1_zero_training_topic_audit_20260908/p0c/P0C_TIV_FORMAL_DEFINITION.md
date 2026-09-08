# P0C：任务信息可行域的最小形式定义

日期：2026-09-09

## 1. 系统

考虑有限时域 (t=0,ldots,H) 上的异构 UAV 团队 (mathcal V)。物理状态为 (x_t)，角色映射为 (ho_i\in\{S,R,A\})，分别代表感知、转发和任务执行角色。联合物理动作 (u_t=(u_t^i)_{i\in\mathcal V}) 按

\[
x_{t+1}=F(x_t,u_t,w_t)
\]

演化，其中 (w_t) 包含目标运动、丢包和外生节点/链路故障。动态通信图

\[
G_t=G(x_t,w_t)=(\mathcal V,\mathcal E_t)
\]

由位置、通信半径和故障共同确定。

本地代码对应关系为：`envs/uav_intercept_3d_env.py:339-354` 先执行 UAV 运动，再更新感知与通信；`envs/uav_intercept_3d_env.py:682-729` 由距离、通信范围、丢包和结构剪枝生成有效通信边。

## 2. 信息令牌与合法性

令牌

\[
\kappa=(c,o,g,d,p,h,\gamma)
\]

包含内容 (c)、来源 (o)、生成时刻 (g)、交付时刻 (d)、传播路径 (p)、跳数 (h) 和置信度 (gamma)。在时刻 (t)，令牌对执行者 (i) 合法，当且仅当：

\[
L_i(\kappa,t)=
\mathbf 1[o\in\mathcal O_i]
\mathbf 1[t-g\le \tau_i]
\mathbf 1[\gamma\ge \underline\gamma_i]
\mathbf 1[p\in\mathcal P_i(w_{0:t})]=1.
\]

这里 (mathcal O_i) 是任务允许的来源集合，(mathcal P_i) 是在故障历史下允许的来源路径集合。该定义对应现有代码中的生成/交付时间、路径、跳数、置信度和 `_attacker_cache_path_is_legal`，而不是新增环境事实。

## 3. 任务完成谓词

令 (y_t) 为任务自动机或阶段状态，(mathcal Y_G) 为完成集合。执行动作 (a_t^i) 只有在物理条件和信息条件均满足时才有效：

\[
a_t^i\in\mathcal A_i^{\mathrm{task}}(x_t,y_t)
\quad\land\quad
\exists \kappa\in Z_t^i:L_i(\kappa,t)=1.
\]

任务成功事件为在截止 (H) 前到达 (y_t\in\mathcal Y_G)，并且所有依赖信息的任务动作都由合法令牌支持。

## 4. 三种 TIV

### 4.1 全信息确定性 TIV

对剩余时域 (h)，定义

\[
\mathcal K_h=
\left\{s:
\exists\pi,\; y_{t+h}\in\mathcal Y_G,
\text{且全过程满足物理、安全和信息合法性约束}
\right\}.
\]

### 4.2 鲁棒 TIV

给定允许故障序列集合 (mathcal W_h)：

\[
\mathcal K_h^{\mathrm{rob}}=
\left\{s:
\exists\pi\;\forall w_{t:t+h-1}\in\mathcal W_h,
\;\mathrm{Success}(s,\pi,w)=1
\right\}.
\]

随机可靠性版本可将全称量词替换为成功概率不低于 (1-\delta)，但它是另一问题，不能与确定性鲁棒定义混用。

### 4.3 分散可观测 TIV

执行者只拥有本地历史 (h_t^i)。令 (B_t^i) 为与该历史一致的状态集合。局部证书 (C_i(h_t^i)=1) 若要可靠，至少必须满足：对所有 (s\in B_t^i)，存在与团队信息结构一致的联合策略保持成功可行。该量词涉及共同知识与联合策略一致性，不能由单个 actor 的局部阈值自然得到。

## 5. 与相邻对象的形式区别及失败点

| 对象 | 判定内容 | 与 TIV 的关系 |
|---|---|---|
| 瞬时图连通 | 当前图是否存在路径 | 既非充分也非必要 |
| AoI 可调度性 | 信息年龄能否满足阈值 | 忽略来源、角色、物理任务和执行窗口 |
| 时序逻辑任务可行性 | 是否存在满足任务/通信公式的轨迹 | 能完整编码上述 TIV，因此是强覆盖 |
| 标准 viability kernel | 是否存在使状态保持约束并到达目标的控制 | 将令牌状态并入系统后即可表达 TIV |
| Dec-POMDP/epistemic planning | 分散历史或知识条件下的任务规划 | 能表达分散可观测 TIV，计算代价高 |

因此，TIV 是一个清晰且有用的领域定义，但仅有该定义不能证明它是新的数学对象。
