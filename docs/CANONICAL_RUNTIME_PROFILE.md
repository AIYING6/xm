# Canonical runtime profile

The intended cloud profile is one RTX 4090 with `CUDA_VISIBLE_DEVICES=0`, `OMP_NUM_THREADS=8`, `MKL_NUM_THREADS=8`, and bounded process concurrency. These are non-scientific settings. A stable throughput/VRAM benchmark has not yet been completed on the cloud server because SSH access is currently unavailable. Gate R remains pending.
