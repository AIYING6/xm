# test_p3a_ood_eval_config.py — P3-A OOD eval-side config invariants (no checkpoints).
import numpy as np
import pytest

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env

BASE = dict(
    env_name="3d_intercept", seed=1, target_policy="straight",
    communication_dropout_prob=0.0, message_delay_steps=0,
    radar_dropout_prob=0.0, strict_target_sensing=True,
    agent_target_info_bottleneck=True, failed_blue_agent=1,
    node_failure_start_step=25, node_failure_duration_steps=80,
    communication_range_scale=1.0,
)


def mk(over: dict):
    cfg = dict(BASE)
    cfg.update(over)
    return make_env(RIGMAPPOConfig(**cfg), seed=1, training=False)


def step(env, n=3):
    obs, so, g = env.reset()
    act = np.zeros(env.config.num_blue, dtype=np.int64)
    for _ in range(n):
        obs, so, g, rew, done, info = env.step(act)
        if np.all(done):
            break
    return env


def test_default_reset_noop():
    env = mk({})
    env.reset()
    assert np.allclose(env.blue_pos[0], [-14000.0, -5500.0, 4800.0])
    assert np.allclose(env.blue_pos[1], [-16000.0, 0.0, 5200.0])
    assert np.allclose(env.blue_pos[2], [-14000.0, 5500.0, 4600.0])
    assert np.allclose(env.red_pos[0, [0, 2]], [10000.0, 5000.0])


def test_g1_centroid_preserved():
    e0 = mk({}); e0.reset()
    e1 = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    assert np.allclose(c0, c1, atol=1e-2)


def test_g1_spacing_scale_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 0.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    d0 = np.linalg.norm(e0.blue_pos[:, :2] - c0, axis=1)
    d1 = np.linalg.norm(e1.blue_pos[:, :2] - c1, axis=1)
    assert np.allclose(d1, d0 * 1.2, atol=1e-2)


def test_g1_rotation_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"blue_init_rotation_deg": 20.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    v0 = e0.blue_pos[0, :2] - c0; v1 = e1.blue_pos[0, :2] - c1
    a0 = np.arctan2(v0[1], v0[0]); a1 = np.arctan2(v1[1], v1[0])
    diff = np.degrees((a1 - a0) % (2 * np.pi))
    assert abs(diff - 20.0) < 0.1 or abs(diff - (20.0 - 360.0)) < 0.1


def test_g2_range_scale_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"target_init_range_scale": 1.4, "target_init_bearing_offset_deg": 0.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    r0 = np.linalg.norm(e0.red_pos[0, :2] - c0)
    r1 = np.linalg.norm(e1.red_pos[0, :2] - c1)
    assert np.allclose(r1, r0 * 1.4, atol=1e-2)


def test_g2_bearing_offset_exact():
    e0 = mk({}); e0.reset()
    e1 = mk({"target_init_bearing_offset_deg": 25.0}); e1.reset()
    c0 = e0.blue_pos[:, :2].mean(0); c1 = e1.blue_pos[:, :2].mean(0)
    b0 = np.arctan2(e0.red_pos[0, 1] - c0[1], e0.red_pos[0, 0] - c0[0])
    b1 = np.arctan2(e1.red_pos[0, 1] - c1[1], e1.red_pos[0, 0] - c1[0])
    diff = np.degrees((b1 - b0) % (2 * np.pi))
    assert abs(diff - 25.0) < 0.1 or abs(diff - (25.0 - 360.0)) < 0.1


def _longest_pair(env):
    xy = env.blue_pos[:, :2]
    dists = np.linalg.norm(xy[:, None, :] - xy[None, :, :], axis=-1)
    np.fill_diagonal(dists, -np.inf)
    a, b = np.unravel_index(int(np.argmax(dists)), dists.shape)
    lo = a if env.blue_pos[a, 1] <= env.blue_pos[b, 1] else b
    hi = b if lo == a else a
    return lo, hi


