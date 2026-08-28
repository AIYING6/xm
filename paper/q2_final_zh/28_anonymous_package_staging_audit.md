# 匿名复现包本地构建与核验记录

**状态：** `LOCAL_STAGING_PASS / EXTERNAL_HOSTING_PENDING`
**范围：** 仅从已完成的三份本地归档整理原始记录、运行 manifest、采样器日志、合同、代码、配置和作图资产；不启动训练、不重跑评估、不修改数值结果。

## 1. 已完成的本地构建

构建命令：

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe `
  scripts/build_drtp_anonymous_reproducibility_package.py `
  --output output/drtp_relay_failure_anonymous_reproducibility_v8
```

输出目录：

```text
output/drtp_relay_failure_anonymous_reproducibility_v8/
```

该目录由构建器重新计算并核验以下三份归档的 SHA256，随后选择性提取投稿复现所需原始评价记录、评价/tape manifest、训练 preflight、每条 run manifest 及 sampler log：

| 证据 strata | 归档 SHA256 | 原始记录 | 选择性提取文件数 |
|---|---|---:|---:|
| 正式 UTR--DRTP（2301--2305） | `cc3e2d29f382c332563c33957f5c109bbee4f42abb91b0d06b2b26cd3e618bdd` | 12,000 | 35 |
| 无图 MAPPO 性能参考（2301--2305） | `2f8b5f1e3025221e70652a6c4d0bcaa05d239cc81f5c70d59301d4f9e66afad5` | 6,000 | 20 |
| 独立三方法重复（2401--2405） | `86a708244fa4d30935159a08d234c48feeb7a4c455208d58fbc58d308b4f4ae1` | 18,000 | 50 |
| 跨评价带零训练诊断（两 cohort×两 tape） | 见 `results/analysis/drtp_cross_tape_reliability/` manifest | 48,000 | diagnostic 全量记录 |

三个 strata 仍为独立证据层。构建器和 README 均明确禁止将正式 cohort 与独立 cohort 合并为 `n=10`。

## 2. 完整性核验

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe `
  scripts/check_drtp_anonymous_reproducibility_package.py `
  --package-root output/drtp_relay_failure_anonymous_reproducibility_v8
```

通过条件：三层均具有 `raw_episode_metrics.csv` 与 `evaluation_manifest.json`，所有已列入 `FILE_MANIFEST_SHA256.csv` 的文件 checksum 一致，package provenance 精确记录三份源归档及本稿源代码 revision，且对文本资产执行匿名标记扫描（作者仓库名、个人路径与预定义身份标识均不得出现）。

## 3. 仍必须由作者完成

此状态不是“数据已公开”。外部匿名托管、外部下载验证、许可证、checkpoint/runtime-state 的公开或受限获取策略、作者/基金/CRediT/冲突元数据以及目标期刊模板均需要作者决定。对应逐项清单在复现包根目录的 `RELEASE_BLOCKERS.md` 和文档24中维护。
