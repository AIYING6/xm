# DRTP/SNR Q2 云端执行说明

使用提交 `e356b87` 的源码压缩包解压后，在项目根目录启动：

```bash
export PYTHON_BIN=python
export GPU_IDS=0
export MAX_PARALLEL=10
export EVAL_WORKERS=8
export CPU_THREADS_TOTAL=16
export OUTPUT_ROOT="results/formal/drtp_snr_q2_mechanism_comparator_10way"

bash scripts/launch_drtp_snr_q2_autodl.sh
```

启动器会依序执行 preflight、创建新 `500000–500099` tape、训练 15 条共同 10M 轨迹、评价 18,000 条 episode、汇总、打包并停止。它拒绝覆盖非空输出目录，且任一阶段失败即退出；不会自动进入任何后续训练。

若需要自动关机，应由云端的外层 `screen`/`setsid` 包装器在启动器返回码为零时执行关机。不要在启动器内部添加无条件关机命令，以免发生失败后误关机而无法下载错误日志。
