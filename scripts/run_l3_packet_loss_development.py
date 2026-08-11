"""L3 packet-loss development progression."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from dataclasses import asdict, replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from envs.uav_intercept_3d_env import ROLE_ATTACKER, ROLE_INTERCEPTOR  # noqa: E402
from scripts import run_new_project_l0_single_interceptor as l0  # noqa: E402
from scripts.run_tli1_l0_reward_development import reward_cfg  # noqa: E402

OUT = ROOT / "results" / "l3_packet_loss_development"
TRAIN_SEEDS = (8701, 8702)
EVAL_SEEDS = tuple(range(870_000, 870_032))
UPDATES = 60
HORIZON = 180
PROTOCOL = "L3_PACKET_LOSS_DEVELOPMENT_V1"


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def cfg(seed: int, out_dir: Path, updates: int = UPDATES):
    # None selects the environment's frozen Scout/Relay/Attacker defaults.
    return replace(
        reward_cfg(seed, out_dir, updates=updates),
        num_blue=3,
        blue_types=None,
        graph_encoder="no_graph",
        continuous_guidance_action_interface=True,
        role_specific_actor_heads=True,
        communication_range_scale=0.5,
        communication_dropout_prob=0.3,
        message_delay_steps=0,
        radar_dropout_prob=0.0,
        strict_target_sensing=True,
        agent_target_info_bottleneck=False,
        mission_reward_alignment_v1_enabled=True,
        protocol_version=PROTOCOL,
        run_id=f"l3_packet_loss_seed{seed}",
    )


def _continuous_from_legacy(env, raw, *, already_guidance: bool = False) -> np.ndarray:
    vals = np.asarray(raw).reshape(-1)
    out = np.zeros((env.config.num_blue, 3), dtype=np.float32)
    for i, value in enumerate(vals[: env.config.num_blue]):
        value = int(value)
        mapped = value if already_guidance else l0.convert_oracle_action(value)
        flight = mapped % l0.GUIDANCE_FLIGHT_ACTION_DIM
        out[i, :2] = l0.GUIDANCE_ACTION_TABLE[flight]
        out[i, 2] = 1.0 if mapped >= l0.GUIDANCE_FLIGHT_ACTION_DIM else -1.0
    return out


def episode(run_cfg, seed: int, mode: str, agent=None) -> dict:
    env = l0.make_env(run_cfg, seed, training=False)
    obs, share, graph = env.reset()
    rng = np.random.default_rng(seed + 41)
    attacker_ids = [i for i, typ in enumerate(env.config.blue_types) if typ.role in {ROLE_ATTACKER, ROLE_INTERCEPTOR}]
    entry = False
    while True:
        if mode == "random":
            action = np.column_stack((rng.uniform(-1, 1, env.config.num_blue), rng.uniform(-1, 1, env.config.num_blue), rng.choice([-1.0, 1.0], env.config.num_blue))).astype(np.float32)
        elif mode == "scripted":
            legacy = np.zeros(env.config.num_blue, dtype=np.int64)
            for i in attacker_ids:
                legacy[i] = int(l0.heuristic_action(obs[i : i + 1])[0])
            action = _continuous_from_legacy(env, legacy, already_guidance=True)
        elif mode == "oracle":
            action = _continuous_from_legacy(env, l0.scripted_oracle_actions(env))
        else:
            action = np.asarray(l0.agent_actions(agent, obs, share, graph), dtype=np.float32).reshape(env.config.num_blue, 3)
        # Only the attacker/interceptor has the mission commit action.  Masking
        # is applied identically to learned and transparent policies.
        for i, typ in enumerate(env.config.blue_types):
            if typ.role not in {ROLE_ATTACKER, ROLE_INTERCEPTOR}:
                action[i, 2] = -1.0
        entry = entry or any(bool(env._in_true_standoff_envelope(i, env.config.blue_types[i])) for i in attacker_ids)
        obs, share, graph, _reward, dones, info = env.step(action)
        if bool(np.all(dones)):
            final = l0.outcome(info)
            neutral = final == "NEUTRALIZED" and int(info["step"]) <= HORIZON
            return {"mode": mode, "episode_seed": seed, "final_outcome": final,
                    "geometry_entry": int(entry), "neutralized_by_180": int(neutral),
                    "rmtn180": int(info["step"]) if neutral else HORIZON,
                    "collision": int(final == "COLLISION"), "constraint_failure": int(final == "CONSTRAINT_FAILURE")}


def main() -> None:
    if OUT.exists() and (OUT / "episode_outcomes.csv").exists():
        raise FileExistsError(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    template = cfg(TRAIN_SEEDS[0], OUT / "template", updates=1)
    (OUT / "L3_MANIFEST.json").write_text(json.dumps({
        "status": "L3_PACKET_LOSS_DEVELOPMENT",
        "performance_use_prohibited": True, "source_commit": source_commit(),
        "training_seeds": list(TRAIN_SEEDS), "evaluation_seeds": list(EVAL_SEEDS), "updates": UPDATES,
        "only_added_complexity": "communication dropout 0.3; range scale 0.5 retained",
        "communication_range_scale": 0.5,
        "communication_dropout_prob": 0.3, "message_delay_steps": 0, "config": asdict(template),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trained = []
    for seed in TRAIN_SEEDS:
        run = OUT / f"l3_packet_loss_seed{seed}"
        run_cfg = cfg(seed, run)
        ckpt = run / "actor_critic_latest.pt"
        if not ckpt.exists():
            l0.train_ri_gmappo(run_cfg)
        trained.append((f"l3_packet_loss_seed{seed}", run_cfg, l0.load_agent(run_cfg, ckpt)))
    rows = []
    eval_cfg = cfg(TRAIN_SEEDS[0], OUT / "template", updates=1)
    for seed in EVAL_SEEDS:
        for mode in ("random", "scripted", "oracle"):
            rows.append(episode(eval_cfg, seed, mode))
        for name, _run_cfg, agent in trained:
            rows.append({**episode(eval_cfg, seed, name, agent), "mode": name})
    with (OUT / "episode_outcomes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for mode in sorted({r["mode"] for r in rows}):
        group = [r for r in rows if r["mode"] == mode]
        summary.append({"mode": mode, "episodes": len(group), "geometry_entry_rate": float(np.mean([r["geometry_entry"] for r in group])),
                        "neutralization_rate": float(np.mean([r["neutralized_by_180"] for r in group])), "rmtn180": float(np.mean([r["rmtn180"] for r in group])),
                        "collision_rate": float(np.mean([r["collision"] for r in group])), "constraint_failure_rate": float(np.mean([r["constraint_failure"] for r in group]))})
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    learned = [r for r in summary if r["mode"].startswith("l3_packet_loss")]
    random_row = next(r for r in summary if r["mode"] == "random")
    positive = [r for r in learned if r["geometry_entry_rate"] > 0 and r["neutralization_rate"] > random_row["neutralization_rate"] and r["rmtn180"] < HORIZON]
    if len(positive) == len(TRAIN_SEEDS):
        verdict = "L3_PACKET_LOSS_LEARNING_SIGNAL_RETAINED"
    elif len(positive) == 0:
        verdict = "L3_PACKET_LOSS_NO_GO__PACKET_DELIVERY_BREAKPOINT"
    else:
        verdict = "L3_PACKET_LOSS_PARTIAL_DEGRADATION"
    payload = {"verdict": verdict, "summary": summary, "performance_use_prohibited": True}
    (OUT / "L3_VERDICT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
