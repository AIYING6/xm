import glob, os

def report(d, pat, label):
    paths = sorted(glob.glob(os.path.join(d, pat)))
    print(f"{label}: count={len(paths)}")
    if paths:
        # 提取 update 数字
        import re
        def num(p):
            m = re.search(r'_(\d+)\.pt$', p)
            return int(m.group(1)) if m else -1
        nums = [num(p) for p in paths]
        print(f"  first={nums[0]} last={nums[-1]} max={max(nums)}")
        for p in paths[-3:]:
            print("  ", os.path.basename(p))

report("results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed1", "actor_critic_update_*.pt", "MAPPO seed1")
report("results/paper_config_runs/dev_1m/runs/mappo/bc_ppo_seed2", "actor_critic_update_*.pt", "MAPPO seed2")
report("results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed1", "happo_update_*.pt", "HAPPO seed1")
report("results/paper_config_runs/dev_1m/runs/happo_standard/bc_ppo_seed2", "happo_update_*.pt", "HAPPO seed2")
