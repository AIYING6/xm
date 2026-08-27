# 补充材料 S3｜超参数、有界投影与证据 provenance

## S3.1 冻结训练合同

正式主 cohort 的训练合同为 `DRTP-UTR-Q2-FORMAL-PAIRED-5SEED-V1`。UTR 与 DRTP 使用相同 SG actor/critic（116,728 参数）、PPO、环境、奖励、七组拓扑训练 universe、50% nominal anchor、10,000,128 environment steps 和 2301--2305 配对训练种子。唯一预期算法差异是：UTR 在六个故障组上条件均匀采样；DRTP 根据既定的六维有界权重更新规则重分配该 50% 故障质量。

PPO 共同设置为：学习率 `3e-4`、`gamma=0.99`、GAE `lambda=0.95`、clip `0.2`、entropy coefficient `0.01`、value-loss coefficient `0.5`、max gradient norm `0.5`、每批 4 次 PPO epoch。环境、观测、奖励和终止规则以 run manifest 与项目配置为准。

## S3.2 DRTP 采样器的明确实现

六组条件权重满足 `q_k in [0.05, 0.35]` 且 `sum_k q_k=1`。初始化 `q_k=1/6`，前 128 updates 保持均匀，之后每 32 updates 适配。冻结超参数为 `kappa=0.20`、`eta=1.00`、`beta=0.50`、`d_max=2.00`、`epsilon=1e-8`。

主文式(4)--(8)给出：组回报 EMA、相对 normal 的 clip difficulty、中心化指数候选、平滑和有界 simplex projection。对待投影向量 `x`，使用 100 次二分求解标量 `lambda`，使 `q_k=min(0.35,max(0.05,x_k-lambda))` 且质量和为 1；浮点残差只在未触及边界的分量上按固定顺序补偿。该投影仅改变训练期采样分布，不改变 PPO 损失、actor/critic 参数量或执行期信息。

## S3.3 评价与完整性标识

| 项目 | 值 |
|---|---|
| 主 cohort tape | episode ID 490000--490099；12 条件；12,000 条 raw records |
| 主 cohort tape SHA256 | `84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2` |
| 主 cohort archive SHA256 | `cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd` |
| 无图 MAPPO 参考 archive SHA256 | `2f8b5f1e3025221e70652a6c4d0bcaa05d239cc81f5c70d59301d4f9e66afad5` |
| 独立三方法 cohort archive SHA256 | `86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1` |
| 独立 cohort tape SHA256 | `c89f63bc5a11e3def88fa677356796ea681ca227d31e47dc584764a3a3084fc2` |

hash 对应的文件位置与匿名发布策略见 `../24_anonymous_reproducibility_package.md` 和 `../25_final_evidence_manifest.json`。所有 completed seed、包括不利 seed 和独立 cohort 的反向结果，均须随复现包保留；不得 checkpoint promotion、seed exclusion 或跨 cohort `n=10` pooling。
