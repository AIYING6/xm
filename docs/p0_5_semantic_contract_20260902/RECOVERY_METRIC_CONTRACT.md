# Recovery metric contract

At failure time `t_f`, record `L_route = t_alternate_path_active - t_f`, `L_message = t_fresh_alternate_support_arrives - t_f`, and `L_task = t_first_post_failure_progress - t_f`. Also retain path switch, rerouting decision, token arrival, cache invalidation and objective recovery events. Undefined latency is recorded as censored/unrecovered, not silently dropped.
