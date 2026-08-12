# Phase 2IA8 P1 pre-completion mechanism-probe launch record

**Status:** frozen before P1 outputs.  
**Protocol:** `PHASE2IA8-PSR-V1`  
**Scope:** fixed-controller, DEVELOPMENT_ONLY mechanism probe; no learned
policy, checkpoint, optimizer, or training update.

## Frozen matrix

- controllers: `structural_oracle`, `legal_observation`;
- new development seeds: `701`, `702`, `703`;
- episodes: 100 per controller × seed (600 total);
- target: straight; communication range scale 1.0; dropout 0.30; delay 2;
  strict sensing and information bottleneck enabled; no fixed node failure;
- support eligibility: the first two consecutive `chain_support_t=1` steps by
  step 220;
- intervention: relay agent 1 fails at the next timestep for 80 steps;
- no fallback failure when ineligible; no continuation after terminal success.

Paired development IDs are frozen:

```text
710000 + 10000 * controller_index + 1000 * seed_index + episode_index
```

## P1 gate

The P1 mechanics gate passes only if, for each controller:

1. all 300 raw episodes and all six controller/seed trace files are present;
2. every activated fault begins exactly one step after a two-step support
   trigger and lasts exactly 80 configured steps;
3. trace reconstruction agrees with raw support eligibility, `t_failure`,
   `t_loss`, `t_recovery`, and event fields;
4. at least 40 support-eligible episodes occur across the three seeds;
5. eligibility occurs in at least two seeds, with at least 10 episodes in two
   of those seeds;
6. at least one eligible episode has an observed support loss after failure.

P1 does not compare controller performance, returns, success, or recovery
rates. A P1 fail leaves Phase2IA8 P2 and all training NO-GO. A P1 pass only
permits a separately frozen P2 archived-checkpoint observability protocol.

## Authorized invocation

```powershell
D:/Anaconda/envs/.conda/envs/cac/python.exe `
  scripts/run_phase2ia8_p1_mechanism_probe.py `
  --execute `
  --out-dir results/development/phase2ia8_p1_mechanism_probe `
  --episodes 100
```
