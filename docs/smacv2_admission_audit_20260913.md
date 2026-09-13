# SMACv2 公开基准接入审计

**日期：** 2026-09-13  
**状态：** `PYTHON_INTERFACE_PASS / SC2_RUNTIME_BLOCKED / NO TRAINING`  
**对应选择卡：** `docs/public_benchmark_mainline_selection_20260913.md`

## 已完成的零训练核验

| 项目 | 结果 | 可追溯事实 |
|---|---|---|
| 官方源码获取 | 通过 | `oxwhirl/smacv2`，本地提交 `577ab5a2cff2391f8df582da5731ea9cd6adf3c6` |
| 许可证 | 通过 | 官方源码根目录 `LICENSE`；MIT |
| 多智能体接口 | 通过 | `smacv2/env/multiagentenv.py`：`reset`、`step`、`get_obs`、`get_state`、`get_avail_actions`、`get_env_info` |
| 现有 `cac` 初始依赖 | 未满足 | 初检为 `smacv2=False`、`smac=False`、`pettingzoo=False`；仅 `lbforaging=True` |
| SMACv2 Python 包安装 | 通过 | 通过本机代理连接官方 PyPI，已成功安装官方源码的 editable 包以及 `pysc2`、`s2clientprotocol`、`absl-py` 等依赖；`import smacv2, pysc2, s2clientprotocol, absl` 通过 |
| 官方地图 | 通过 | 官方源码随附 `smacv2/env/starcraft2/maps/SMAC_Maps/*.SC2Map` |
| StarCraft II 客户端 | 阻塞 | 标准 Windows 路径未发现本地 SC2 客户端；没有客户端不能创建真实 episode |

## 结论边界

静态审计证明 SMACv2 的观察、全局状态、合法动作掩码与终止信息足以桥接到本仓库的训练接口；它**不证明**该基准已在本机运行、MAPPO 已可学习、任何新方法有价值，或 SMACv2 会自动提供论文创新。

Python 网络/证书问题已通过本机代理解决。当前唯一运行阻塞是 StarCraft II 客户端本体；这不应被解释为题目 NO-GO。客户端可用后，下一项唯一授权的操作是标准 MAPPO adapter smoke test：随机合法动作完成一个短 episode，逐项记录 `obs/state/action-mask/reward/done/info`，不训练。

## 后续恢复条件

1. 安装与官方 README 匹配的 StarCraft II 版本；
2. 将源码内的 `SMAC_Maps` 复制或链接到该客户端所要求的地图目录；
3. 运行随机合法动作 smoke test，并保存版本、地图哈希及接口 schema；
4. 仅在 smoke test 通过后，才决定是否做短预算 MAPPO 可学习性审计。

在上述条件前，不实现新算法，不命名方法，也不将 SMACv2 写入论文的实验部分。
