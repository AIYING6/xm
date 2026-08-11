# P2 初步现象审计记录

状态：`P2_PRELIMINARY_AUDIT_HARNESS_VALIDATED__NOT_A_PASS`

`scripts/audit_p2_latent_scope.py` 已完成一次无训练、无 UAV 修改的 MPE/Particle 风格连续协作预检，输出写入 `results/p2_latent_scope_audit.json`（结果目录不纳入版本控制）。

当前预检确认：

- nominal 场景下所有透明控制器均可完成；
- 隐藏 sensing scope 会使受影响 agent 的合法局部控制退化；
- oracle 与非 oracle 控制器出现可测差异；
- 审计器不向非 oracle 控制器注入全局 target/scope truth；
- 未执行任何训练或参数优化。

这不是 P2 PASS。当前脚本只是确定性审计器的工程预检，尚未满足正式协议的两个独立标准 benchmark、paired counterfactual 完整覆盖和 scope-mask 等价性红队要求。正式结论必须在审计器接入两个独立、可追溯的标准 cooperative benchmark 后再作出。

## 发现并修复的审计器问题

初版静态控制器曾直接读取 target truth，违反 actor 合法信息边界；该路径已改为使用每个 agent 的局部估计/历史缓存，并重新运行无训练预检。这个工程缺陷不作为科学结果报告。
