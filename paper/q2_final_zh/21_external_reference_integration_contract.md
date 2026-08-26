# 21 MAPPO-NoGraph 外部参考结果整合合同

## 1. 目的与边界

本合同仅规定完成后的 MAPPO-NoGraph 外部参考如何进入中文主稿。其功能是帮助读者理解图结构主干在同一冻结任务中的外部定位；它不替代、稀释或重写 UTR–DRTP 的参数匹配主消融。

主因果问题仍是：在相同 SG actor/critic、116,728 参数、PPO、环境、奖励、七组暴露、50% 正常工况锚点、10M 预算和共同评价 tape 下，有界自适应加权相对均匀加权的增量作用。

外部参考问题是：移除图消息输入的标准 MAPPO-NoGraph 在同一任务、相同训练种子和共同 tape 上处于什么性能位置。由于网络结构与参数量不同，该结果不能被用于归因“DRTP 的自适应加权”本身。

## 2. 接入硬条件

只有同时满足以下条件，才允许将外部结果写入主稿或补充材料：

1. `DRTP_MAPPO_EXTERNAL_REFERENCE_DECISION.json` 的状态为 `EXTERNAL_REFERENCE_COMPLETE`；
2. 五个 seed `2301–2305` 全部从零开始、严格连续训练到 10M final checkpoint；
3. 新的 MAPPO-NoGraph 评价与已冻结 UTR/DRTP 正式评价使用同一 `490000–490099` tape，且 tape hash 一致；
4. 外部评价包含全部计划 episode、所有五个 seed 和完整安全指标；
5. 未发生 checkpoint promotion、seed exclusion、预算替换或结果驱动重跑；
6. 归档 SHA256、run manifest 与 machine-readable paired effects 均可读取。

缺少任一项时，主稿继续保持“尚无可纳入性能主表的外部 MAPPO 比较”的现状，不得以训练日志、截图或部分 seed 替代。

## 3. 允许的正文整合方式

通过第 2 节硬条件后，允许在以下位置增加一段有限表述：

- 第 2.4 节：将 MAPPO-NoGraph 从文献定位升级为“同任务外部参考”，明确它回答架构定位而非自适应权重的因果识别；
- 第 5.1 节表 1：增加“外部参考”一行，列明网络结构/参数量不同；
- 第 6 节：增加一张补充性表或一幅补充性图，完整展示 UTR、DRTP 与 MAPPO-NoGraph 的绝对值及 MAPPO 相对两者的五 seed paired effects；
- 第 7.4 与第 7.5 节：据实际结果讨论图结构参考的定位和不可归因边界。

摘要、贡献第 3 条和结论中的 UTR–DRTP 主因果结论不因外部参考而改写。除非外部结果本身满足完整硬条件，主文不得出现 MAPPO 的具体性能数字。

## 4. 结果解释纪律

| 观察到的外部结果 | 允许解释 | 禁止解释 |
|---|---|---|
| MAPPO-NoGraph 低于 UTR/DRTP | 在该冻结任务、该外部参考合同下，图结构主干与更高绝对性能相一致 | 图结构或 DRTP 在所有无人机/MARL 任务中必然更优 |
| MAPPO-NoGraph 接近 UTR | 外部参考未提供明显架构性能分离 | DRTP 的自适应加权失效；两者参数/结构不同不能回答该问题 |
| MAPPO-NoGraph 高于 DRTP | 外部参考不支持将 DRTP 描述为相对该基线的绝对最优方法 | 删除 UTR–DRTP 主消融，或隐藏 MAPPO 的五 seed 差值 |

无论方向如何，必须保留全部五个 seed、均值、中位数、最差 paired difference、collision、timeout 和 constraint violation。episode 不是独立训练重复；训练 seed 才是独立单位。

## 5. 明确排除的内容

- 不启动第二个外部算法、PPO sweep、图网络调参或 MAPPO 再训练；
- 不把 MAPPO-NoGraph 写成与 UTR/DRTP 完全同构的主消融；
- 不用外部参考的结果修订 DRTP 历史 development/held-out 结论；
- 不将 EGTR P3 的内部 1M 结果混入外部参考表或 DRTP 主结论。

## 6. 投稿前状态

当前状态为：外部参考训练合同和汇总脚本已冻结，但本地尚未收到可核验的完成归档。因此本合同是“结果到达后的防返工接口”，不是对外部结果的预先肯定，也不阻塞 DRTP 主稿继续完成引用、图表、数据可用性和中文期刊模板工作。
