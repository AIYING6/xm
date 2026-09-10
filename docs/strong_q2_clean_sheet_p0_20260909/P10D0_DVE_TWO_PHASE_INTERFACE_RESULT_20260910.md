# P10-D0 DVE 双阶段执行接口审计

**判定：** `P10D0_TWO_PHASE_INTERFACE_PASS`  
**训练：** 候选与基线均未启动。

## 1. 审计发现的问题

P10-C 最小环境把完成时状态直接作为策略观测。如果据此训练普通 recurrent/delay-aware policy，它可以直接输出 accept/fallback，与 DVE admission 使用相同的即时信息。这样即便 DVE 获得收益，也无法区分收益来自有效性包络还是来自额外完成时状态。

因此在任何学习实验前，将系统拆分为两个具有不同计算与信息语义的阶段。

## 2. 冻结接口

### 慢策略提议阶段

策略从起始快照生成计划动作。允许输入：起始局部状态、起始任务状态和部署前已知的时延分布描述。禁止输入：实际完成状态、未来状态、隐藏队友状态和未实现的实际推理时延。

计划动作一旦进入计算即被冻结，不能在看到完成状态后重新解释为该慢策略的输出。

### 轻量 admission 阶段

推理完成后，一个有界轻量组件可读取实际经过时间、当前局部状态、计划动作元数据和签名团队预约摘要，只输出 accept/fallback。fixed TTL、safety shield 和 DVE 必须共享完全相同的 admission 输入与运行预算；差异只能是接受规则。

## 3. 审计结果

- 两个具有不同完成状态的样本，其 proposal observation 逐元素一致；
- proposal 冻结前读取 completion observation 会被拒绝；
- proposal 冻结后，合法 admission observation 能区分当前相对误差和预约状态；
- 同一个 corridor proposal 在有效完成状态被接受时价值为 8，在过期状态回退时价值为 3；
- 没有未来状态或隐藏真值进入慢策略输入；
- 新旧环境相关测试共 5 项全部通过。

## 4. 公平比较含义

后续主对照不是“DVE 看当前状态、baseline 不看”的不公平比较。所有 admission 方法均看到相同完成时合法输入：

- fixed TTL 只依据经过时间；
- current-state shield 只依据硬安全谓词；
- DVE 依据动作特定的任务与团队有效域。

慢策略骨干、proposal、参数预算、执行延迟和状态轨迹必须匹配。若 DVE 的 admission 计算本身超过实时预算，其动作应按相同规则过期，不能豁免。

## 5. 下一步

进入 P10-D1 baseline-only learnability：

1. 冻结 train/validation/sealed-test 状态生成器；
2. 只训练容量匹配的慢 proposal policy 与 delay-aware admission baseline；
3. 不实现 DVE validity head；
4. 验证至少 2/3 seeds 优于 always-accept/fallback，且接受率不落入极端常数区间；
5. P10-D1 禁止访问 sealed test。

基线不可学习则重审任务表示，不得据此声称 DVE 有效。

## 6. 资产

- 内核：`envs/dve_async_execution_kernel.py`
- 接口合同：`configs/p10d0_dve_two_phase_interface_20260910.json`
- 测试：`tests/test_dve_async_execution_kernel.py`
- 机器结果：`docs/strong_q2_clean_sheet_p0_20260909/P10D0_DVE_INTERFACE_AUDIT_RESULT.json`

