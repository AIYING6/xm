# EA-RG-MAPPO UAV Kill-Chain Recovery

This repository studies heterogeneous UAV cooperative decision-making under strict intermittent sensing, limited communication, message uncertainty, and relay-node failure.

The current paper-facing method is:

```text
EA-RG-MAPPO: Edge-Aware Multi-Relation Role-Graph MAPPO
```

The project is not a complete 6DOF red-blue air-combat system. The main statistical evidence is a lightweight 3DOF, 3v1 heterogeneous UAV kill-chain recovery task. Small 4v2/5v2 and LAG/JSBSim replay studies are planned only as controlled scenario-depth supplements after the main 3v1 evidence is hardened.

## Research Question

Under limited communication, intermittent sensing, message loss/delay, and relay-node failure, can a perception-communication-task-support multi-relation role graph improve heterogeneous UAV kill-chain recovery?

## Main Scenario

The main environment is `3d_intercept`:

- Scout detects and tracks the target.
- Relay forwards target information.
- Attacker forms and holds an attack window.
- The relay node loses communication function during the episode.
- Remaining UAVs must recover the reconnaissance-information-attack chain.

The environment includes:

- 3DOF position, speed, heading, and flight-path-angle dynamics;
- heterogeneous radar, communication, maneuver, and attack capabilities;
- strict target sensing and actor target-information bottleneck;
- communication dropout, message delay, cache TTL, and confidence;
- node failure and post-failure recovery metrics;
- CTDE separation between decentralized actor inputs and centralized critic state.

## Method

EA-RG-MAPPO separates three relation types:

- perception relation: who can directly sense target information;
- communication relation: which messages are physically delivered;
- task-support relation: which role pair currently supports kill-chain recovery.

The graph encoder uses role-pair-conditioned message passing so Scout-to-Relay, Scout-to-Attacker, Relay-to-Attacker, and peer-support messages are not forced to share one homogeneous edge rule.

## Baselines

The paper-facing baseline set is:

- Rule / geometric controller for feasibility reference;
- MAPPO / no-graph CTDE;
- Single-Graph GAT-MAPPO;
- Parameter-Matched Single Graph;
- HAPPO no-graph heterogeneous-policy baseline;
- EA-RG-MAPPO.

The current `happo` code path implements sequential heterogeneous-agent PPO updates with the HAPPO previous-agent joint-ratio correction. Earlier runs produced before this correction are historical HAPPO-style diagnostics and must not be mixed into formal paper evidence.

## Repository Layout

```text
algorithms/ri_gmappo/      MAPPO, graph encoders, training loop
envs/                      2D debug environment and 3DOF intercept environment
configs/paper/             paper-facing protocol and method configs
scripts/                   training, evaluation, audits, manifest utilities
tests/                     information-boundary and environment tests
docs/                      current project state, decisions, protocols, audits
results/                   development and paper-protocol outputs
```

## Environment

The active local environment is:

```text
conda env: cac
python: 3.8.20
torch: 2.4.1+cu124
numpy: 1.24.4
matplotlib: 3.7.5
```

Install minimal Python dependencies with:

```bash
pip install -r requirements.txt
```

If using CUDA-specific PyTorch wheels, install PyTorch from the official index matching the local CUDA runtime, then install the remaining requirements.

## Validation Commands

Run the core information-boundary tests:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe -m pytest tests/test_gate1_communication_feasibility.py -q
```

Audit paper configs and checkpoint-selection schema:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/audit_paper_configs.py
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/audit_checkpoint_selection_schema.py
```

Generate the current dev-1M command manifest:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/generate_paper_commands.py --mode dev_1m --methods mappo single_graph ea_rg_mappo happo --seeds 0 1 2 --include-sweeps
```

Run one resumable training chunk:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/run_manifest_training_chunk.py --method ea_rg_mappo --seed 0 --chunk-updates 100 --python-exe D:/Anaconda/envs/.conda/envs/cac/python.exe
```

Check current long-run progress:

```bash
D:/Anaconda/envs/.conda/envs/cac/python.exe scripts/check_training_progress.py --mode dev_1m --methods ea_rg_mappo single_graph mappo happo --seeds 0
```

## Current Experiment Status

The active formalization path is:

1. Re-run/continue dev-1M training with the corrected HAPPO baseline and keep pre-correction HAPPO-style outputs out of formal comparisons.
2. Run validation checkpoint sweeps only.
3. Freeze checkpoint-selection and training-budget decisions.
4. Expand to more training seeds.
5. Run final test once after all protocol choices are frozen.

Training-time online evaluations use only 5 episodes and are noisy monitors. They are not paper evidence. Current progress and audit status are recorded in:

```text
docs/PROJECT_STATE.md
docs/dev1m_seed0_progress.md
```

## Target-Prior Risk

Strict target sensing uses a configurable target prior before valid target information is available:

```text
target_prior_position = (10000, 0, 5000)
```

This is now exposed through `--target-prior-position` and recorded in evaluation CSVs. Target-prior perturbation/no-prior diagnostics should be run after dev-1M validation selection to test whether the learned policy depends on the fixed initial prior.

## Evidence Boundary

Historical results before P0 information-boundary hardening are development evidence only. Paper-facing claims must use checkpoints and evaluations generated after:

- actor graph feature leakage removal;
- role-identity ablation correction;
- strict target-cache TTL/confidence tests;
- checkpoint selection on validation split only.

Do not mix historical development diagnostics with final paper tables.
