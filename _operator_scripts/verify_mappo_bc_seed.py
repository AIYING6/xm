# verify_mappo_bc_seed.py
# Per-seed acceptance check for the MAPPO formal BC (frozen mappo-freeze-v1.5.0).
#
# Checks (immediate, per seed):
#   - mappo_bc_actor.pt exists and is readable
#   - payload keys are exactly {"actor_state", "meta"} (no critic / graph modules)
#   - actor state 100% strict-load into MAPPOAgent3D
#   - critic unchanged by the BC load (random-init critic untouched)
#   - episodes=120 / epochs=20 / obs=34 / role_dim=4 / action=27 / hidden=64
#   - pretrained_modules=actor; demo_sha256 recorded; code_commit=11fa019
#   - effective-config SHA recomputed == recorded
#   - loss/acc and actor params finite (no NaN/Inf); grad_norm finite
# Usage:
#   python verify_mappo_bc_seed.py --root <OutRoot> --seed 0
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo import RIGMAPPOConfig  # noqa: E402
from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPO3DConfig,
    MAPPOAgent3D,
    effective_config_sha256,
)

EXPECTED = {
    "episodes": 120,
    "epochs": 20,
    "obs_dim": 34,
    "role_dim": 4,
    "action_dim": 27,
    "hidden_dim": 64,
    "num_agents": 3,
    "pretrained_modules": "actor",
}
CODE_COMMIT_MARK = "11fa019"


