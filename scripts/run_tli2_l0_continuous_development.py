"""TLI2 continuous-action L0 development training (non-evidentiary)."""

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
from scripts import run_new_project_l0_single_interceptor as base
from scripts.run_tli1_l0_reward_development import reward_cfg


OUT = ROOT / "results" / "tli2_l0_continuous_development_v6"
TRAIN_SEEDS = base.TRAIN_SEEDS
EVAL_SEEDS = base.EVAL_SEEDS
UPDATES = base.UPDATES
PROTOCOL_VERSION = "TLI2_L0_CONTINUOUS_ACTION_DEVELOPMENT_V1"


def source_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "UNAVAILABLE"


def cfg(seed: int, out_dir: Path, updates: int = UPDATES):
    return replace(
        reward_cfg(seed, out_dir, updates=updates),
        continuous_guidance_action_interface=True,
        protocol_version=PROTOCOL_VERSION,
        run_id=f"tli2_l0_continuous_seed{seed}",
    )


def _as_continuous_action(env, raw, rng):
    """Adapt legacy evaluator actions to the frozen hybrid interface."""
    arr = np.asarray(raw)
    if arr.size == 3:
        return arr.astype(np.float32).reshape(1, 3)
    value = int(arr.reshape(-1)[0])
    flight = value % base.GUIDANCE_FLIGHT_ACTION_DIM
    turn, climb = base.GUIDANCE_ACTION_TABLE[flight]
    commit = 1.0 if value >= base.GUIDANCE_FLIGHT_ACTION_DIM else -1.0
    return np.asarray([[float(turn), float(climb), commit]], dtype=np.float32)


def continuous_episode(cfg_obj, seed: int, mode: str, agent=None) -> dict:
    env = base.make_env(cfg_obj, seed, training=False)
    obs, share, graph = env.reset()
    rng = np.random.default_rng(seed + 33)
    entry = False
    while True:
        if mode == "random":
            action = np.asarray([[rng.uniform(-1.0, 1.0), rng.uniform(-1.0, 1.0),
                                  1.0 if rng.random() < 0.5 else -1.0]], dtype=np.float32)
        elif mode == "scripted":
            action = _as_continuous_action(env, base.heuristic_action(obs), rng)
        elif mode == "oracle":
            action = _as_continuous_action(env, base.convert_oracle_action(int(base.scripted_oracle_actions(env)[0])), rng)
        else:
            action = _as_continuous_action(env, base.agent_actions(agent, obs, share, graph), rng)
        entry = entry or bool(env._in_true_standoff_envelope(0, env.config.blue_types[0]))
        obs, share, graph, _reward, dones, info = env.step(action)
        if bool(np.all(dones)):
            final = base.outcome(info)
            neutral = final == "NEUTRALIZED" and int(info["step"]) <= base.RMTN_HORIZON
            return {"mode": mode, "episode_seed": seed, "final_outcome": final,
                    "geometry_entry": int(entry), "neutralized_by_180": int(neutral),
                    "rmtn180": int(info["step"]) if neutral else base.RMTN_HORIZON}


def main() -> None:
    # A prior training-only attempt may be reused for evaluator debugging;
    # never overwrite an existing episode table or verdict.
    if OUT.exists() and (OUT / "episode_outcomes.csv").exists():
        raise FileExistsError(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    template = cfg(TRAIN_SEEDS[0], OUT / "template", updates=1)
    (OUT / "TLI2_MANIFEST.json").write_text(json.dumps({
        "status": "TLI2_CONTINUOUS_ACTION_DEVELOPMENT",
        "performance_use_prohibited": True,
        "source_commit": source_commit(),
        "training_seeds": list(TRAIN_SEEDS),
        "evaluation_seeds": list(EVAL_SEEDS),
        "updates": UPDATES,
        "only_new_variable_vs_tli1": "continuous_guidance_action_interface=true",
        "config": asdict(template),
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trained = []
    for seed in TRAIN_SEEDS:
        run = OUT / f"tli2_l0_continuous_seed{seed}"
        run_cfg = cfg(seed, run)
        ckpt = run / "actor_critic_latest.pt"
        if not ckpt.exists():
            base.train_ri_gmappo(run_cfg)
        trained.append((f"tli2_l0_continuous_seed{seed}", run_cfg, base.load_agent(run_cfg, ckpt)))
    rows = []
    eval_cfg = cfg(TRAIN_SEEDS[0], OUT / "template", updates=1)
    for seed in EVAL_SEEDS:
        for mode in ("random", "scripted", "oracle"):
            rows.append(continuous_episode(eval_cfg, seed, mode))
        for name, _run_cfg, agent in trained:
            rows.append({**continuous_episode(eval_cfg, seed, name, agent), "mode": name})
    with (OUT / "episode_outcomes.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    summary = []
    for mode in sorted({r["mode"] for r in rows}):
        group = [r for r in rows if r["mode"] == mode]
        summary.append({
            "mode": mode, "episodes": len(group),
            "geometry_entry_rate": float(np.mean([r["geometry_entry"] for r in group])),
            "neutralization_rate": float(np.mean([r["neutralized_by_180"] for r in group])),
            "rmtn180": float(np.mean([r["rmtn180"] for r in group])),
        })
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summary[0])); writer.writeheader(); writer.writerows(summary)
    learned = [r for r in summary if r["mode"].startswith("tli2_l0_continuous_seed")]
    positive = [r for r in learned if r["geometry_entry_rate"] > 0 and r["neutralization_rate"] > 0 and r["rmtn180"] < 180]
    if len(positive) == len(TRAIN_SEEDS):
        verdict = "TLI2_CONTINUOUS_ACTION_ESTABLISHES_L0_LEARNING_SIGNAL"
    elif len(positive) == 0 and all(r["neutralization_rate"] == 0 for r in learned):
        verdict = "TLI2_CONTINUOUS_ACTION_NO_GO__ACTION_PARAMETERIZATION_NOT_SUFFICIENT"
    else:
        verdict = "TLI2_CONTINUOUS_ACTION_PARTIAL_UNSTABLE_SIGNAL"
    payload = {"verdict": verdict, "summary": summary, "performance_use_prohibited": True}
    (OUT / "TLI2_VERDICT.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
