# Reward scale test

[{'scale': 'small', 'zero': 0.0, 'quarter_progress': 0.25, 'one_completion': 1.0, 'all_completion': 1.0, 'full_collision_density': -1.0}, {'scale': 'main', 'zero': 0.0, 'quarter_progress': 0.25, 'one_completion': 0.5, 'all_completion': 1.0, 'full_collision_density': -1.0}, {'scale': 'large', 'zero': 0.0, 'quarter_progress': 0.25, 'one_completion': 0.3333333333333333, 'all_completion': 1.0, 'full_collision_density': -1.0}]

PASS=True. Quarter progress, all-objective completion and full collision density are scale invariant. A single completion is deliberately 1/K, which prevents more objectives from multiplying team reward.