def build_cfg(seed: int, out_dir: str) -> MAPPO3DConfig:
    """Reconstruct the exact cfg used by the formal BC (frozen env params)."""
    env_cfg = RIGMAPPOConfig(
        seed=seed,
        env_name="3d_intercept",
        num_envs=1,
        rollout_steps=1,
        updates=1,
        hidden_dim=64,
        target_policy="straight",
        target_speed=1.0,
        communication_radius=1000.0,
        strict_target_sensing=True,
        agent_target_info_bottleneck=True,
        target_prior_position=(10000.0, 0.0, 5000.0),
        max_target_message_age_steps=80,
        min_target_confidence=0.2,
        communication_dropout_prob=0.30,
        message_delay_steps=2,
        radar_dropout_prob=0.0,
        failed_blue_agent=1,
        node_failure_start_random_min=25,
        node_failure_start_random_max=70,
        node_failure_duration_steps=80,
        attack_hold_steps=4,
        min_success_step=80,
        post_loss_chain_reclosure_reward_weight=0.5,
        post_loss_chain_reclosure_min_step=80,
        safety_proximity_distance=2500.0,
        safety_proximity_penalty_weight=0.5,
        device="cpu",
    )
    return MAPPO3DConfig(env=env_cfg, device="cpu", out_dir=out_dir)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()

    seed = args.seed
    seed_dir = args.root / f"bc_seed{seed}"
    ckpt = seed_dir / "mappo_bc_actor.pt"
    log_csv = seed_dir / "bc_train_log.csv"
    eff_json = seed_dir / "effective_config.json"
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, bool(ok), detail))

    # 1. checkpoint exists and readable
    if not ckpt.exists():
        check("checkpoint exists", False, str(ckpt))
    else:
        check("checkpoint exists", True, str(ckpt))
        try:
            payload = torch.load(ckpt, map_location="cpu", weights_only=False)
            check("checkpoint readable", True)
        except Exception as e:  # noqa: BLE001
            payload = None
            check("checkpoint readable", False, str(e))

    if payload is not None:
        # 2. payload contains ONLY actor_state + meta
        keys = sorted(payload.keys())
        check("payload keys == {actor_state, meta}", keys == ["actor_state", "meta"], f"keys={keys}")
        meta = payload.get("meta", {})
        actor_state = payload.get("actor_state")
        check("actor_state is dict", isinstance(actor_state, dict))

        # 3. meta fields
        for k, v in EXPECTED.items():
            got = meta.get(k)
            check(f"meta.{k} == {v}", got == v, f"got={got!r}")
        demo_sha = meta.get("demo_sha256")
        check("meta.demo_sha256 recorded", isinstance(demo_sha, str) and len(demo_sha) == 64, f"demo_sha={demo_sha}")
        cc = meta.get("code_commit", "")
        check("meta.code_commit contains 11fa019", CODE_COMMIT_MARK in str(cc), f"code_commit={cc!r}")

        # 4. strict load + critic invariance
        cfg = build_cfg(seed, str(seed_dir))
        agent = MAPPOAgent3D(
            obs_dim=EXPECTED["obs_dim"],
            role_dim=EXPECTED["role_dim"],
            share_obs_dim=47,
            action_dim=EXPECTED["action_dim"],
            hidden_dim=EXPECTED["hidden_dim"],
        )
        critic_before = copy.deepcopy(agent.critic.state_dict())
        try:
            agent.actor.load_state_dict(actor_state)  # strict by default
            check("actor 100% strict-load", True)
        except Exception as e:  # noqa: BLE001
            check("actor 100% strict-load", False, str(e))
        critic_same = all(
            k in critic_before and torch.equal(critic_before[k], agent.critic.state_dict()[k])
            for k in critic_before
        )
        check("critic unchanged by BC load", critic_same)

        # 5. actor params == checkpoint params; finite check
        actor_params = sum(v.numel() for v in actor_state.values())
        net_params = sum(v.numel() for v in agent.actor.state_dict().values())
        check("actor param count == meta-driven net", actor_params == net_params, f"{actor_params} vs {net_params}")
        finite = all(bool(torch.isfinite(v).all()) for v in actor_state.values())
        check("actor params finite (no NaN/Inf)", finite)

        # grad_norm finite on a single mini-batch backward
        torch.manual_seed(seed)
        x = torch.randn(64, EXPECTED["obs_dim"] + EXPECTED["role_dim"])
        y = torch.randint(0, EXPECTED["action_dim"], (64,))
        out = agent.actor(x)
        loss = torch.nn.functional.cross_entropy(out, y)
        loss.backward()
        gn = sum(p.grad.detach().square().sum() for p in agent.actor.parameters() if p.grad is not None).sqrt().item()
        check("grad_norm finite", np.isfinite(gn), f"grad_norm={gn:.4g}")

        # 6. effective-config SHA recomputed == recorded
        recomputed = effective_config_sha256(cfg)
        recorded = meta.get("effective_config_sha256")
        check("effective-config SHA matches recompute", recomputed == recorded, f"rec={recomputed[:16]}… recd={str(recorded)[:16]}…")

        # 7. train log finite
        loss_ok = acc_ok = True
        if log_csv.exists():
            rows = []
            with log_csv.open("r", encoding="utf-8", newline="") as f:
                import csv as _csv
                for r in _csv.DictReader(f):
                    rows.append(r)
            loss_ok = all(np.isfinite(float(r["loss"])) for r in rows)
            acc_ok = all(np.isfinite(float(r["acc"])) for r in rows)
            check("train log epochs == 20", len(rows) == EXPECTED["epochs"], f"rows={len(rows)}")
        check("train loss finite", loss_ok)
        check("train acc finite", acc_ok)

    all_ok = all(ok for _, ok, _ in checks)

    # report
    report = [
        f"# MAPPO BC per-seed verify: seed {seed}",
        f"checkpoint sha256: {sha256(ckpt) if ckpt.exists() else 'MISSING'}",
        "",
    ]
    for name, ok, detail in checks:
        report.append(f"- [{'PASS' if ok else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))
    report.append("")
    report.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    report.append("") if all_ok else None
    report.append(f"generated: seed={seed} root={args.root}")

    notes_dir = args.root / "_bc_operator_notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / f"verify_seed{seed}.md").write_text("\n".join(report), encoding="utf-8")

    for name, ok, detail in checks:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" ({detail})" if detail else ""))
    print("OVERALL:", "PASS" if all_ok else "FAIL")
    print(f"report: {notes_dir / f'verify_seed{seed}.md'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
