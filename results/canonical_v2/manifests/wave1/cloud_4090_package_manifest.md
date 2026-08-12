# Cloud 4090 package manifest

This package is prepared for transfer to a remote RTX 4090 server. It contains the frozen source/protocol and the incomplete local Wave 1 artifacts for possible provenance-preserving resume. Local Wave 1 was terminated by user request; it is not a complete formal result.

Required remote checks before launch:

- `nvidia-smi` shows RTX 4090;
- `python -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))"` passes;
- uploaded files pass the package SHA256 check;
- no endpoint/tau/seed/failure/checkpoint-selection changes are made;
- any resume from a partial checkpoint is recorded as a technical continuation with checkpoint SHA256 and update offset.

Default hardware scheduling is `RUN_CONCURRENCY=2`, which can be raised only after observing GPU memory and utilization without changing the scientific runner arguments. The fixed runner arguments remain in `scripts/cloud/run_phase3a_wave1_4090.sh`.
