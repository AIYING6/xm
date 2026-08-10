# Fig. 1 Fidelity V1 → V2 对照与版式核验

## 参考图作为视觉母版

本轮重构将用户提供的 Fig. 1 用作**几何与视觉语言母版**，而非内容模板。保留的骨架包括：

- 宽幅画布、上方 `(a)/(b)` 与下方 `(c)/(d)` 的四联边界；
- Scout 左上、Relay 右上、Attacker 左下、Target 右下的任务场景构图；
- `(b)` 的正常/relay-failure 双小场景加双信息流框；
- `(c)` 上方去中心化执行、下方集中训练，并由中部 CTDE boundary 分隔；
- `(d)` 左侧来源块/特征块、中部大编码器、右侧融合与嵌入；
- 底部横向角色—关系—失效图例、细黑边框、白底与淡灰山地背景。

## 布局锚点的静态核验

最终图以归一化坐标固定主要面板：`(a) x=.025–.540`、`(b) x=.540–.975`、`(c) x=.025–.540`、`(d) x=.540–.975`；底部图例为 `x=.025–.975`。参考图的主分割线位于约 53% 宽度；最终图为 54.0%，面板分割与外边界偏差在 1–2% 量级，满足本轮 3–5% 的布局锚点目标。

`fig1_architecture_fidelity_v2_overlay.png` 是参考图与最终图按相同像素尺寸（1491×1055）进行 50% alpha 叠加的可视 QA 工件。它仅用于比较面板、标题、图例与主模块的相对位置；不作为论文插图。

## Fidelity V1 发现与 V2 修复

| 项目 | Fidelity V1 | Fidelity V2 修复 |
|---|---|---|
| `(b)` 下方 flow schematic | disrupted 版本的节点横坐标超出信息流框，视觉不稳定 | 改为按信息流框宽度比例布置四节点，正常/失效框均完整闭合。 |
| `(d)` 底部说明条 | 使用部分字体不稳定的数学符号 | 改为文字分隔符，保证 SVG/PDF/PNG 一致可读。 |
| 面板视觉重心 | 已采用参考图的上/下、左/右四联骨架 | 保持该骨架，未再按 PCRF-R2 自行重排。 |

## 必须存在的科学替换（非视觉偏离）

- `Relation types` 改为 `Legal evidence sources`，且只保留 `P: direct perception` 与 `C: delivered + cache-valid communication`；
- `(c)` 的旧多关系模块替换为 `P/C legal-source graph construction → PCRF-R2 encoder → Actor Policy`，下半部分保留 centralized critic；
- `(d)` 的第三个左侧槽位是灰金色 `Conflict descriptor`，不是第三种关系来源；
- 旧方法模块没有出现在最终图中。

这些替换由 `fig1_architecture_content_audit.md` 中所列的冻结协议及实现术语约束。
