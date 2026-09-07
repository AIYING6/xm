# DRTP 中文投稿稿图表计划

所有图表只能由冻结聚合 CSV、manifest 和 sampler 日志生成；A/B cohort 在主图中始终分开，不以 pooled n=10 取代独立验证。

| 编号 | 图题 | 回答的问题 | 版式与证据边界 |
|---|---|---|---|
| 图 1 | DRTP 整体框架 | 方法到底改变了什么 | 冻结条件支持集 → 名义/故障组 → EMA 回报缺口 → 有界概率更新 → 不变的 MAPPO；必须显著标记“仅 reset 分配变化” |
| 图 2 | 拓扑故障与训练暴露机制 | 为什么故障不是匿名关卡 | 展示角色图、失效节点、发生时刻、持续时间、名义锚点与组内均匀采样；不展示未经验证的因果箭头 |
| 图 3 | UTR 与 DRTP 训练过程 | RQ2：机制如何不同 | 用 UTR/PLR-style/DRTP 的条件分配流程图和冻结 sampler `q` 轨迹；轨迹是过程证据，不替代最终性能比较 |
| 图 4 | 主鲁棒性比较 | RQ1：是否重复优于 UTR | A/B 两个独立配对 seed 面板，另列 timeout、collision；不得合并成安全分数 |
| 图 5 | OOD/泛化结果 | RQ3：是否转移至冻结 shift | structural 与 parameter shift 的 A/B 配对 delta 热图或森林图；图注明确仅限冻结协议 |
| 图 6 | 6-UAV 跨尺度验证 | RQ4：是否扩展到大团队 | 完成后显示 UTR/DRTP 的 5 seed 配对端点和条件分解；当前不渲染虚构图 |

| 编号 | 表题 | 内容 |
|---|---|---|
| 表 1 | 匹配环境与训练协议 | 环境、角色图、冻结故障支持集、PPO、预算、endpoint tape、唯一方法差异 |
| 表 2 | 主终点结果 | A/B 各自的均值、中位数、最差 seed、SD、success、timeout、collision |
| 表 3 | PLR-style 外部比较 | A/B 分开报告；标题标明 cohort-dependent，不宣称全面胜出 |
| 表 4 | 6-UAV 跨尺度验证 | 正式结果完成后填写 |
| 表 5 | 关键机制消融 | 仅在预先冻结的消融协议完成后填写；否则保持待填 |
| 补充表 S1 | UTR/PLR-style/DRTP 机制比较 | sampling object、adaptation signal、topology semantics、nominal reference、update rule、constraints |
| 补充表 S2 | 冻结 OOD 对比 | shift family、paired delta、lower tail、timeout、collision |

## 图注统一规则

1. 主结果图注明确 `n=5 independently trained policies per cohort`；
2. 回报、timeout 与 collision 分开报告；
3. 不把 development-only EGTR/GA-EGTR 放入主结果图；
4. 6-UAV完成前，图 6 只能使用“正式实验进行中”的内部占位，不进入投稿 PDF；
5. 所有数值必须可追溯到聚合产物，禁止手工录入或从中间训练日志推断。
