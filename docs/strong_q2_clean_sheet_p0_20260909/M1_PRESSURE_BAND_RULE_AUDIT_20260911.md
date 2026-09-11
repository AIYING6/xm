# M1 压力带确定性规则验证

## 结论

`M1_PRESSURE_BANDS_PASS`。

在不训练、不接入 FUM-MAPPO 的条件下，冻结的 M1 任务已满足一个基础要求：不同的公开压力带诱导不同的、可解释的感知选择；冲突带中的偏好还会随公开后验与信息年龄变化而改变。

## 已验证的行为

| 压力带 | 公共主导信号 | 规则选择的区域 | 含义 |
|---|---|---:|---|
| uncertainty-dominant | 区域 0 的初始后验方差最大 | 0 | 高不确定性区域具有优先感知价值 |
| freshness-dominant | 区域 3 的 urgency × age 最大 | 3 | 高时效风险区域具有优先更新价值 |
| conflict-band（早） | 区域 0 的初始方差优势 | 0 | 初始时优先降低认知不确定性 |
| conflict-band（后） | 区域 3 的累积时效风险 | 3 | 经过一次测量与等待后，优先级发生合理转换 |

实现与可重复命令：

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/audit_m1_pressure_bands.py
```

## 证据边界

该结果只证明任务构造存在可区分的公开决策压力，且不是任何静态区域优先顺序都能同时匹配。它**不能**证明：

- MAPPO 能学习这些行为；
- FUM-MAPPO 优于基础 MAPPO；
- 联合价值规则是最优策略；
- 该任务已经具有论文级实验结论。

下一步授权仅限基础 MAPPO 的短预算可学习性测试。
