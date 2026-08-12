# Phase 2IA6 task-feasibility protocol

**Protocol ID:** `PHASE2IA6-TF-V1`  
**Status:** frozen design protocol; no policy training is authorized.  
**Branch:** `scientific_recovery_v2`  
**Motivation:** Phase 2IA4 and Phase 2IA5 both established that the present
development policies do not routinely form the prerequisite chain. This
protocol tests task feasibility before any further efficacy experiment.

## 1. Question and strict boundary

The sole question is:

> Can the unchanged 3DOF environment admit a sustained cooperative chain
> under a transparent, deterministic controller, without silently treating
> oracle state as a deployable observation?

This is not a test of EA-RG-MAPPO, Role-Gate, MAPPO, learning, recovery,
survival, success rate, or paper headline performance. No checkpoint is loaded
and no agent parameter is updated.

The canonical recovery endpoint, canonical training protocol, canonical seeds,
and all prior development artifacts remain untouched. Phase 3A remains NO-GO.

## 2. Frozen environment conditions

All probes use the existing 3DOF environment without source changes:

- three fixed UAV roles and their existing dynamics, sensing, communication,
  action table, reward-independent transition rules, and terminal conditions;
- `max_steps=260`, `attack_hold_steps=4`;
- target policy `straight`;
- communication range scale `1.0`, dropout `0.30`, delay `2`;
- strict target sensing and agent target-information bottleneck enabled;
- no node failure, no random policy, no learned control, and no altered
  initialization distribution;
- development-only feasibility seeds `601, 602, 603`;
- 100 deterministic episodes per controller × seed, for 600 episodes total.

Episode IDs are pre-registered as:

```text
610000 + 10000 * controller_index + 1000 * seed_index + episode_index
```

where `controller_index` is 0 for structural and 1 for legal-observation
controller and `seed_index` is 0, 1, 2 for 601, 602, 603.

## 3. Two controllers

### F0: structural controller (diagnostic oracle)

F0 is a fixed proportional-pursuit guidance law using simulator target state
only to establish *geometric/dynamic reachability*. It never claims deployable
observability, never trains, and is separately labelled `ORACLE_STRUCTURAL` in
every output.

### F1: legal-observation controller

F1 uses only each agent's legal observation vector and existing local target
cache semantics. It applies the same fixed guidance computation to each
agent's own legal target estimate; when no target information is available, it
uses a deterministic neutral search action. It does not read simulator target
position/velocity in its action-selection path.

F0 passing alone means only that the environment geometry is reachable. A
future learning task may be considered only if F1 also passes.

## 4. Pre-registered feasibility endpoint and gate F

The endpoint is **four consecutive `chain_closed` observations before step
220**. This is a feasibility endpoint, not the strict recovery endpoint.

For each controller independently, Gate F passes only when all hold:

1. at least 40 of 300 episodes satisfy the endpoint;
2. endpoint episodes occur in at least two of the three seeds;
3. at least two seeds each contribute at least 10 endpoint episodes;
4. raw timestep traces cover all episodes and independently reproduce the
   endpoint;
5. for F1, an information-access audit confirms that action selection reads
   only legal observation/cache quantities.

No performance number, return, terminal label, or operational post-failure
field may be substituted for this gate.

## 5. Interpretation matrix

| F0 structural | F1 legal-observation | Interpretation | Next action |
|---|---|---|---|
| FAIL | any | Present task is structurally infeasible under its nominal dynamics | Stop; do not train; create a scientific redesign proposal if desired. |
| PASS | FAIL | Geometry is reachable but observation/information task is not | Stop; do not train; audit information/task construction. |
| PASS | PASS | A stable chain is demonstrably feasible without a learned policy | A separate development-task design protocol may be proposed. |

This protocol produces no `KEEP`/`REMOVE ROLE-GATE` decision. Role-Gate stays
`UNRESOLVED` even if both feasibility gates pass.

## 6. Implementation and launch safeguards

Before a feasibility run, an independent executor audit must prove:

- no call to a checkpoint loader or optimizer;
- F1 controller's action routine does not access simulator `red_pos`,
  `red_speed`, `red_heading`, or `red_gamma`;
- output files are under a new `results/development/phase2ia6_task_feasibility`
  namespace and refuse overwrite;
- deterministic replay and endpoint reconstruction tests pass;
- a launch record is committed before outcomes exist.

No source, environment, or protocol modification may be made after the first
formal feasibility output appears. No training is authorized by a Gate F pass.
