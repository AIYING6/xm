# EGTR 双 cohort 同步执行修订

**状态：** `EGTR_DOUBLE_COHORT_SIMULTANEOUS_EXECUTION_AUTHORIZED`  
**生效条件：** 必须在任何 71011--71025 训练开始前通过本修订的零训练审计。

本修订仅改变执行调度：Cohort A（71011--71015）与 Cohort B（71021--71025）可从同一冻结源码、同一成熟预算、同一未被训练读取的 development-only tape 下同步启动。这样做放弃“若 A 失败则节省 B 算力”的资源停止规则，但不改变任何统计或科学判定。

仍然禁止 pooled n=10 作为确认性推断。A、B 均必须独立通过完全相同的机器门；任一 cohort 失败即为 `EGTR_DOUBLE_COHORT_REPLICATION_NO_GO`。不允许基于中间曲线、A 的结果或 B 的结果修改公式、κ、simplex、L1、PPO、环境、reward、seed、tape、阈值、catastrophic 定义或安全规则。

本修订不授权 Cohort C、1M/3M checkpoint promotion、后续算法版本或 held-out/OOD claim。