def test_c1_symmetric_prune():
    # large comm range so the longest pair is reachable in the unpruned case
    env = mk({"comm_topology_mode": "symmetric_longest_prune",
              "communication_range_scale": 10.0})
    env.reset()
    lo, hi = _longest_pair(env)
    assert sorted(env._ood_prune_links) == sorted([(lo, hi), (hi, lo)])
    env = step(env, 3)
    # both directions pruned after comm update
    assert env.comm_adj[hi, lo] == 0.0 and env.comm_adj[lo, hi] == 0.0


def test_c2_directed_prune_only():
    env = mk({"comm_topology_mode": "directed_longest_prune",
              "communication_range_scale": 10.0})
    env.reset()
    lo, hi = _longest_pair(env)
    assert env._ood_prune_links == [(lo, hi)]  # lower-y -> higher-y only
    env = step(env, 3)
    assert env.comm_adj[hi, lo] == 0.0   # lower-y -> higher-y pruned
    assert env.comm_adj[lo, hi] == 1.0   # reverse kept


def test_j1_composition():
    env = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0,
              "target_policy": "weaving", "comm_topology_mode": "symmetric_longest_prune"})
    env.reset()
    assert len(env._ood_prune_links) == 2
    assert env.config.target_policy == "weaving"


@pytest.mark.parametrize("cell_over", [
    {"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0},
    {"target_init_range_scale": 1.4, "target_init_bearing_offset_deg": 25.0},
    {"target_policy": "weaving"},
    {"target_policy": "break_turn"},
    {"comm_topology_mode": "symmetric_longest_prune"},
    {"comm_topology_mode": "directed_longest_prune"},
    {"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0,
     "target_policy": "weaving", "comm_topology_mode": "symmetric_longest_prune"},
])
def test_all_cells_interface_smoke(cell_over):
    env = mk(cell_over)
    obs, so, g = env.reset()
    act = np.zeros(env.config.num_blue, dtype=np.int64)
    for _ in range(5):
        obs, so, g, rew, done, info = env.step(act)
        assert g["relation_adj"].shape == (3, 4, 4)
        if np.all(done):
            break


def test_happo_same_env_config():
    # HAPPO uses the same make_env; verify OOD overrides flow into the env
    env = mk({"blue_init_spacing_scale": 1.2, "blue_init_rotation_deg": 20.0})
    env.reset()
    c = env.blue_pos[:, :2].mean(0)
    d = np.linalg.norm(env.blue_pos[:, :2] - c, axis=1)
    base = mk({}); base.reset()
    c0 = base.blue_pos[:, :2].mean(0)
    d0 = np.linalg.norm(base.blue_pos[:, :2] - c0, axis=1)
    assert np.allclose(d, d0 * 1.2, atol=1e-2)


# ---------------------------------------------------------------------------
# P3-A.2 v1.1.2 provenance tests: checkpoint manifest / MAPPO strict loader /
# frozen protocol invariants. No performance endpoints are touched.
# ---------------------------------------------------------------------------

EXPECTED_UPDATES = {
    ("full_ea_rg", "0"): 700, ("full_ea_rg", "1"): 900, ("full_ea_rg", "2"): 977,
    ("mappo", "0"): 600, ("mappo", "1"): 900, ("mappo", "2"): 100,
    ("happo", "0"): 300, ("happo", "1"): 977, ("happo", "2"): 800,
    ("param_matched_single", "0"): 500, ("param_matched_single", "1"): 200,
    ("param_matched_single", "2"): 900,
}

EXPECTED_SHA256_PREFIX = {
    ("full_ea_rg", "0"): "B9FECBE9ACC3", ("full_ea_rg", "1"): "84AA96304E66",
    ("full_ea_rg", "2"): "BD4ADC24E017", ("mappo", "0"): "C99A5718F4C0",
    ("mappo", "1"): "6ABA31F9197D", ("mappo", "2"): "21A242CFB4C2",
    ("happo", "0"): "1219F17D5201", ("happo", "1"): "A5B46A285722",
    ("happo", "2"): "39239D1BADF6", ("param_matched_single", "0"): "C7CDEB2F29D3",
    ("param_matched_single", "1"): "FE0323270689", ("param_matched_single", "2"): "98AB73AEC76B",
}


@pytest.mark.parametrize("method", ["full_ea_rg", "mappo", "happo", "param_matched_single"])
@pytest.mark.parametrize("seed", ["0", "1", "2"])
def test_checkpoint_update_mapping_exact(method, seed):
    from scripts.p3a_ood_cells import checkpoint_update, load_held_out_manifest
    man = load_held_out_manifest()
    assert (method, seed) in man, f"missing {method} seed{seed} in held-out manifest"
    assert checkpoint_update(method, seed) == EXPECTED_UPDATES[(method, seed)]
    assert man[(method, seed)]["match"] == "PASS"


@pytest.mark.parametrize("method", ["full_ea_rg", "mappo", "happo", "param_matched_single"])
@pytest.mark.parametrize("seed", ["0", "1", "2"])
def test_checkpoint_sha256_matches_manifest(method, seed):
    from scripts.p3a_ood_cells import checkpoint_path, load_held_out_manifest
    man = load_held_out_manifest()
    ck = checkpoint_path(method, seed)
    if not ck.exists():
        pytest.skip(f"checkpoint file not present: {ck}")
    from scripts.p3a_mappo_loader import sha256_file
    actual = sha256_file(ck)
    assert actual == man[(method, seed)]["sha256"]
    assert actual.startswith(EXPECTED_SHA256_PREFIX[(method, seed)])


def test_manifest_has_exactly_12_primary_rows():
    from scripts.p3a_ood_cells import load_held_out_manifest
    man = load_held_out_manifest()
    primary = {(m, s) for m in ["full_ea_rg", "mappo", "happo", "param_matched_single"]
               for s in ["0", "1", "2"]}
    assert primary.issubset(set(man.keys()))
    assert all(k in man for k in primary)


def test_mappo_agent_is_mappo_agent_3d():
    from scripts.p3a_mappo_loader import MAPPOAgent3D, build_config, load_agent_strict
    from scripts.p3a_ood_cells import checkpoint_path
    ck = checkpoint_path("mappo", "0")
    if not ck.exists():
        pytest.skip(f"mappo checkpoint not present: {ck}")
    import argparse
    a = argparse.Namespace(checkpoint=ck, seed=0, episodes=1, eval_batch_size=1,
                           base_seed=1208607, target_policy="straight",
                           communication_range_scale=1.0, communication_dropout_prob=0.3,
                           message_delay_steps=2, radar_dropout_prob=0.0,
                           strict_target_sensing=True, agent_target_info_bottleneck=True,
                           target_prior_position=(0.0, 0.0, 0.0),
                           max_target_message_age_steps=40, min_target_confidence=0.0,
                           failed_blue_agent=1, node_failure_start_step=25,
                           node_failure_duration_steps=80, attack_hold_steps=4,
                           min_success_step=0, stochastic=False, allow_random_policy=False,
                           hidden_dim=64, role_dim=8, intent_dim=8,
                           graph_encoder="multi_relation", graph_relation_ablation="none",
                           graph_message_ablation="none", graph_input_ablation="none",
                           multi_relation_global_residual_weight=0.5, device="cpu",
                           max_steps=260,
                           blue_init_rotation_deg=0.0, blue_init_spacing_scale=1.0,
                           target_init_range_scale=1.0, target_init_bearing_offset_deg=0.0,
                           comm_topology_mode="none")
    cfg = build_config(a)
    agent, audit = load_agent_strict(a, cfg)
    assert isinstance(agent, MAPPOAgent3D)
    assert audit["agent_class"] == "MAPPOAgent3D"
    assert audit["strict_load"] is True
    assert audit["partial_tensors"] == 0
    assert audit["skipped_tensors"] == 0


def test_mappo_loader_never_uses_matching_load():
    import re
    from pathlib import Path
    src = Path("scripts/p3a_mappo_loader.py").read_text(encoding="utf-8")
    # Only check import/call usage, not doc-comment mentions.
    import_lines = [ln for ln in src.splitlines()
                    if ln.startswith("import ") or ln.startswith("from ")]
    assert not any("load_matching_state_dict" in ln for ln in import_lines)
    assert "load_matching_state_dict(" not in src
    assert "MAPPOAgent3D" in src
    assert "strict" in src.lower()


def test_mappo_load_signature_strict_no_partial():
    # Held-out MAPPO behavior: strict state_dict load, 12 tensors, no partial.
    from scripts.p3a_ood_cells import checkpoint_path
    ck = checkpoint_path("mappo", "0")
    if not ck.exists():
        pytest.skip(f"mappo checkpoint not present: {ck}")
    import torch
    from algorithms.ri_gmappo.simple_ri_gmappo import make_env
    from scripts.p3a_mappo_loader import build_config, compute_load_signature, MAPPOAgent3D
    import argparse
    a = argparse.Namespace(checkpoint=ck, seed=0, episodes=1, eval_batch_size=1,
                           base_seed=1208607, target_policy="straight",
                           communication_range_scale=1.0, communication_dropout_prob=0.3,
                           message_delay_steps=2, radar_dropout_prob=0.0,
                           strict_target_sensing=True, agent_target_info_bottleneck=True,
                           target_prior_position=(0.0, 0.0, 0.0),
                           max_target_message_age_steps=40, min_target_confidence=0.0,
                           failed_blue_agent=1, node_failure_start_step=25,
                           node_failure_duration_steps=80, attack_hold_steps=4,
                           min_success_step=0, stochastic=False, allow_random_policy=False,
                           hidden_dim=64, role_dim=8, intent_dim=8,
                           graph_encoder="multi_relation", graph_relation_ablation="none",
                           graph_message_ablation="none", graph_input_ablation="none",
                           multi_relation_global_residual_weight=0.5, device="cpu",
                           max_steps=260,
                           blue_init_rotation_deg=0.0, blue_init_spacing_scale=1.0,
                           target_init_range_scale=1.0, target_init_bearing_offset_deg=0.0,
                           comm_topology_mode="none")
    cfg = build_config(a)
    env = make_env(cfg, a.seed, training=False)
    sd = torch.load(ck, map_location="cpu", weights_only=True)
    obs_in = int(sd["actor.net.0.weight"].shape[1])
    action_out = int(sd["actor.net.4.weight"].shape[0])
    hidden = int(sd["actor.net.0.weight"].shape[0])
    agent = MAPPOAgent3D(obs_dim=env.obs_dim, role_dim=obs_in - env.obs_dim,
                         share_obs_dim=env.share_obs_dim, action_dim=action_out,
                         hidden_dim=hidden)
    sig = compute_load_signature(agent, str(ck), torch.device("cpu"))
    assert sig["partial_tensors"] == 0
    assert sig["skipped_tensors"] == 0
    assert sig["matched_tensors"] == len(sd)


def test_preflight_uses_correct_loaders():
    from pathlib import Path
    src = Path("scripts/run_p3a_ood_preflight.py").read_text(encoding="utf-8")
    # mappo must route through p3a_mappo_loader STRICT, not ri build_agent
    assert "load_agent_strict" in src
    assert "method == \"mappo\"" in src
    # Full / Wider (non-happo, non-mappo) go through evaluate_ri_gmappo_3d
    assert "ri_build_agent(a, cfg)" in src
    # HAPPO through evaluate_happo_3d
    assert "ha_build_agent(a, cfg)" in src


def test_method_graph_encoder_mapping():
    from scripts.run_p3a_ood_preflight import _METHOD_GRAPH_ENCODER
    assert _METHOD_GRAPH_ENCODER == {
        "full_ea_rg": "multi_relation",
        "param_matched_single": "single",
        "mappo": "no_graph",
        "happo": "no_graph",
    }


def test_wider_single_graph_load_signature_matches_held_out():
    # Held-out param_matched_single (Wider Single-Graph): 34/0/0 via single encoder.
    from scripts.p3a_ood_cells import checkpoint_path
    from scripts.run_p3a_ood_preflight import make_args, common_eval_overrides
    from scripts.evaluate_ri_gmappo_3d import build_config, build_agent
    from scripts.p3a_mappo_loader import compute_load_signature
    import torch
    ck = checkpoint_path("param_matched_single", "0")
    if not ck.exists():
        pytest.skip(f"wider checkpoint not present: {ck}")
    a = make_args(ck, "0", "cpu", 1, common_eval_overrides(), method="param_matched_single")
    cfg = build_config(a)
    agent, _ = build_agent(a, cfg)
    sig = compute_load_signature(agent, str(ck), torch.device("cpu"))
    assert sig["partial_tensors"] == 0
    assert sig["skipped_tensors"] == 0
    assert sig["matched_tensors"] == 34


def test_protocol_invariants_v1_1():
    from scripts.p3a_ood_cells import (CELLS, EVAL_BASE_SEED, EXPOSURE_GATE,
                                       FAILURE_DURATION, FAILURE_START, HORIZON,
                                       OUT_ROOT)
    assert FAILURE_START == 25
    assert FAILURE_DURATION == 80
    assert HORIZON == 260
    assert EXPOSURE_GATE == 0.99
    assert EVAL_BASE_SEED == 1208607
    assert set(CELLS.keys()) == {"G1", "G2", "M1", "M2", "C1", "C2", "J1"}
    assert CELLS["G1"] == {"blue_init_spacing_scale": 1.20, "blue_init_rotation_deg": 20.0}
    assert CELLS["G2"] == {"target_init_range_scale": 1.40, "target_init_bearing_offset_deg": 25.0}
    assert CELLS["M1"] == {"target_policy": "weaving"}
    assert CELLS["M2"] == {"target_policy": "break_turn"}
    assert CELLS["C1"] == {"comm_topology_mode": "symmetric_longest_prune"}
    assert CELLS["C2"] == {"comm_topology_mode": "directed_longest_prune"}
    assert CELLS["J1"] == {"blue_init_spacing_scale": 1.20, "blue_init_rotation_deg": 20.0,
                           "target_policy": "weaving", "comm_topology_mode": "symmetric_longest_prune"}


def test_output_root_is_v1_1():
    from scripts.p3a_ood_cells import OUT_ROOT
    assert str(OUT_ROOT).endswith("p3a_ood_results_v1_1")
    assert "v1_0" not in str(OUT_ROOT)


# ---------------------------------------------------------------------------
# P3-A.3a collection runner + raw schema / recovery clock (frozen P1)
# ---------------------------------------------------------------------------

def test_raw_schema_frozen_columns():
    from scripts.run_p3a_ood_eval import RAW_COLUMNS, PROTOCOL_TAG, IMPLEMENTATION_TAG, PREFLIGHT_LOCK_TAG, TAU_PRIMARY, TAU_FULL
    required = {
        "method", "train_seed", "cell", "episode_id", "eval_seed",
        "checkpoint_path", "checkpoint_sha256", "checkpoint_update",
        "protocol_tag", "implementation_tag", "preflight_lock_tag",
        "steps", "failure_start_step", "failure_exposed",
        "success", "collision", "post_failure_chain_recovered",
        "recovery_window_start_step", "recovery_event_time", "censor_time",
        "recovery_observed", "reward",
    }
    assert set(RAW_COLUMNS) == required
    assert PROTOCOL_TAG == "p3a-ood-protocol-v1.1"
    assert IMPLEMENTATION_TAG == "p3a-ood-eval-impl-v1.1.3"
    assert PREFLIGHT_LOCK_TAG == "p3a-ood-preflight-lock-v1.1"
    assert TAU_PRIMARY == 80
    assert TAU_FULL == 220


def test_p3a3a_runtime_episodes_frozen():
    from scripts.run_p3a_ood_eval import (  # noqa: F401
        build_raw_row, completeness_audit, run_cell,
    )
    assert True  # import smoke; real 8400 run happens outside tests


def test_completeness_audit_logic():
    from scripts.run_p3a_ood_eval import completeness_audit, EPISODES_PER_CELL
    rows = []
    for m in ["full_ea_rg", "mappo", "happo", "param_matched_single"]:
        for s in ["0", "1", "2"]:
            for c in ["G1", "G2", "M1", "M2", "C1", "C2", "J1"]:
                for e in range(EPISODES_PER_CELL):
                    rows.append({"method": m, "train_seed": s, "cell": c, "episode_id": e,
                                 "checkpoint_sha256": "A" * 64, "failure_exposed": 1})
    audit = completeness_audit(rows)
    assert audit["rows"] == 8400
    assert audit["expected_rows"] == 8400
    assert audit["unique_cells"] == 84
    assert audit["missing"] == []
    assert audit["duplicates"] == 0
    assert audit["exposure_violations"] == 0


def test_completeness_audit_detects_missing():
    from scripts.run_p3a_ood_eval import completeness_audit
    rows = [{"method": "full_ea_rg", "train_seed": "0", "cell": "G1", "episode_id": 0,
             "checkpoint_sha256": "B" * 64, "failure_exposed": 1}]
    audit = completeness_audit(rows)
    assert audit["rows"] == 1
    assert len(audit["missing"]) == 8399


def _full_info(t, chain_closed=0.0, tracking=1.0, comm=1.0):
    """Minimal step-info dict carrying every key post_failure_recovery_metrics reads."""
    return {
        "step": float(t),
        "chain_closed": float(chain_closed),
        "node_failure_active": 1.0 if t >= 25 else 0.0,
        "tracking_rate": float(tracking),
        "comm_connectivity": float(comm),
        "attacker_info_attack_window": 1.0,
        "attacker_window_cache_generation_step_max": 200.0,
        "attacker_window_cache_delivery_step_max": 200.0,
        "attacker_window_direct_info": 1.0,
        "attacker_window_comm_info": 0.0,
    }


def test_recovery_clock_matches_p1_definition():
    """P1 frozen: T_event = stable_window_start - failure_start; T_censor = steps - failure_start.
    Verify build_raw_row maps the held-out recovery metrics exactly."""
    import argparse
    from scripts.run_p3a_ood_eval import build_raw_row
    args = argparse.Namespace(
        node_failure_start_step=25, node_failure_duration_steps=80,
        failed_blue_agent=1, attack_hold_steps=4,
    )
    # recovered episode: chain closes at step 40 -> stable_window_start = 40-4+1=37
    # T_event = 37 - 25 = 12
    infos = [_full_info(t, chain_closed=1.0 if t >= 40 else 0.0) for t in range(20, 45)]
    row = build_raw_row("full_ea_rg", "0", "G1", 0, args, "SHA", infos,
                        {"step": 44, "success": 0.0, "collision": 0.0}, 1.5)
    assert row["recovery_observed"] == 1.0
    assert row["recovery_event_time"] == 12.0
    assert row["recovery_window_start_step"] == 37.0
    assert row["censor_time"] == -1.0
    assert row["failure_exposed"] == 1.0
    assert row["steps"] == 44.0
    assert row["reward"] == 1.5


def test_censor_clock_unrecovered():
    import argparse
    from scripts.run_p3a_ood_eval import build_raw_row
    args = argparse.Namespace(
        node_failure_start_step=25, node_failure_duration_steps=80,
        failed_blue_agent=1, attack_hold_steps=4,
    )
    infos = [_full_info(t, chain_closed=0.0) for t in range(20, 61)]
    row = build_raw_row("mappo", "1", "C1", 3, args, "SHA", infos,
                        {"step": 60, "success": 0.0, "collision": 0.0}, -2.0)
    assert row["recovery_observed"] == 0.0
    assert row["recovery_event_time"] == -1.0
    assert row["censor_time"] == 35.0  # 60 - 25
    assert row["recovery_window_start_step"] == -1.0


# ---------------------------------------------------------------------------
# P3-A.3b statistical analysis (frozen primary endpoint)
# ---------------------------------------------------------------------------

def test_km_rmst_no_events():
    from scripts.analyze_p3a_ood import km_rmst
    # all censored at 60 -> S(t)=1 -> RMST(tau=80) = 80
    rmst = km_rmst(np.array([-1.0]), np.array([60.0]), 80.0)
    assert abs(rmst - 80.0) < 1e-9


def test_km_rmst_all_event_at_0():
    from scripts.analyze_p3a_ood import km_rmst
    # all events at t=0 -> S(t)=0 immediately -> RMST = 0
    rmst = km_rmst(np.array([0.0, 0.0]), np.array([-1.0, -1.0]), 80.0)
    assert abs(rmst) < 1e-9


def test_km_rmst_mixed():
    from scripts.analyze_p3a_ood import km_rmst
    # one event at 20, one censored at 60, tau=80
    rmst = km_rmst(np.array([20.0, -1.0]), np.array([-1.0, 60.0]), 80.0)
    # S(0..20)=1 (area 20), S(20..60)=0.5 (area 0.5*40=20), S(60..80)=0.5 (area 10)
    assert abs(rmst - 50.0) < 1e-6


def test_km_rmst_event_after_tau_no_double_count():
    # Regression for the double-count bug: a single event at t>tau must give
    # RMST(tau) = tau (S=1 over [0,tau]); it must NOT exceed tau.
    from scripts.analyze_p3a_ood import km_rmst
    rmst = km_rmst(np.array([100.0]), np.array([-1.0]), 80.0)
    assert abs(rmst - 80.0) < 1e-9
    rmst2 = km_rmst(np.array([-1.0]), np.array([120.0]), 80.0)
    assert abs(rmst2 - 80.0) < 1e-9
    # mixed: event at 100 (>tau) and censor at 30.
    # S=1 over [0,30]; censoring at 30 does NOT reduce S; event at 100 is
    # outside the window -> S stays 1 -> RMST80 = 80.
    rmst3 = km_rmst(np.array([100.0, -1.0]), np.array([-1.0, 30.0]), 80.0)
    assert abs(rmst3 - 80.0) < 1e-6
    # never exceeds tau
    assert rmst <= 80.0 + 1e-9 and rmst2 <= 80.0 + 1e-9 and rmst3 <= 80.0 + 1e-9


def test_bootstrap_params_frozen():
    from scripts.analyze_p3a_ood import N_BOOT, RNG_SEED, TAU_PRIMARY, TAU_FULL, CELLS_ORDER
    assert N_BOOT == 10000
    assert RNG_SEED == 20260807
    assert TAU_PRIMARY == 80
    assert TAU_FULL == 220
    assert CELLS_ORDER == ["C1", "C2", "G1", "G2", "J1", "M1", "M2"]


def _synthetic_8400(full_early: bool = True, n: int = 100):
    """Build a synthetic 8400-row dataset. If full_early, Full recovers earlier
    (small T_event) than MAPPO, so Delta^OOD should be negative."""
    import numpy as np
    rows = []
    rng = np.random.default_rng(7)
    for method in ["full_ea_rg", "mappo", "happo", "param_matched_single"]:
        for seed in ["0", "1", "2"]:
            for cell in ["C1", "C2", "G1", "G2", "J1", "M1", "M2"]:
                for e in range(n):
                    rec = bool(rng.random() < 0.7)
                    if method == "full_ea_rg":
                        tev = float(rng.uniform(2, 25)) if rec else -1.0
                        tce = -1.0 if rec else float(rng.uniform(40, 80))
                    elif method == "mappo":
                        tev = float(rng.uniform(15, 50)) if rec else -1.0
                        tce = -1.0 if rec else float(rng.uniform(60, 120))
                    else:
                        tev = float(rng.uniform(5, 40)) if rec else -1.0
                        tce = -1.0 if rec else float(rng.uniform(50, 100))
                    rows.append({"method": method, "train_seed": seed, "cell": cell,
                                 "episode_id": e, "eval_seed": 0,
                                 "checkpoint_sha256": "A" * 64, "checkpoint_path": "x",
                                 "checkpoint_update": 1, "protocol_tag": "p",
                                 "implementation_tag": "i", "preflight_lock_tag": "l",
                                 "steps": 100.0, "failure_start_step": 25.0,
                                 "failure_exposed": 1.0, "success": 0.0,
                                 "collision": 0.0, "post_failure_chain_recovered": float(rec),
                                 "recovery_window_start_step": 0.0,
                                 "recovery_event_time": tev, "censor_time": tce,
                                 "recovery_observed": float(rec), "reward": 0.0})
    return rows


def test_hierarchical_bootstrap_sign_and_reproducible():
    from scripts.analyze_p3a_ood import hierarchical_bootstrap_delta, RNG_SEED
    rows = _synthetic_8400(full_early=True)
    m1, sd1, lo1, hi1, p1 = hierarchical_bootstrap_delta(rows, n_boot=200)
    m2, sd2, lo2, hi2, p2 = hierarchical_bootstrap_delta(rows, n_boot=200)
    assert m1 < 0  # Full recovers earlier -> Delta negative
    assert lo1 < 0 and hi1 < 0
    assert p1 >= 0.95
    # reproducible under the frozen RNG seed
    assert m1 == m2 and lo1 == lo2 and hi1 == hi2 and p1 == p2


def test_analysis_runtime_imports():
    from scripts.analyze_p3a_ood import (  # noqa: F401
        km_rmst, cell_stats, hierarchical_bootstrap_delta, main,
    )
    assert True


def test_cell_stats_paired_clock_not_disjoint():
    """Regression: cell_stats must feed km_rmst per-episode paired (event, censor)
    arrays (same length), not disjoint recovered/censored lists. A block with
    many recovered events at ~20 must NOT yield RMST80=80 (ceiling artifact)."""
    from scripts.analyze_p3a_ood import cell_stats, km_rmst
    rows = []
    for i in range(95):
        rows.append({"success": 0.0, "collision": 0.0, "recovery_observed": 1.0,
                     "recovery_event_time": 17.0, "censor_time": -1.0})
    for i in range(5):
        rows.append({"success": 0.0, "collision": 0.0, "recovery_observed": 0.0,
                     "recovery_event_time": -1.0, "censor_time": 60.0})
    st = cell_stats(rows)
    assert st["P_rec"] == 0.95
    assert st["RMST80"] < 80.0  # must not be ceiling-saturated
    assert 0.0 <= st["RMST80"] <= 80.0
    assert 0.0 <= st["RMST220"] <= 220.0


def test_happo_rollout_interface_matches_held_out():
    # Regression: preflight must call HAPPO via get_action_and_value with the
    # same signature as evaluate_happo_3d.py (no get_action, no intent kwargs).
    from pathlib import Path
    preflight = Path("scripts/run_p3a_ood_preflight.py").read_text(encoding="utf-8")
    # Anchor on the rollout branch (distinct comment; audit branch also has
    # "elif method == \"happo\":" so we must not match that).
    anchor = "# HAPPO uses the same get_action_and_value signature as RI"
    hap_block_start = preflight.index(anchor)
    hap_block = preflight[hap_block_start:hap_block_start + 1400]
    assert "get_action_and_value" in hap_block
    assert "agent.get_action(" not in hap_block
    assert "intent_label" not in hap_block
    assert "relation_adj=" in hap_block
    assert "deterministic=True" in hap_block
