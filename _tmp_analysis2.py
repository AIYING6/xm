import pandas as pd, os
base = 'results/paper_config_runs/chain_aux_dev100/runs'

def load(grp, s):
    f = os.path.join(base, grp, 'bc_ppo_' + s, 'train_log.csv')
    if os.path.exists(f):
        df = pd.read_csv(f)
        df['grp'] = 'chain_aux' if 'chain_aux' in grp else 'baseline'
        df['seed'] = s
        return df
    return None

runs = {}
for grp in ['ea_rg_mappo', 'ea_rg_mappo_chain_aux']:
    for s in ['seed0', 'seed1', 'seed2']:
        d = load(grp, s)
        if d is not None:
            runs[(d.grp.iloc[0], s)] = d

print("=== EVAL DISTANCE TREND (every eval interval) ===")
for key, df in runs.items():
    ev = df.dropna(subset=['eval_avg_distance'])
    dists = ev['eval_avg_distance'].round(0).tolist()
    print(f"{key[0]:9s} {key[1]} dist={dists}")

print("\n=== FINAL EVAL DISTANCE by group (mean over seeds) ===")
for grp in ['baseline', 'chain_aux']:
    vals = []
    for s in ['seed0', 'seed1', 'seed2']:
        df = runs[(grp, s)]
        ev = df.dropna(subset=['eval_avg_distance'])
        vals.append(ev['eval_avg_distance'].iloc[-1])
    print(f"{grp:9s} final_dist mean={sum(vals)/len(vals):.0f}  seeds={[round(v) for v in vals]}")

print("\n=== SUCCESS RATE any nonzero? ===")
for key, df in runs.items():
    ev = df.dropna(subset=['eval_success_rate'])
    any_succ = (ev['eval_success_rate'] > 0).any()
    last = ev['eval_success_rate'].iloc[-1]
    print(f"{key[0]:9s} {key[1]} any_success={any_succ} last_succ={last:.2f}")

print("\n=== TRAIN REWARD trend (window mean of last 20 updates) ===")
for key, df in runs.items():
    last20 = df['train_avg_reward'].tail(20).mean()
    first20 = df['train_avg_reward'].head(20).mean()
    print(f"{key[0]:9s} {key[1]} first20={first20:.3f} last20={last20:.3f} delta={last20-first20:+.3f}")

print("\n=== VALUE LOSS trend (last eval) ===")
for key, df in runs.items():
    ev = df.dropna(subset=['eval_avg_distance'])
    print(f"{key[0]:9s} {key[1]} value_loss_last={df['value_loss'].iloc[-1]:.3f} entropy_last={df['entropy'].iloc[-1]:.2f}")
