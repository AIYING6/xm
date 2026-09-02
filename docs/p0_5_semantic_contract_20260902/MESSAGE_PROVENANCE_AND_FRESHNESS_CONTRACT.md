# Message provenance and freshness contract

`m = (objective_id, target_estimate, source_scout, t_sense, relay_route, t_receive, age, validity)`, where `age = t_now - t_sense`. A terminal may use support iff `valid == true`, `age <= tau_max`, source/relay fields match an active legal route, and the objective remains outstanding.

Failed-edge packets are not created. Cache updates reject packets whose legal edge is masked. Repeated forwarding preserves earliest sensing time and route history; duplicates are deterministically deduplicated by `(objective_id, source_scout, t_sense)`. A route switch changes provenance but never makes stale support fresh. `tau_max` is a physical parameter to freeze from scripted feasibility geometry before P1, not a performance-tuned learner knob.
