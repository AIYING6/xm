# Robustness protocol v1.5 tests: module-copy safety + extended scenario
# registry across the three formal evaluation chains (sweep / happo / mappo).
from __future__ import annotations

import hashlib
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AB_ROOT = Path(r"D:/Code/Codex/ri_gmappo_uav_ablation_v1.5")
sys.path.insert(0, str(ROOT))

import scripts.evaluate_robustness_v1_5 as rob  # noqa: E402

NEW_KEYS = [
    "dropout050_delay2_relay_failure",
    "dropout070_delay2_relay_failure",
    "dropout030_delay4_relay_failure",
    "dropout030_delay8_relay_failure",
    "dropout070_delay8_relay_failure_early",
]
PARAMS = {
    "dropout050_delay2_relay_failure": (0.50, 2, 1, 40, 80),
    "dropout070_delay2_relay_failure": (0.70, 2, 1, 40, 80),
    "dropout030_delay4_relay_failure": (0.30, 4, 1, 40, 80),
    "dropout030_delay8_relay_failure": (0.30, 8, 1, 40, 80),
    "dropout070_delay8_relay_failure_early": (0.70, 8, 1, 25, 80),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def test_entry_expected_files_exist() -> None:
    for entry, (_, _, expected) in rob.ENTRY_MODULES.items():
        assert expected.exists(), (entry, expected)


def test_extended_registry_from_ablation_has_new_keys(monkeypatch) -> None:
    # --entry sweep imports the registry from the ABLATION worktree
    monkeypatch.setattr(sys, "path", [str(ROOT)] + [p for p in sys.path if p not in (str(ROOT), str(AB_ROOT))])
    extended = rob.build_extended_scenarios(rob.AB_ROOT)
    for k in NEW_KEYS:
        assert k in extended, k
    for k in ("dropout030_delay2_relay_failure", "relay_failure", "scout_failure"):
        assert k in extended, k


def test_new_scenario_params_match_protocol() -> None:
    extended = rob.build_extended_scenarios(rob.AB_ROOT)
    for k, (dropout, delay, agent, start, dur) in PARAMS.items():
        s = extended[k]
        assert s.communication_dropout_prob == dropout, k
        assert s.message_delay_steps == delay, k
        assert s.failed_blue_agent == agent, k
        assert s.node_failure_start_step == start, k
        assert s.node_failure_duration_steps == dur, k


def test_sweep_module_copied_file_guard() -> None:
    # the ablation worktree copy of the sweep module must be the one patched
    sys.path.insert(0, str(AB_ROOT))
    mod = importlib.import_module("scripts.evaluate_3d_checkpoint_sweep")
    expected = rob.AB_ROOT / "scripts/evaluate_3d_checkpoint_sweep.py"
    assert Path(mod.__file__).resolve() == expected.resolve()
    assert sha256(expected) == sha256(Path(mod.__file__))


def test_inject_extended_into_entry_module(monkeypatch) -> None:
    # verify identity: after inject, module.SCENARIOS IS the extended registry
    for entry in ("sweep", "happo", "mappo"):
        scripts_root, mod_name, expected_file = rob.ENTRY_MODULES[entry]
        monkeypatch.setattr(sys, "path", [str(scripts_root)] + [p for p in sys.path if p not in (str(ROOT), str(AB_ROOT))])
        extended = rob.build_extended_scenarios(scripts_root)
        module = importlib.import_module(mod_name)
        assert Path(module.__file__).resolve() == expected_file.resolve(), entry
        module.SCENARIOS = extended
        assert module.SCENARIOS is extended, f"{entry}: identity not injected"
        for k in NEW_KEYS:
            assert k in module.SCENARIOS, (entry, k)


def test_make_eval_args_uses_injected_registry_sweep() -> None:
    # the frozen sweep make_eval_args must resolve a NEW key after injection
    sys.path.insert(0, str(AB_ROOT))
    extended = rob.build_extended_scenarios(rob.AB_ROOT)
    mod = importlib.import_module("scripts.evaluate_3d_checkpoint_sweep")
    mod.SCENARIOS = extended
    from types import SimpleNamespace

    args = SimpleNamespace(
        episodes=2, eval_batch_size=1, base_seed=946804,
        target_policy="straight", strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        target_prior_position=(10_000.0, 0.0, 5_000.0),
        max_target_message_age_steps=80, min_target_confidence=0.2,
        attack_hold_steps=4, min_success_step=0,
        graph_relation_ablation="none", graph_message_ablation="none",
        graph_input_ablation="none", multi_relation_global_residual_weight=1.0,
        device="cpu",
    )
    cand = mod.Candidate(
        graph_encoder="multi_relation", train_seed=0,
        checkpoint=ROOT / "actor_critic_update_0700.pt", update=700,
    )
    ea = mod.make_eval_args(args, cand, "dropout070_delay8_relay_failure_early")
    assert ea.communication_dropout_prob == 0.70
    assert ea.message_delay_steps == 8
    assert ea.failed_blue_agent == 1
    assert ea.node_failure_start_step == 25
