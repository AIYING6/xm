# LAG/JSBSim Migration Probe

Generated: 2026-07-16T22:22:13

Purpose:

```text
Check whether the local LAG copy can support the next EA-RG-MAPPO-S migration step.
This probe does not claim 6DOF validation; it separates reusable interfaces from current blockers.
```

## Summary

| Item | Value |
|---|---|
| LAG root | `C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG` |
| Missing required paths | 1 |
| Failed imports | 1 |
| Synthetic graph smoke rows | 400 |
| Real JSBSim status | blocked: envs/JSBSim/data submodule missing |

## Path and Import Checks

| Item | Status | Detail |
|---|---|---|
| LAG root | present | `directory: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG` |
| README | present | `file: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\README.md` |
| git submodule manifest | present | `file: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\.gitmodules` |
| MultipleCombat env | present | `file: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\envs\JSBSim\envs\multiplecombat_env.py` |
| MultipleCombat task | present | `file: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\envs\JSBSim\tasks\multiplecombat_task.py` |
| Base env | present | `file: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\envs\JSBSim\envs\env_base.py` |
| JSBSim simulator wrapper | present | `file: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\envs\JSBSim\core\simulatior.py` |
| JSBSim data submodule | missing | `not found: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\envs\JSBSim\data` |
| LAG model directory | present | `directory: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\envs\JSBSim\model` |
| LAG configs | present | `directory: C:\Users\96251\Documents\Codex\2026-07-12\ni\work\LAG\envs\JSBSim\configs` |
| import config | ok | `module imported without instantiating JSBSim env` |
| import envs.JSBSim.envs.multiplecombat_env | failed | `ModuleNotFoundError: No module named 'envs.JSBSim.human_task'` |
| import envs.JSBSim.tasks.multiplecombat_task | ok | `module imported without instantiating JSBSim env` |

## Interface Observations

| Field | Observed value |
|---|---|
| task_class | `MultipleCombatTask` |
| action_space_line | `self.action_space = spaces.MultiDiscrete([41, 41, 41, 30])` |
| obs_length_line | `self.obs_length = 9 + (self.num_agents - 1) * 6` |
| share_obs_line | `self.share_observation_space = spaces.Box(low=-10, high=10., shape=(self.num_agents * self.obs_length,))` |
| reward_classes | `AltitudeReward, EventDrivenReward, MissilePostureReward, PostureReward` |
| termination_classes | `ExtremeState, LowAltitude, Overload, SafeReturn, Timeout` |
| env_step_signature | `self, action: np.ndarray` |
| env_reset_signature | `self` |
| base_state_pack_line | `state = np.hstack([self.task.get_obs(self, agent_id) for agent_id in self.agents.keys()])` |
| load_simulator_line | `from ..core.simulatior import AircraftSimulator, BaseSimulator` |
| jsbsim_data_line | `self.jsbsim_exec = jsbsim.FGFDMExec(os.path.join(get_root_dir(), 'data'))` |
| position_getter | `def get_position(self):` |
| velocity_getter | `def get_velocity(self):` |
| attitude_getter | `def get_rpy(self):` |
| synthetic_graph_smoke_rows | `400` |
| real_jsbsim_status | `blocked: envs/JSBSim/data submodule missing` |

## Migration Interpretation

```text
Reusable now:
1. MultipleCombat environment/task files are present.
2. The simulator wrapper exposes position, velocity, and attitude getters that can feed a 6DOF role graph.
3. The existing synthetic LAG graph smoke test confirms node/edge tensor construction is numerically stable.

Blocked now:
1. Real JSBSim environment reset is blocked if envs/JSBSim/data is missing.
2. Current 2D action head cannot be reused directly because LAG uses MultiDiscrete aircraft controls.
3. A real 6DOF result still requires simulator data, reset/step smoke test, and new evaluation metrics.
```

## Next Minimal Step

```text
After installing/updating the JSBSim data submodule, run a real MultipleCombatEnv reset/one-step probe.
Only after that succeeds should we adapt EA-RG-MAPPO-S actor inputs or start any 6DOF training.
```
