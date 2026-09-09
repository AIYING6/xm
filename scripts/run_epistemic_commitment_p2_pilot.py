"""Frozen P2 pilot training, evaluation, and aggregation runner."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import torch
from torch import nn


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.epistemic_commitment import (
    CapacityMatchedRecurrentActor,
    CommitmentActorConfig,
    InformationSetCommitmentActor,
    parameter_count,
)
from algorithms.epistemic_commitment_objective import commitment_actor_loss
from envs.epistemic_commitment_trainable_env import (
    ACTION_FALLBACK,
    EpistemicCommitmentEpisodeSpec,
    EpistemicCommitmentTrainableEnv,
    RELIABILITY_CONTEXTS,
    make_balanced_evaluation_tape,
)
from scripts.run_epistemic_commitment_p1g_smoke import (
    CommitmentCritic,
    METHOD_CANDIDATE,
    METHOD_RECURRENT,
    METHODS,
)


FREEZE_PATH = ROOT / "configs" / "epistemic_commitment_p2_pilot_freeze_20260909.json"


def load_freeze() -> dict:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    if freeze.get("protocol") != "EPISTEMIC-COMMITMENT-P2-PILOT-FREEZE-V1":
        raise ValueError("unexpected P2 freeze protocol")
    return freeze


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        raise ValueError("refusing to write empty CSV")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class CommitmentPilotRunner:
    checkpoint_protocol = "EPISTEMIC-COMMITMENT-P2-PILOT-CHECKPOINT-V1"

    def __init__(self, method: str, seed: int, freeze: dict) -> None:
        if method not in METHODS:
            raise ValueError(f"unknown method: {method}")
        if seed not in freeze["training_seeds"]:
            raise ValueError(f"seed {seed} is outside frozen registry")
        self.method = method
        self.seed = int(seed)
        self.freeze = copy.deepcopy(freeze)
        torch.manual_seed(self.seed)
        config = CommitmentActorConfig(
            input_dim=39,
            hidden_dim=int(freeze["actor_hidden_dim"]),
            robust_softmin_temperature=float(freeze["robust_softmin_temperature"]),
        )
        self.actor: nn.Module
        if method == METHOD_CANDIDATE:
            self.actor = InformationSetCommitmentActor(config)
        else:
            self.actor = CapacityMatchedRecurrentActor(config)
        self.critic = CommitmentCritic(117, int(freeze["critic_hidden_dim"]))
        self.actor_optimizer = torch.optim.Adam(
            self.actor.parameters(), lr=float(freeze["actor_learning_rate"])
        )
        self.critic_optimizer = torch.optim.Adam(
            self.critic.parameters(), lr=float(freeze["critic_learning_rate"])
        )
        self.action_generator = torch.Generator(device="cpu")
        self.action_generator.manual_seed(self.seed + 73)
        self.spec_rng = np.random.default_rng(self.seed + 101)
        self.update_index = 0
        self.episodes_seen = 0
        self.physics_steps = 0

    def _training_specs(self, count: int) -> list[EpistemicCommitmentEpisodeSpec]:
        contexts = tuple(RELIABILITY_CONTEXTS)
        specs: list[EpistemicCommitmentEpisodeSpec] = []
        for _ in range(count):
            context = contexts[int(self.spec_rng.integers(0, len(contexts)))]
            delivered = bool(self.spec_rng.random() < RELIABILITY_CONTEXTS[context])
            specs.append(
                EpistemicCommitmentEpisodeSpec(
                    1_000_000 + self.seed * 100_000 + self.episodes_seen + len(specs),
                    context,
                    delivered,
                )
            )
        return specs

    def _prepare_batch(self, specs: list[EpistemicCommitmentEpisodeSpec]) -> dict:
        histories: list[np.ndarray] = []
        shared: list[np.ndarray] = []
        priors: list[float] = []
        envs: list[EpistemicCommitmentTrainableEnv] = []
        for spec in specs:
            env = EpistemicCommitmentTrainableEnv(self.seed, spec)
            obs0, _, _ = env.reset()
            obs1, share1, _, _, _, _ = env.step([ACTION_FALLBACK] * 3)
            for agent_id in (env.leader_id, env.follower_id):
                histories.append(np.stack((obs0[agent_id], obs1[agent_id])))
                priors.append(RELIABILITY_CONTEXTS[spec.context])
            shared.append(share1[0])
            envs.append(env)
        history = torch.as_tensor(np.stack(histories), dtype=torch.float32)
        prior = torch.as_tensor(priors, dtype=torch.float32)
        share_obs = torch.as_tensor(np.stack(shared), dtype=torch.float32)
        with torch.no_grad():
            rollout_output = self.actor(history)
            probabilities = torch.softmax(rollout_output["mode_logits"], dim=-1)
            actions = torch.multinomial(
                probabilities, 1, generator=self.action_generator
            ).squeeze(-1)
            old_log_prob = torch.log(
                torch.gather(probabilities, 1, actions[:, None]).squeeze(1)
            )
        rewards: list[float] = []
        infos: list[dict] = []
        for episode_index, env in enumerate(envs):
            leader = int(actions[2 * episode_index].item())
            follower = int(actions[2 * episode_index + 1].item())
            _, _, _, reward, _, info = env.step([leader, ACTION_FALLBACK, follower])
            rewards.append(float(reward[0, 0]))
            infos.append(info)
        return {
            "history": history,
            "prior": prior,
            "share_obs": share_obs,
            "actions": actions,
            "old_log_prob": old_log_prob,
            "rewards": torch.as_tensor(rewards, dtype=torch.float32),
            "infos": infos,
        }

    def update(self, episode_count: int | None = None) -> dict:
        count = int(episode_count or self.freeze["episodes_per_update"])
        batch = self._prepare_batch(self._training_specs(count))
        with torch.no_grad():
            advantages_episode = batch["rewards"] - self.critic(batch["share_obs"])
            advantages = torch.repeat_interleave(advantages_episode, 2)
            advantages = (advantages - advantages.mean()) / (
                advantages.std(unbiased=False) + 1e-6
            )
        last_actor = last_critic = last_calibration = 0.0
        for _ in range(int(self.freeze["ppo_epochs_per_update"])):
            output = self.actor(batch["history"])
            actor_loss, telemetry = commitment_actor_loss(
                output,
                batch["actions"],
                batch["old_log_prob"],
                advantages,
                batch["prior"],
                calibration_weight=float(self.freeze["calibration_weight"]),
                calibration_radius=float(self.freeze["ambiguity_radius"]),
                clip_epsilon=float(self.freeze["ppo_clip_epsilon"]),
            )
            values = self.critic(batch["share_obs"])
            critic_loss = torch.mean((values - batch["rewards"]) ** 2)
            self.actor_optimizer.zero_grad(set_to_none=True)
            actor_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.actor.parameters(), 0.5)
            self.actor_optimizer.step()
            self.critic_optimizer.zero_grad(set_to_none=True)
            critic_loss.backward()
            torch.nn.utils.clip_grad_norm_(self.critic.parameters(), 0.5)
            self.critic_optimizer.step()
            last_actor = float(actor_loss.detach())
            last_critic = float(critic_loss.detach())
            last_calibration = float(telemetry["calibration_loss"].detach())

        infos: list[dict] = batch["infos"]
        self.episodes_seen += count
        self.physics_steps += count * int(self.freeze["physical_steps_per_episode"])
        metrics = {
            "update": self.update_index,
            "episodes_seen": self.episodes_seen,
            "physics_steps": self.physics_steps,
            "mean_task_value": float(batch["rewards"].mean()),
            "bilateral_commitment_rate": float(np.mean([x["bilateral_commitment_success"] for x in infos])),
            "single_sided_commitment_rate": float(np.mean([x["single_sided_commitment"] for x in infos])),
            "defer_rate": float(np.mean([x["defer"] for x in infos])),
            "fallback_rate": float(np.mean([x["fallback"] for x in infos])),
            "stale_token_commit_rate": float(np.mean([x["stale_token_commit"] for x in infos])),
            "collision_rate": float(np.mean([x["collision"] for x in infos])),
            "constraint_violation_rate": float(np.mean([x["constraint_violation"] for x in infos])),
            "actor_loss": last_actor,
            "critic_loss": last_critic,
            "calibration_loss": last_calibration,
        }
        self.update_index += 1
        return metrics

    def state_dict(self) -> dict:
        return {
            "protocol": self.checkpoint_protocol,
            "method": self.method,
            "seed": self.seed,
            "freeze_sha256": file_sha256(FREEZE_PATH),
            "update_index": self.update_index,
            "episodes_seen": self.episodes_seen,
            "physics_steps": self.physics_steps,
            "actor": copy.deepcopy(self.actor.state_dict()),
            "critic": copy.deepcopy(self.critic.state_dict()),
            "actor_optimizer": copy.deepcopy(self.actor_optimizer.state_dict()),
            "critic_optimizer": copy.deepcopy(self.critic_optimizer.state_dict()),
            "action_generator_state": self.action_generator.get_state().clone(),
            "spec_rng_state": copy.deepcopy(self.spec_rng.bit_generator.state),
        }

    def load_state_dict(self, state: dict) -> None:
        if state.get("protocol") != self.checkpoint_protocol:
            raise ValueError("unsupported P2 checkpoint protocol")
        if state.get("method") != self.method or int(state.get("seed")) != self.seed:
            raise ValueError("checkpoint method/seed mismatch")
        if state.get("freeze_sha256") != file_sha256(FREEZE_PATH):
            raise ValueError("checkpoint freeze hash mismatch")
        self.update_index = int(state["update_index"])
        self.episodes_seen = int(state["episodes_seen"])
        self.physics_steps = int(state["physics_steps"])
        self.actor.load_state_dict(state["actor"])
        self.critic.load_state_dict(state["critic"])
        self.actor_optimizer.load_state_dict(state["actor_optimizer"])
        self.critic_optimizer.load_state_dict(state["critic_optimizer"])
        self.action_generator.set_state(state["action_generator_state"])
        self.spec_rng.bit_generator.state = copy.deepcopy(state["spec_rng_state"])


def _training_manifest(runner: CommitmentPilotRunner, smoke: bool, status: str) -> dict:
    return {
        "protocol": runner.freeze["protocol"],
        "status": status,
        "method": runner.method,
        "seed": runner.seed,
        "episodes": runner.episodes_seen,
        "physics_steps": runner.physics_steps,
        "fixed_endpoint": status == "completed" and not smoke,
        "actor_parameters": parameter_count(runner.actor),
        "freeze_sha256": file_sha256(FREEZE_PATH),
        "scientific_evidence": status == "completed" and not smoke,
    }


def run_train(
    method: str,
    seed: int,
    output_root: Path,
    execute: bool,
    smoke: bool,
    resume: bool = False,
) -> dict:
    freeze = load_freeze()
    if method not in freeze["methods"]:
        raise ValueError(f"method {method} is outside frozen registry")
    if seed not in freeze["training_seeds"]:
        raise ValueError(f"seed {seed} is outside frozen registry")
    run_dir = output_root / "runs" / method / f"seed{seed}"
    if run_dir.exists() and not resume:
        raise FileExistsError(f"refusing to overwrite run: {run_dir}")
    if not execute:
        return {"status": "dry_run", "method": method, "seed": seed, "run_dir": str(run_dir)}
    if smoke and resume:
        raise ValueError("smoke runs cannot resume")
    run_dir.mkdir(parents=True, exist_ok=resume)
    runner = CommitmentPilotRunner(method, seed, freeze)
    log_path = run_dir / "train_log.csv"
    log_rows: list[dict] = []
    if resume:
        checkpoint = run_dir / "checkpoint_latest.pt"
        if not checkpoint.is_file():
            raise FileNotFoundError(f"resume checkpoint missing: {checkpoint}")
        manifest_path = run_dir / "run_manifest.json"
        if not manifest_path.is_file():
            raise FileNotFoundError(f"resume manifest missing: {manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest.get("status") != "training_in_progress":
            raise ValueError("only an interrupted in-progress run may resume")
        runner.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=False))
        if log_path.is_file():
            with log_path.open("r", encoding="utf-8", newline="") as handle:
                log_rows = list(csv.DictReader(handle))
    _write_json(
        run_dir / "run_manifest.json",
        _training_manifest(runner, smoke, "smoke_in_progress" if smoke else "training_in_progress"),
    )
    target_episodes = 3 if smoke else int(freeze["episodes_per_run"])
    while runner.episodes_seen < target_episodes:
        remaining = target_episodes - runner.episodes_seen
        metrics = runner.update(min(int(freeze["episodes_per_update"]), remaining))
        log_rows.append(metrics)
        if not smoke and runner.update_index % int(freeze["checkpoint_every_updates"]) == 0:
            torch.save(runner.state_dict(), run_dir / "checkpoint_latest.pt")
            _write_csv(log_path, log_rows)
            _write_json(
                run_dir / "run_manifest.json",
                _training_manifest(runner, smoke=False, status="training_in_progress"),
            )
    _write_csv(log_path, log_rows)
    torch.save(runner.state_dict(), run_dir / "checkpoint_final.pt")
    manifest = _training_manifest(
        runner, smoke, "smoke_complete" if smoke else "completed"
    )
    _write_json(run_dir / "run_manifest.json", manifest)
    return manifest


def _load_actor(method: str, seed: int, checkpoint: Path, freeze: dict) -> nn.Module:
    runner = CommitmentPilotRunner(method, seed, freeze)
    state = torch.load(checkpoint, map_location="cpu", weights_only=False)
    runner.load_state_dict(state)
    runner.actor.eval()
    return runner.actor


def run_evaluate(method: str, seed: int, output_root: Path, execute: bool) -> dict:
    freeze = load_freeze()
    run_dir = output_root / "runs" / method / f"seed{seed}"
    checkpoint = run_dir / "checkpoint_final.pt"
    eval_path = output_root / "evaluations" / method / f"seed{seed}" / "episode_metrics.csv"
    if eval_path.exists():
        raise FileExistsError(f"refusing to overwrite evaluation: {eval_path}")
    if not execute:
        return {"status": "dry_run", "checkpoint": str(checkpoint), "output": str(eval_path)}
    if not checkpoint.is_file():
        raise FileNotFoundError(checkpoint)
    manifest_path = run_dir / "run_manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = {
        "protocol": freeze["protocol"],
        "status": "completed",
        "method": method,
        "seed": seed,
        "episodes": int(freeze["episodes_per_run"]),
        "physics_steps": int(freeze["physical_steps_per_run"]),
        "fixed_endpoint": True,
        "scientific_evidence": True,
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise ValueError(f"run manifest mismatch for {key}: {manifest.get(key)!r}")
    actor = _load_actor(method, seed, checkpoint, freeze)
    rows: list[dict] = []
    for spec in make_balanced_evaluation_tape(int(freeze["evaluation_tape_start_episode_id"])):
        env = EpistemicCommitmentTrainableEnv(seed, spec)
        obs0, _, _ = env.reset()
        obs1, _, _, _, _, _ = env.step([ACTION_FALLBACK] * 3)
        histories = torch.as_tensor(
            np.stack(
                [
                    np.stack((obs0[env.leader_id], obs1[env.leader_id])),
                    np.stack((obs0[env.follower_id], obs1[env.follower_id])),
                ]
            ),
            dtype=torch.float32,
        )
        with torch.no_grad():
            output = actor(histories)
            actions = torch.argmax(output["mode_logits"], dim=-1)
        _, _, _, reward, _, info = env.step(
            [int(actions[0]), ACTION_FALLBACK, int(actions[1])]
        )
        rows.append(
            {
                "method": method,
                "train_seed": seed,
                "episode_id": spec.episode_id,
                "context": spec.context,
                "delivered": int(spec.delivered),
                "task_value": float(reward[0, 0]),
                "leader_commit": float(info["leader_action"] == "commit"),
                "bilateral_commitment": info["bilateral_commitment_success"],
                "single_sided_commitment": info["single_sided_commitment"],
                "defer": info["defer"],
                "fallback": info["fallback"],
                "stale_token_commit": info["stale_token_commit"],
                "collision": info["collision"],
                "constraint_violation": info["constraint_violation"],
            }
        )
    _write_csv(eval_path, rows)
    return {"status": "completed", "rows": len(rows), "output": str(eval_path)}


def _mean(rows: list[dict], key: str) -> float:
    return float(np.mean([float(row[key]) for row in rows]))


def run_aggregate(output_root: Path, execute: bool) -> dict:
    freeze = load_freeze()
    diagnostics = output_root / "diagnostics" / "p2_pilot_final"
    if diagnostics.exists():
        raise FileExistsError(f"refusing to overwrite diagnostics: {diagnostics}")
    if not execute:
        return {"status": "dry_run", "output": str(diagnostics)}
    all_rows: dict[tuple[str, int], list[dict]] = {}
    for method in freeze["methods"]:
        for seed in freeze["training_seeds"]:
            path = output_root / "evaluations" / method / f"seed{seed}" / "episode_metrics.csv"
            if not path.is_file():
                raise FileNotFoundError(path)
            with path.open("r", encoding="utf-8", newline="") as handle:
                all_rows[(method, seed)] = list(csv.DictReader(handle))
            rows = all_rows[(method, seed)]
            if len(rows) != int(freeze["evaluation_episodes"]):
                raise ValueError(f"evaluation row count mismatch: {path}")
            context_counts = {
                context: sum(row["context"] == context for row in rows)
                for context in RELIABILITY_CONTEXTS
            }
            if context_counts != {context: 100 for context in RELIABILITY_CONTEXTS}:
                raise ValueError(f"evaluation context balance mismatch: {path}")
    summaries: list[dict] = []
    for (method, seed), rows in all_rows.items():
        context_commit = {}
        for context in RELIABILITY_CONTEXTS:
            selected = [row for row in rows if row["context"] == context]
            context_commit[context] = _mean(selected, "leader_commit")
        summaries.append(
            {
                "method": method,
                "train_seed": seed,
                "mean_task_value": _mean(rows, "task_value"),
                "bilateral_commitment_rate": _mean(rows, "bilateral_commitment"),
                "single_sided_commitment_rate": _mean(rows, "single_sided_commitment"),
                "defer_rate": _mean(rows, "defer"),
                "fallback_rate": _mean(rows, "fallback"),
                "stale_token_commit_rate": _mean(rows, "stale_token_commit"),
                "collision_rate": _mean(rows, "collision"),
                "constraint_violation_rate": _mean(rows, "constraint_violation"),
                "high_minus_low_commit_rate": context_commit["high"] - context_commit["low"],
            }
        )
    by_key = {(row["method"], int(row["train_seed"])): row for row in summaries}
    gate = freeze["continue_gate"]
    paired: list[dict] = []
    seed_passes = 0
    for seed in freeze["training_seeds"]:
        candidate = by_key[(METHOD_CANDIDATE, seed)]
        baseline = by_key[(METHOD_RECURRENT, seed)]
        task_delta = float(candidate["mean_task_value"]) - float(baseline["mean_task_value"])
        unilateral_reduction = float(baseline["single_sided_commitment_rate"]) - float(
            candidate["single_sided_commitment_rate"]
        )
        fallback_increase = float(candidate["fallback_rate"]) - float(baseline["fallback_rate"])
        passed = (
            unilateral_reduction >= float(gate["minimum_single_sided_commitment_reduction"])
            and task_delta >= float(gate["minimum_task_value_delta"])
            and float(candidate["high_minus_low_commit_rate"])
            >= float(gate["minimum_high_minus_low_commit_rate"])
            and fallback_increase <= float(gate["maximum_fallback_rate_increase"])
            and float(candidate["collision_rate"]) <= float(baseline["collision_rate"])
            and float(candidate["constraint_violation_rate"])
            <= float(baseline["constraint_violation_rate"])
        )
        seed_passes += int(passed)
        paired.append(
            {
                "train_seed": seed,
                "delta_task_value": task_delta,
                "single_sided_commitment_reduction": unilateral_reduction,
                "fallback_rate_increase": fallback_increase,
                "candidate_high_minus_low_commit_rate": candidate["high_minus_low_commit_rate"],
                "seed_gate_pass": passed,
            }
        )
    baseline_mean = float(
        np.mean(
            [
                float(by_key[(METHOD_RECURRENT, seed)]["mean_task_value"])
                for seed in freeze["training_seeds"]
            ]
        )
    )
    baseline_learnable = baseline_mean > float(gate["baseline_mean_task_value_floor"])
    continue_pass = baseline_learnable and seed_passes >= int(gate["minimum_seeds_passing"])
    verdict = "P2_PILOT_CONTINUE" if continue_pass else "P2_PILOT_STOP"
    diagnostics.mkdir(parents=True)
    _write_csv(diagnostics / "P2_PER_SEED_SUMMARY.csv", summaries)
    _write_csv(diagnostics / "P2_PAIRED_GATE.csv", paired)
    report = {
        "protocol": "EPISTEMIC-COMMITMENT-P2-PILOT-REPORT-V1",
        "verdict": verdict,
        "baseline_learnable": baseline_learnable,
        "baseline_mean_task_value": baseline_mean,
        "seed_gate_passes": seed_passes,
        "required_seed_gate_passes": int(gate["minimum_seeds_passing"]),
        "automatic_continuation": False,
        "automatic_revision": False,
    }
    _write_json(diagnostics / "P2_PILOT_REPORT.json", report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    train = subparsers.add_parser("train")
    train.add_argument("--method", choices=METHODS, required=True)
    train.add_argument("--seed", type=int, required=True)
    train.add_argument("--output-root", type=Path, required=True)
    train.add_argument("--execute", action="store_true")
    train.add_argument("--smoke", action="store_true")
    train.add_argument("--resume", action="store_true")
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--method", choices=METHODS, required=True)
    evaluate.add_argument("--seed", type=int, required=True)
    evaluate.add_argument("--output-root", type=Path, required=True)
    evaluate.add_argument("--execute", action="store_true")
    aggregate = subparsers.add_parser("aggregate")
    aggregate.add_argument("--output-root", type=Path, required=True)
    aggregate.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.command == "train":
        result = run_train(
            args.method,
            args.seed,
            args.output_root,
            args.execute,
            args.smoke,
            args.resume,
        )
    elif args.command == "evaluate":
        result = run_evaluate(args.method, args.seed, args.output_root, args.execute)
    else:
        result = run_aggregate(args.output_root, args.execute)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
