import pandas as pd, os
base = 'results/paper_config_runs/chain_aux_dev100/runs'
runs = []
for grp in ['ea_rg_mappo', 'ea_rg_mappo_chain_aux']:
    for s in ['seed0', 'seed1', 'seed2']:
        f = os.path.join(base, grp, 'bc_ppo_' + s, 'train_log.csv')
        if os.path.exists(f):
            df = pd.read_csv(f)
            df['grp'] = 'chain_aux' if 'chain_aux' in grp else 'baseline'
            df['seed'] = s
            runs.append(df)

print("=== EVAL SUMMARY (last eval row per run) ===")
for df in runs:
    ev = df.dropna(subset=['eval_success_rate'])
    if len(ev) == 0:
        continue
    last = ev.iloc[-1]
    print(f"{df.grp.iloc[0]:10s} {df.seed.iloc[0]} upd={int(last['update']):3d} succ={last.eval_success_rate:.2f} "
          f"timeout={last.eval_timeout_rate:.2f} avg_dist={last.eval_avg_distance:.0f} n_eval={len(ev)}")

print("\n=== TRAIN METRICS (update 1 vs last) ===")
for df in runs:
    r1 = df.iloc[0]
    rl = df.iloc[-1]
    if df.grp.iloc[0] == 'chain_aux':
        ca = rl.chain_aux_acc
    else:
        ca = float('nan')
    print(f"{df.grp.iloc[0]:10s} {df.seed.iloc[0]} upd={int(rl['update']):3d} loss1={r1.loss:.3f} lossL={rl.loss:.3f} "
          f"valL1={r1.value_loss:.3f} valLL={rl.value_loss:.3f} entL={rl.entropy:.2f} "
          f"train_rwd_L={rl.train_avg_reward:.3f} chainaux_acc={ca:.3f}")

print("\n=== CHAIN-AUX ACCURACY across updates (seed0/1 completed) ===")
for df in runs:
    if df.grp.iloc[0] != 'chain_aux':
        continue
    ev = df.dropna(subset=['chain_aux_acc'])
    if len(ev) == 0:
        continue
    accs = ev['chain_aux_acc'].tolist()
    print(f"chain_aux {df.seed.iloc[0]} upd={int(df['update'].iloc[-1]):3d} "
          f"acc_first={accs[0]:.3f} acc_last={accs[-1]:.3f} acc_mean={sum(accs)/len(accs):.3f}")
