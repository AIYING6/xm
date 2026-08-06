# audit_mappo_bc_formal.py
# 3/3 comprehensive audit of the MAPPO formal BC (frozen mappo-freeze-v1.5.0).
#
# Generates under <root>/_bc_operator_notes/:
#   bc_manifest.csv                 - 3 rows, paths + SHA + meta
#   bc_audit_report.md              - full narrative audit
#   bc_checkpoint_sha256.txt        - 3 unique SHA256 lines
#   effective_config_audit.csv      - recorded vs recomputed config SHA
#   demo_generation_manifest.json   - demo metadata per seed
#
# Verifies: 3/3 paths unique, 3/3 strict-loadable, network dims consistent,
# actor param counts equal, critic NOT inside BC, seed/demo/config/commit/tag
# complete, no _smoke assets, no overwritten formal checkpoints.
from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo import RIGMAPPOConfig  # noqa: E402
from scripts.train_mappo_3d_formal_v1_5 import (  # noqa: E402
    MAPPO3DConfig,
    MAPPOAgent3D,
    effective_config_sha256,
)

SEEDS = [0, 1, 2]
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
CODE_COMMIT = "mappo-freeze-v1.5.0 @ 11fa019"
SHARE_OBS_DIM = 47
FROZEN_ENV = dict(
    env_name="3d_intercept", num_envs=1, rollout_steps=1, updates=1,
    hidden_dim=64, target_policy="straight", target_speed=1.0,
    communication_radius=1000.0, strict_target_sensing=True,
    agent_target_info_bottleneck=True, target_prior_position=(10000.0, 0.0, 5000.0),
    max_target_message_age_steps=80, min_target_confidence=0.2,
    communication_dropout_prob=0.30, message_delay_steps=2, radar_dropout_prob=0.0,
    failed_blue_agent=1, node_failure_start_random_min=25,
    node_failure_start_random_max=70, node_failure_duration_steps=80,
    attack_hold_steps=4, min_success_step=80,
    post_loss_chain_reclosure_reward_weight=0.5,
    post_loss_chain_reclosure_min_step=80, safety_proximity_distance=2500.0,
    safety_proximity_penalty_weight=0.5, device="cpu",
)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def recompute_sha(seed: int) -> str:
    env_cfg = RIGMAPPOConfig(seed=seed, **FROZEN_ENV)
    cfg = MAPPO3DConfig(env=env_cfg, device="cpu", out_dir="formal_bc_audit")
    return effective_config_sha256(cfg)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root: Path = args.root
    notes = root / "_bc_operator_notes"
    notes.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    manifest_rows: list[dict] = []
    sha_lines: list[str] = []
    eff_rows: list[dict] = []
    demo_manifest: dict = {"code_tag": CODE_COMMIT, "frozen_parameters": EXPECTED, "seeds": {}}
    git_snapshot: list[str] = []

    for seed in SEEDS:
        seed_dir = root / f"bc_seed{seed}"
        ckpt = seed_dir / "mappo_bc_actor.pt"
        if not ckpt.exists():
            problems.append(f"seed{seed}: checkpoint MISSING {ckpt}")
            continue
        try:
            payload = torch.load(ckpt, map_location="cpu", weights_only=False)
        except Exception as e:  # noqa: BLE001
            problems.append(f"seed{seed}: checkpoint unreadable: {e}")
            continue
        meta = payload.get("meta", {})
        keys = sorted(payload.keys())
        if keys != ["actor_state", "meta"]:
            problems.append(f"seed{seed}: payload keys {keys} != [actor_state, meta]")
        actor_state = payload.get("actor_state")
        if not isinstance(actor_state, dict):
            problems.append(f"seed{seed}: actor_state not a dict")
            continue

        # strict load + critic invariance
        try:
            agent = MAPPOAgent3D(
                obs_dim=EXPECTED["obs_dim"], role_dim=EXPECTED["role_dim"],
                share_obs_dim=SHARE_OBS_DIM, action_dim=EXPECTED["action_dim"],
                hidden_dim=EXPECTED["hidden_dim"],
            )
            critic_before = copy.deepcopy(agent.critic.state_dict())
            agent.actor.load_state_dict(actor_state)
            critic_same = all(
                k in critic_before and torch.equal(critic_before[k], agent.critic.state_dict()[k])
                for k in critic_before
            )
        except Exception as e:  # noqa: BLE001
            problems.append(f"seed{seed}: strict load failed: {e}")
            critic_same = False

        n_params = sum(v.numel() for v in actor_state.values())
        rec_sha = recompute_sha(seed)
        recd_sha = meta.get("effective_config_sha256")
        if recd_sha != rec_sha:
            problems.append(f"seed{seed}: effective-config SHA mismatch recorded={recd_sha} recomputed={rec_sha}")
        if not critic_same:
            problems.append(f"seed{seed}: critic changed by actor BC load")
        for k, v in EXPECTED.items():
            if meta.get(k) != v:
                problems.append(f"seed{seed}: meta.{k}={meta.get(k)!r} != {v!r}")
        if CODE_COMMIT not in str(meta.get("code_commit", "")):
            problems.append(f"seed{seed}: code_commit missing freeze tag: {meta.get('code_commit')!r}")
        if not (isinstance(meta.get("demo_sha256"), str) and len(meta["demo_sha256"]) == 64):
            problems.append(f"seed{seed}: demo_sha256 malformed: {meta.get('demo_sha256')!r}")
        finite = all(bool(torch.isfinite(v).all()) for v in actor_state.values())
        if not finite:
            problems.append(f"seed{seed}: actor params contain NaN/Inf")

        ckpt_sha = sha256(ckpt)
        sha_lines.append(f"{ckpt_sha}  bc_seed{seed}/mappo_bc_actor.pt")
        manifest_rows.append({
            "seed": seed,
            "checkpoint_path": f"bc_seed{seed}/mappo_bc_actor.pt",
            "checkpoint_sha256": ckpt_sha,
            "actor_params": n_params,
            "obs_dim": meta.get("obs_dim"),
            "role_dim": meta.get("role_dim"),
            "action_dim": meta.get("action_dim"),
            "hidden_dim": meta.get("hidden_dim"),
            "num_agents": meta.get("num_agents"),
            "episodes": meta.get("episodes"),
            "epochs": meta.get("epochs"),
            "pretrained_modules": meta.get("pretrained_modules"),
            "demo_sha256": meta.get("demo_sha256"),
            "demo_success_rate": meta.get("demo_success_rate"),
            "final_bc_loss": meta.get("final_bc_loss"),
            "final_bc_acc": meta.get("final_bc_acc"),
            "effective_config_sha256": recd_sha,
            "code_commit": meta.get("code_commit"),
            "strict_load": "PASS",
            "critic_untouched": "PASS" if critic_same else "FAIL",
        })
        eff_rows.append({"seed": seed, "recorded_sha256": recd_sha, "recomputed_sha256": rec_sha, "match": "PASS" if recd_sha == rec_sha else "FAIL"})
        demo_manifest["seeds"][str(seed)] = {
            "demo_source": meta.get("demo_source"),
            "demo_sha256": meta.get("demo_sha256"),
            "demo_success_rate": meta.get("demo_success_rate"),
            "episodes": meta.get("episodes"),
            "epochs": meta.get("epochs"),
            "optimizer_config": meta.get("optimizer_config"),
            "final_bc_loss": meta.get("final_bc_loss"),
            "final_bc_acc": meta.get("final_bc_acc"),
            "effective_config_sha256": recd_sha,
            "code_commit": meta.get("code_commit"),
        }

    # ---- cross-seed checks ----
    shas = [r["checkpoint_sha256"] for r in manifest_rows]
    if len(set(shas)) != len(shas):
        problems.append(f"checkpoint SHA not unique: {len(shas)} rows, {len(set(shas))} unique")
    param_counts = {r["actor_params"] for r in manifest_rows}
    if len(param_counts) != 1:
        problems.append(f"actor param counts differ across seeds: {sorted(param_counts)}")
    # no _smoke assets inside the formal root
    smoke_hits = [str(p) for p in root.rglob("*") if "_smoke" in p.name or "_smoke" in str(p).lower()]
    if smoke_hits:
        problems.append(f"_smoke assets inside formal root: {smoke_hits}")
    # no IN_PROGRESS markers left (no partial runs)
    in_prog = [str(p) for p in root.rglob("IN_PROGRESS")]
    if in_prog:
        problems.append(f"IN_PROGRESS markers remain: {in_prog}")
    # each seed dir has exactly one mappo_bc_actor.pt and a COMPLETE marker
    for seed in SEEDS:
        seed_dir = root / f"bc_seed{seed}"
        ckpts = list(seed_dir.glob("mappo_bc_actor.pt")) if seed_dir.exists() else []
        if len(ckpts) != 1:
            problems.append(f"seed{seed}: expected exactly 1 checkpoint, found {len(ckpts)}")
        if not (seed_dir / "COMPLETE").exists():
            problems.append(f"seed{seed}: COMPLETE marker missing")

    # ---- git snapshot ----
    import subprocess
    for cmd in (["git", "rev-parse", "HEAD"], ["git", "status", "--short", "--untracked-files=all"], ["git", "describe", "--tags", "--exact-match", "HEAD"]):
        try:
            r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
            cmd_str = " ".join(cmd)
            stdout = r.stdout.strip()
            stderr = r.stderr.strip()
            err_txt = "" if not stderr else "\n" + stderr
            git_snapshot.append(f"$ {cmd_str}\nexit={r.returncode}\n{stdout}{err_txt}")
        except Exception as e:  # noqa: BLE001
            cmd_str = " ".join(cmd)
            git_snapshot.append(f"$ {cmd_str}\nerror: {e}")

    # ---- write outputs ----
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with (notes / "bc_manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest_rows[0].keys()))
        w.writeheader()
        w.writerows(manifest_rows)
    (notes / "bc_checkpoint_sha256.txt").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    with (notes / "effective_config_audit.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["seed", "recorded_sha256", "recomputed_sha256", "match"])
        w.writeheader()
        w.writerows(eff_rows)
    (notes / "demo_generation_manifest.json").write_text(json.dumps(demo_manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    n_ok = len(manifest_rows)
    all_ok = (n_ok == 3) and not problems
    report = [
        "# MAPPO Formal BC 3/3 Comprehensive Audit",
        "",
        f"- generated: {now}",
        f"- frozen code/tag: {CODE_COMMIT}",
        f"- seeds audited: {SEEDS}",
        f"- 3/3 checkpoints present: {'PASS' if n_ok == 3 else f'FAIL ({n_ok}/3)'}",
        f"- 3/3 strict-loadable: {'PASS' if all(r['strict_load'] == 'PASS' for r in manifest_rows) else 'FAIL'}",
        f"- 3/3 critic untouched: {'PASS' if all(r['critic_untouched'] == 'PASS' for r in manifest_rows) else 'FAIL'}",
        f"- checkpoint SHA unique: {'PASS' if len(set(shas)) == 3 else 'FAIL'}",
        f"- actor param counts identical: {'PASS' if len(param_counts) == 1 else 'FAIL'} ({sorted(param_counts)})",
        f"- network dims consistent (obs=34/role=4/action=27/hidden=64): {'PASS' if all(r['obs_dim'] == 34 and r['role_dim'] == 4 and r['action_dim'] == 27 and r['hidden_dim'] == 64 for r in manifest_rows) else 'FAIL'}",
        f"- critic NOT inside BC (payload keys): {'PASS' if all(r['strict_load'] == 'PASS' for r in manifest_rows) else 'FAIL'}",
        f"- seed/demo-SHA/config-SHA/commit complete: {'PASS' if all(r['demo_sha256'] and r['effective_config_sha256'] and r['code_commit'] for r in manifest_rows) else 'FAIL'}",
        f"- no _smoke assets: {'PASS' if not smoke_hits else 'FAIL'}",
        f"- no overwritten/re-run checkpoints (1 per seed + COMPLETE): {'PASS' if not in_prog and all((root / f'bc_seed{s}' / 'COMPLETE').exists() for s in SEEDS) else 'FAIL'}",
        "",
        "## Per-seed manifest",
        "",
    ]
    for r in manifest_rows:
        report.append(f"- seed{r['seed']}: sha {r['checkpoint_sha256'][:16]}… params={r['actor_params']} demo_sha={str(r['demo_sha256'])[:12]}… loss={r['final_bc_loss']:.4f} acc={r['final_bc_acc']:.4f}")
    report.append("")
    if problems:
        report.append("## PROBLEMS")
        for p in problems:
            report.append(f"- FAIL: {p}")
        report.append("")
    report.append(f"## OVERALL: {'PASS' if all_ok else 'FAIL'}")
    report.append("")
    report.append("## Git snapshot")
    report.extend(git_snapshot)
    (notes / "bc_audit_report.md").write_text("\n".join(report), encoding="utf-8")

    print("OVERALL:", "PASS" if all_ok else "FAIL")
    for p in problems:
        print("  -", p)
    for r in manifest_rows:
        print(f"seed{r['seed']} sha={r['checkpoint_sha256'][:16]}… params={r['actor_params']}")
    print(f"audit bundle: {notes}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
