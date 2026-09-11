"""Static and synthetic preflight for the C1 BC3 identifiability pilot.

This check deliberately does not import the optional LBF benchmark, train a
policy, or write into a result directory.  It verifies the frozen contract's
information boundary and the four model paths before a short pilot is allowed.
"""
from __future__ import annotations

import argparse
import inspect
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.c1_bc3_mappo import C1PilotMAPPO, update_capability_posterior
from envs.c1_lbf_masked_adapter import C1LBFConfig, C1MaskedLBFAdapter


PROTOCOL = "C1-BC3-IDENTIFIABILITY-PILOT-V1"
ARMS = ("ff_mappo", "recurrent_mappo", "bc3_mappo", "shuffled_bc3_mappo")


def fail(message: str) -> None:
    raise RuntimeError(message)


def source_boundary_checks() -> dict[str, bool]:
    config = C1LBFConfig(seed=1)
    if config.emit_public_joint_load_receipt:
        fail("the public receipt must default to off for historical C1 protocols")
    actor_source = inspect.getsource(C1MaskedLBFAdapter.actor_observation)
    critic_source = inspect.getsource(C1MaskedLBFAdapter.critic_observation)
    return {
        "receipt_default_off": True,
        "actor_does_not_call_critic_observation": "critic_observation" not in actor_source,
        "receipt_is_optional_actor_feature": "emit_public_joint_load_receipt" in actor_source,
        "critic_truth_is_separate_from_actor_method": "levels" in critic_source,
    }


def synthetic_model_checks() -> dict[str, bool]:
    torch.manual_seed(11)
    obs = torch.zeros((3, 2, 12), dtype=torch.float32)
    critic = torch.zeros((3, 2, 22), dtype=torch.float32)
    masks = torch.ones((3, 2, 6), dtype=torch.float32)
    posterior = torch.full((3, 2), 0.5, dtype=torch.float32)
    checks: dict[str, bool] = {}
    for arm in ARMS:
        model = C1PilotMAPPO(obs_dim=12, critic_dim=22, action_dim=6, arm=arm)
        memory = model.initial_memory(3, 2, device="cpu") if model.uses_memory else None
        distribution, next_memory = model.action_distribution(
            obs, masks, memory=memory, posterior=posterior if model.uses_posterior else None
        )
        checks[f"{arm}_actor_shape"] = tuple(distribution.logits.shape) == (3, 2, 6)
        checks[f"{arm}_critic_shape"] = tuple(model.value(critic).shape) == (3, 2)
        checks[f"{arm}_memory_path"] = (next_memory is not None) == model.uses_memory
    no_receipt = update_capability_posterior(
        posterior, joint_load_receipt=torch.zeros_like(posterior), public_team_reward=torch.zeros_like(posterior)
    )
    failed_receipt = update_capability_posterior(
        posterior, joint_load_receipt=torch.ones_like(posterior), public_team_reward=torch.zeros_like(posterior)
    )
    successful_receipt = update_capability_posterior(
        posterior, joint_load_receipt=torch.ones_like(posterior), public_team_reward=torch.ones_like(posterior)
    )
    checks["posterior_holds_without_public_receipt"] = bool(torch.allclose(no_receipt, posterior))
    checks["failed_public_receipt_reduces_capability_feature"] = bool(torch.all(failed_receipt < posterior))
    checks["successful_public_receipt_increases_capability_feature"] = bool(torch.all(successful_receipt > posterior))
    return checks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze", type=Path, default=ROOT / "configs" / "c1_bc3_identifiability_pilot_freeze_20260911.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("refusing to write a preflight record without --execute")
    if args.output.exists():
        raise FileExistsError(f"refusing to overwrite {args.output}")
    freeze = json.loads(args.freeze.read_text(encoding="utf-8"))
    if freeze.get("protocol") != PROTOCOL or tuple(freeze.get("arms", {})) != ARMS:
        fail("frozen C1 BC3 contract does not match the runner")
    checks = {**source_boundary_checks(), **synthetic_model_checks()}
    if not all(checks.values()):
        fail(f"C1 BC3 preflight failed: {[key for key, value in checks.items() if not value]}")
    args.output.mkdir(parents=True)
    payload = {
        "protocol": "C1-BC3-IDENTIFIABILITY-PREFLIGHT-V1",
        "verdict": "C1_BC3_PREFLIGHT_PASS",
        "checks": checks,
        "scope": "static and synthetic only; no optional LBF environment, training, or endpoint evaluation was run",
        "training_started": False,
        "evaluation_started": False,
    }
    (args.output / "C1_BC3_PREFLIGHT.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
