# v1.6 最小资格重训协议（未启动）

状态：`V1_6_MINIMAL_QUALIFICATION_PROTOCOL_FROZEN__READY_FOR_USER_LAUNCH`

日期：2026-08-11

## 目的

只判断 strict recipient-specific actor contract 修复后，EA-RG 是否仍相对强 baseline 保留稳定方向信号。不产生论文正式结论，不扩展 robustness 或 ablation。

## 固定矩阵

| 维度 | 冻结值 |
|---|---|
| 方法 | MAPPO/no-graph、strong single-graph、EA-RG multi-relation、HAPPO |
| 训练 seed | 6101、6102（均为新 seed） |
| 训练 runs | 4 方法 × 2 seeds = 8 runs |
| 场景 | `configs/paper/main_gate1.yaml` 的 primary strict-sensing scenario suite |
| actor contract | local sensing 或 delivered/cache-valid packet；全局 target 旁路禁止 |
| rollout | `num_envs=4`、`rollout_steps=64` |
| qualification budget | `updates=977`，即约 `250,112` environment steps/method/seed |
| hidden dim / optimizer / reward | 继承冻结 main_gate1 及各方法原公平配置，不单独调参 |
| evaluation | validation 与 test 种子从同一 frozen manifest 生成；不使用训练结果改协议 |
| device | 训练前由用户明确指定 `cuda` 或 `cpu`；不得因单个方法更慢而改变预算 |

## 方法公平规则

* MAPPO、single-graph、EA-RG 必须使用相同合法 actor 输入来源和相同任务/通信配置；
* HAPPO 只能在其必要的角色/顺序更新接口上不同，不能额外获得信息或训练步数；
* BC（若保留）必须同数据、同 episodes、同 epochs；若某方法 BC 不兼容，统一禁用 BC，而不是只给部分方法保留；
* checkpoint 只按 validation 选择；qualification test 不参与选择。

## 判定顺序

1. 先检查 8 个 run 的 manifest、hash、训练步数、actor-contract flag 和 checkpoint 完整性；
2. 比较 EA-RG 与 single-graph、MAPPO 的 primary endpoint 和完成时间；
3. 检查两个 seed 是否方向一致，不以单个 seed 的峰值作 PASS；
4. 检查 collision/constraint failure 是否异常增加；
5. 若 EA-RG 两个 seed 均无优势或依赖非法输入，`QUALIFICATION_NO_GO`；
6. 只有两个 seed 都保持合理方向优势，才授权 4 方法 × 5 seeds 的 formal retraining。

## 启动前最后检查

* `scripts/test_actor_target_information_contract.py`：4/4 PASS；
* `scripts/test_actor_boundary_v1_8.py`：14/14 PASS；
* `scripts/audit_a0_information_compatible_ctde.py` 已完成只读审计；
* 不覆盖现有 `results/`；qualification 输出使用全新目录；
* 训练前保存 command manifest、git commit、配置 hash 和 seed manifest。

本协议仅冻结最小资格判断，尚未授权执行命令。

