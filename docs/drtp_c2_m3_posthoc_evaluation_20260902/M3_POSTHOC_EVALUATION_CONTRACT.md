# C2-M3 fixed post-hoc milestone evaluation contract

**Status:** `M3_E0_EVALUATION_AUTHORIZED`  
**Scope:** cloud-only checkpoint evaluation of completed C2-M3 trajectories.

This step evaluates both frozen arms (`utr_sg` and `group_weighted_utr_sg`) for
seeds 5101–5110 at all four pre-saved milestones: 125k, 250k, 375k and 500k.
It uses only the separately frozen 690000–690049 development tape. The same
base episode IDs are used under nominal, F0, early-onset, long-duration and
compound failure conditions.

The checkpoint labels are fixed before execution. They are used solely to
order training-only telemetry and task divergence in time. No result may
select or promote a checkpoint, change a training trajectory, tune an
algorithm, or alter Mainline A.

The output is a temporal-ordering gate, not an algorithm-performance claim.
It returns `M3_ACTIONABLE_MECHANISM_CANDIDATE` only if each cohort contains at
least two final rescue and two final harm trajectories under the frozen margin;
otherwise it returns `M3_NO_ACTIONABLE_MECHANISM`. Either result stops without
automatic intervention design or further training.
