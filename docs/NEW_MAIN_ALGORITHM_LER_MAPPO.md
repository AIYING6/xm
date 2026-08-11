# 新主线：Legal-Evidence Role-Conditioned MAPPO

状态：`LER_MAPPO_MAINLINE_FROZEN__IMPLEMENTATION_AUTHORIZED`

## 主问题

在严格 recipient-specific actor information contract 下，不同 UAV 角色获得的目标证据来源、有效性和动作语义不同。统一策略输出会把无效动作和不完整证据混入同一个优化空间，导致异构协同退化。

## 算法假设

将合法证据状态（local sensing、delivered-valid packet、cache age、confidence）与角色动作语义显式用于 actor 条件化，并对角色不适用的动作 head 做硬 mask，可改善 mission-level physical neutralization。

核心机制只有两项：

1. role-conditioned actor heads；
2. legal-evidence validity gate，仅使用执行期合法证据控制 guidance head 的输入尺度和可用性。

不使用 global target truth、critic truth、Relay failure、progress latent、future prediction、额外 reward 或新通信原语。

## 主要比较

- unified heterogeneous MAPPO：统一 actor 输出；
- role-specific MAPPO：只有角色专用 heads；
- LER-MAPPO：角色专用 heads + 合法证据 validity gate；
- fixed scripted/oracle：只作可达性上界。

所有方法使用相同 observation、action、critic、reward、horizon、训练预算和评估 seeds。Full 只新增 legal-evidence validity gate；参数量差异预冻结在 1% 内。

## 主要指标

- `Neutralization rate`；
- `P(attack-range acquisition | legal evidence)`；
- `evidence-to-range latency`；
- `NO_ATTACK_RANGE_ACQUISITION` fraction；
- `RMTN180`；
- 角色无效动作率和 evidence-gate 合法性回归。

## 开发顺序

1. 实现 LER actor 与参数量审计；
2. 运行 actor-contract、continuous-action、role-head 回归；
3. 进行 2-seed development pilot；
4. 只有机制指标和 mission endpoint 同方向改善，才冻结 fresh-seed F1/F2；
5. 若 pilot 无改善，关闭该主线，不再追加模块。

## 论文定位

应用型算法论文，主张是：在真实 3DOF heterogeneous UAV mission 中，执行期合法证据和角色动作语义必须共同进入策略优化；贡献重点是完整机制、严格信息公平比较和物理终点验证，而不是声称发明新的 RL 理论家族。
