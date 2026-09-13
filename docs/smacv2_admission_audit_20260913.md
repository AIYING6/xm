# SMACv2 公开基准接入审计

**日期：** 2026-09-13  
**状态：** `STATIC_INTERFACE_PASS / RUNTIME_DEPENDENCY_BLOCKED / NO TRAINING`  
**对应选择卡：** `docs/public_benchmark_mainline_selection_20260913.md`

## 已完成的零训练核验

| 项目 | 结果 | 可追溯事实 |
|---|---|---|
| 官方源码获取 | 通过 | `oxwhirl/smacv2`，本地提交 `577ab5a2cff2391f8df582da5731ea9cd6adf3c6` |
| 许可证 | 通过 | 官方源码根目录 `LICENSE`；MIT |
| 多智能体接口 | 通过 | `smacv2/env/multiagentenv.py`：`reset`、`step`、`get_obs`、`get_state`、`get_avail_actions`、`get_env_info` |
| 现有 `cac` 依赖 | 未满足 | `smacv2=False`、`smac=False`、`pettingzoo=False`；仅 `lbforaging=True` |
| SMACv2 Python 包安装 | 阻塞 | 官方镜像和官方 PyPI 均在下载 `pysc2>=3.0.0` 时发生 TLS 证书链错误 |
| StarCraft II 与地图 | 未核验 | 官方 README 要求本地 SC2 客户端与 `SMAC_Maps`；Python 依赖安装未完成前未尝试运行 |

## 结论边界

静态审计证明 SMACv2 的观察、全局状态、合法动作掩码与终止信息足以桥接到本仓库的训练接口；它**不证明**该基准已在本机运行、MAPPO 已可学习、任何新方法有价值，或 SMACv2 会自动提供论文创新。

本机网络/证书配置是当前唯一已知的运行阻塞，不应把它解释为题目 NO-GO。恢复依赖后，下一项唯一授权的操作是标准 MAPPO adapter smoke test：随机合法动作完成一个短 episode，逐项记录 `obs/state/action-mask/reward/done/info`，不训练。

## 后续恢复条件

1. 以可验证的内部包源、干净 Conda 环境或用户提供的离线 wheel 安装 `pysc2`、`s2clientprotocol`、`absl-py` 与官方 SMACv2；
2. 安装与官方 README 匹配的 StarCraft II 版本和 `SMAC_Maps`；
3. 运行随机合法动作 smoke test，并保存版本、地图哈希及接口 schema；
4. 仅在 smoke test 通过后，才决定是否做短预算 MAPPO 可学习性审计。

在上述条件前，不实现新算法，不命名方法，也不将 SMACv2 写入论文的实验部分。
