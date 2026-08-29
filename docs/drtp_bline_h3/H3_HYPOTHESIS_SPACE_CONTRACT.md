# DRTP B 线 H3 假设空间压缩合同

本阶段为零训练、零重评估、零算法修改的证据压缩。输入只限已经存在的
1900/2000、2300/2400、B3 2701–2703 与 H2 2801–2805 数据产品。

H1（直接 `sampler/q → exposure → behavior/support → outcome`）与 H2（早期
critic/policy 脆弱性 × adaptive sampling）均为永久关闭假设。不得换名、放宽
重复门槛或拆开其中一层后重新包装为 H3。

H3 只有同时满足未被反驳、现有描述性支持、可写出时间顺序、可配对 UTR 对照、
可由新 seed 证伪、短预算可检验且有单一最小修复方向时，才可被推荐。否则返回
`NO_ACTIONABLE_H3`，不得训练。
