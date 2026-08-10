# v1.9 F1 收尾与 F2 就绪清单

**状态：F1 运行中；本文档不授权 F2，也不读取任何确认性 episode。**

## F1 完成后的唯一顺序

1. 等待 24/24 个 run 均完成 300 updates；不得因任一 training-time validation 值暂停、加训、换 seed 或修改方法。
2. 运行现有 F1 artifact gate，核验连续训练日志、31 个 validation update、snapshot/summary/event-record SHA256、stderr、有限数值、R2 encoder provenance 与 CUDA/source attestation。
3. 仅从 immutable training-time validation records 运行冻结 selector，输出 24 个 selected checkpoint 的路径、update、SHA256、method、seed、source commit 与 selector fields。
4. 生成并保存 `F1_R2_TRAINING_ARTIFACT_GATE_MANIFEST.json` 与 `F1_R2_SELECTED_CHECKPOINTS_MANIFEST.json`；输出必须表明 `confirmatory_heldout_accessed=false`。
5. 备份 F1 工件；停止 GPU 训练。此时状态才可申请更新为 `F1_R2_FORMAL_TRAINING_COMPLETE__CHECKPOINTS_FROZEN__READY_FOR_F2_AUTHORIZATION`。
6. 停止并等待作者单独授权 F2。F2 之前不得打开确认性 generator、episode bank 或任何由其派生的统计结果。

## 云端 F1 收尾命令（仅在训练脚本自然结束后使用）

```bash
cd /root/autodl-tmp/v1_9_f1_r2_3041e99

python scripts/check_v1_9_f1_r2_artifacts.py \
  --root results/v1_9_f1_r2_formal \
  --expected-source-commit 3041e9971453cc21dfdb6f25fdb4454a1d5fa947 \
  --output results/v1_9_f1_r2_formal/F1_R2_TRAINING_ARTIFACT_GATE_MANIFEST.json

python scripts/select_v1_9_f1_r2_checkpoints.py \
  --root results/v1_9_f1_r2_formal \
  --expected-source-commit 3041e9971453cc21dfdb6f25fdb4454a1d5fa947 \
  --output results/v1_9_f1_r2_formal/F1_R2_SELECTED_CHECKPOINTS_MANIFEST.json
```

正常 F1 launcher 已在成功路径自动执行上述两个步骤；本段只用于审计人工核查，不应用于失败或中断 run 的补救。若 manifest 已存在，不得覆盖或重新生成。

## F2 合成数据烟雾测试的边界

`scripts/test_v1_9_f2_synthetic_preflight.py` 只在临时目录生成虚构的 24 checkpoint 条目和 300 个 `synthetic-*` episode 标识。虚构 selector winner 覆盖 update 120、180、240 和 300，以确保计划不假定每个正式 checkpoint 都来自最后一个 update。该测试检查：

- 3 methods × 8 training seeds 的选择清单结构；
- 每个 checkpoint 使用同一顺序的 300 个配对 episode 标识；
- 训练 seed 在 bootstrap 外层、episode 配对在内层的输入布局；
- 合成数据不会引用 `results/`、真实 episode generator、F2 seed 或 F2 hash。

该测试不创建确认性 population、不运行 actor、不计算真实性能指标，也不构成 F2 pre-authorization。
