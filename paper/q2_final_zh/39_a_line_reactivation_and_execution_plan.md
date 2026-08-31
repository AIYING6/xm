# A 线投稿收敛重启与执行计划

**状态：** `A_LINE_ACTIVE — SCIENTIFIC_EVIDENCE_FROZEN`  
**B 线：** `FROZEN; NOT A SUBMISSION DEPENDENCY`

## 一句话论证

在冻结的三无人机中继节点故障协同任务中，DRTP-SG-MAPPO 仅改变训练期六类故障组的有界权重；在参数、暴露范围、PPO、奖励和执行期信息边界匹配的正式 2301--2305 五种子 10M cohort 内，它相对 UTR-SG-MAPPO 在 F0、跨扰动均值和跨扰动最差端点呈一致正向配对收益；但独立 2401--2405 cohort 及跨 tape 诊断显示该收益未跨训练 cohort 稳定复现。

## 已核验的 A 线事实

- `scripts/check_q2_final_zh_manuscript.py` 已通过：正式主证据、外部 NoGraph 性能参考、独立反向 cohort、附加未见条件评价与八张受控图均已纳入；没有 formal-result placeholder，也没有跨 cohort 合并为 `n=10`。
- `scripts/check_drtp_submission_release_gate.py` 输出 `TECHNICAL_READY_AUTHOR_ACTION_REQUIRED`：科学材料、中文投稿前审稿版和本地匿名复现 staging 已就绪；未完成项仅为真实作者元数据和外部匿名托管。
- B 线的所有结果均不进入 A 线的方法、主表、主图或因果结论。它们不能成为删除、修饰或重新解释独立反向 cohort 的理由。

## 当前优先级

| 优先级 | 工作 | 责任方 | 完成标准 | 是否需要训练 |
| --- | --- | --- | --- | --- |
| P0 | 维持证据和主张边界 | 项目 | 正式 cohort 与独立 cohort 分层；不写 strict OOD、稳定优越、一般 DRO 或 adaptive necessity | 否 |
| P0 | 建立独立的 DRTP 英文投稿稿 | 项目 | 英文标题、摘要、术语和全部章节均以 `main_zh.md` 为唯一科学来源；不覆盖旧 EA-RG 英文稿 | 否 |
| P1 | 投稿前红队审稿与统计叙事核验 | 项目 | 每一核心主张对应可追溯证据，局限性在摘要、结果、讨论和结论一致 | 否 |
| P1 | 选择一个主投和一个备投 | 作者 | 目标期刊、文章类型、字数和格式明确 | 否 |
| P0（提交前） | 匿名复现包外部可访问性 | 作者 | 外部下载、SHA256、许可证、checkpoint 获取策略均实际验证 | 否 |
| P0（提交前） | 作者信息与声明 | 作者 | 作者、单位、基金、CRediT、COI、数据代码声明按目标刊填写 | 否 |

## 现在明确不做

1. 不再新增 DRTP、UTR 或 B 线候选的大规模训练；
2. 不为证明正文未主张的在线自适应必要性而补固定非均匀 10M 对照；
3. 不将 post hoc 未见条件评价重写为原始确认性 OOD；
4. 不因 B 线失败降低或隐藏 Original DRTP 在正式 cohort 内的真实结果；
5. 不将现有 `paper_latex_3d_en/` 的 EA-RG-MAPPO 旧稿当作 DRTP 投稿稿。

## 近期交付顺序

1. 创建 DRTP 英文稿的术语、主张和摘要规范；
2. 从中文终稿逐节重建英文 Introduction--Conclusion，先保证实验和讨论层的证据边界；
3. 对英文稿运行主张--证据、术语与匿名性审计；
4. 作者选刊后再迁移模板、压缩字数、补齐声明和外部匿名链接；
5. 完成最终 PDF 视觉核验与投稿 release gate。

此计划的目标不是把 DRTP 写成“已稳定解决”的算法，而是把已经完成的、可复核的正向正式 cohort 结果及其可靠性边界组织成一篇最能经受应用型 Q2 审稿的论文。
