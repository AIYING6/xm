# P2 Latent Agent-Scoped Uncertainty：最终裁决

状态：`P2_NO_GO__LATENT_SCOPE_PROBLEM_NOT_IDENTIFIABLE_ON_STANDARD_MPE2`

## 审计范围

使用数据盘隔离的 MPE2 标准环境：

- `simple_spread_v3`
- `simple_formation_v1`

固定四个种子，执行无训练 paired scope audit。scope 仅通过清零受影响 agent 的局部 landmark-relative observation 注入；物理动力学、动作接口和随机种子不变。

## 结果

两个标准任务中，nominal、single-scope 和 switching-scope 下，oracle 与局部历史控制器的任务完成率均为 100%。局部 scope 会改变部分观测和平均回报，但没有造成稳定的任务完成差距，也没有出现 scope oracle 可完成而 local-history 明显失败的反事实链。

因此不满足 P2 的核心条件：

> hidden scope 必须改变最优协同行为，并在标准 benchmark 上形成可重复、不能由简单局部策略等价解决的任务退化。

## 裁决

P2 关闭：

`P2_NO_GO__LATENT_SCOPE_PROBLEM_NOT_IDENTIFIABLE_ON_STANDARD_MPE2`

不实现 P2 算法、不追加 scope 强度、不新增训练、不回到 UAV 平台制造现象。MPE2 依赖和审计脚本仅作为可复现实验记录保留。
