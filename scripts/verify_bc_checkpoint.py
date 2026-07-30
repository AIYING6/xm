"""Verify that a formal BC initialization checkpoint is usable and method-compatible.

This closes the gap where a BC directory was treated as ``FRESH`` merely because
``actor_critic_latest.pt`` existed on disk. A truncated write, an empty state
dict, a wrong hidden dim, or a checkpoint produced by a different method would
all previously pass.

Checks performed per BC checkpoint:

- ``bc_exists``            file is present
- ``bc_nonempty_file``     file size > 0
- ``bc_loadable``          ``torch.load(..., map_location="cpu")`` succeeds
- ``bc_nonempty_state``    the recovered state dict has at least one tensor
- ``bc_method_compatible`` a model built with the method's own architecture
                           accepts the state dict with an exact match
- ``bc_sha256``            content digest, recorded for provenance
- ``bc_freeze_commit``     freeze commit recorded in the BC manifest, if any

The method-compatibility check builds the real agent for the method (the same
constructor path used by the BC pretrainer) and requires an *exact* match:
every key present, every shape equal, nothing skipped and nothing partially
expanded. ``load_matching_state_dict`` silently tolerates partial/skipped
tensors, so it is used only through its ``exact_match`` return flag.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Architecture registry for the five formal methods. These MUST stay in sync
# with scripts/run_formal_post_sixth_1m_bc.ps1 and the chunk launcher.
METHOD_SPECS: dict[str, dict] = {
    "no_graph": {
        "family": "ri_gmappo",
        "graph_encoder": "no_graph",
        "hidden_dim": 64,
        "role_gate_prior_strength": 0.0,
        "checkpoint_name": "actor_critic_latest.pt",
    },
    "single_graph": {
        "family": "ri_gmappo",
        "graph_encoder": "single",
        "hidden_dim": 64,
        "role_gate_prior_strength": 0.0,
        "checkpoint_name": "actor_critic_latest.pt",
    },
    "param_matched_single": {
        "family": "ri_gmappo",
        "graph_encoder": "single",
        "hidden_dim": 96,
        "role_gate_prior_strength": 0.0,
        "checkpoint_name": "actor_critic_latest.pt",
    },
    "ea_rg_mappo_s_gate_prior": {
        "family": "ri_gmappo",
        "graph_encoder": "multi_relation",
        "hidden_dim": 64,
        "role_gate_prior_strength": 0.4,
        "checkpoint_name": "actor_critic_latest.pt",
    },
    "happo": {
        "family": "happo",
        "graph_encoder": "no_graph",
        "hidden_dim": 64,
        "role_gate_prior_strength": 0.0,
        "checkpoint_name": "happo_bc_latest.pt",
    },
}

ROLE_DIM = 8
INTENT_DIM = 8

# Env knobs that affect observation/graph dimensionality. Must mirror the BC
# and PPO launchers, otherwise the exact-match check would fail spuriously.
ENV_KWARGS = dict(
    env_name="3d_intercept",
    target_policy="straight",
    strict_target_sensing=True,
    agent_target_info_bottleneck=True,
    communication_dropout_prob=0.30,
    message_delay_steps=2,
    failed_blue_agent=1,
)


def bc_checkpoint_name(method: str) -> str:
    return METHOD_SPECS[method]["checkpoint_name"]


def bc_checkpoint_path(root: Path, method: str, seed: int) -> Path:
    return root / method / f"bc_seed{seed}" / bc_checkpoint_name(method)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _state_dict_from(payload) -> dict:
    """Recover a plain ``name -> tensor`` mapping from a saved BC payload."""
    if isinstance(payload, dict) and "model_state" in payload:
        payload = payload["model_state"]
    if not isinstance(payload, dict):
        return {}
    return {k: v for k, v in payload.items() if isinstance(v, torch.Tensor)}


def _build_reference_agent(method: str):
    """Build a freshly initialized agent using the method's own architecture."""
    import numpy as np

    from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOConfig, make_env

    spec = METHOD_SPECS[method]
    cfg = RIGMAPPOConfig(seed=0, **ENV_KWARGS)
    env = make_env(cfg, 0, training=False)
    _, share_obs, graph = env.reset()

    common = dict(
        obs_dim=env.obs_dim,
        node_feat_dim=graph["node_feat"].shape[-1],
        edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share_obs.shape[-1],
        action_dim=env.action_dim,
        num_agents=env.num_agents,
        hidden_dim=spec["hidden_dim"],
        role_dim=ROLE_DIM,
        intent_dim=INTENT_DIM,
    )

    if spec["family"] == "happo":
        from scripts.train_happo_baseline import HAPPOBaselineAgent

        return HAPPOBaselineAgent(
            num_roles=max(5, int(np.max(graph["role"])) + 1),
            **common,
        )

    from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent

    return RIGMAPPOAgent(
        num_roles=max(4, int(np.max(graph["role"])) + 1),
        graph_encoder=spec["graph_encoder"],
        role_gate_prior_strength=spec["role_gate_prior_strength"],
        **common,
    )


def _exact_match(method: str, state: dict) -> tuple[bool, str]:
    """Require every reference parameter to be present with an identical shape."""
    try:
        agent = _build_reference_agent(method)
    except Exception as exc:  # pragma: no cover - env construction failure
        return False, f"reference_build_failed: {type(exc).__name__}: {exc}"

    reference = agent.state_dict()
    missing = [k for k in reference if k not in state]
    unexpected = [k for k in state if k not in reference]
    mismatched = [
        k
        for k in reference
        if k in state and tuple(reference[k].shape) != tuple(state[k].shape)
    ]
    if missing or unexpected or mismatched:
        return False, (
            f"missing={len(missing)} unexpected={len(unexpected)} "
            f"shape_mismatch={len(mismatched)}"
            + (f" first_missing={missing[0]}" if missing else "")
            + (f" first_mismatch={mismatched[0]}" if mismatched else "")
        )

    try:
        agent.load_state_dict(state, strict=True)
    except Exception as exc:
        return False, f"load_state_dict_failed: {type(exc).__name__}: {exc}"
    return True, "exact"


def read_manifest_commit(bc_dir: Path) -> str:
    manifest = bc_dir / "bc_manifest.json"
    if not manifest.exists():
        return ""
    try:
        data = json.loads(manifest.read_text(encoding="utf-8-sig"))
    except Exception:
        return ""
    return str(data.get("freeze_commit", ""))


def verify_bc(
    root: Path,
    method: str,
    seed: int,
    *,
    check_architecture: bool = True,
) -> dict:
    """Run all BC integrity checks for one method/seed."""
    path = bc_checkpoint_path(root, method, seed)
    result = {
        "method": method,
        "seed": seed,
        "path": str(path),
        "bc_exists": False,
        "bc_nonempty_file": False,
        "bc_loadable": False,
        "bc_nonempty_state": False,
        "bc_method_compatible": False,
        "bc_sha256": "",
        "bc_freeze_commit": "",
        "bc_tensor_count": 0,
        "detail": "",
    }
    if not path.exists():
        result["detail"] = "missing"
        return result
    result["bc_exists"] = True

    if path.stat().st_size <= 0:
        result["detail"] = "empty_file"
        return result
    result["bc_nonempty_file"] = True
    result["bc_sha256"] = sha256_of(path)
    result["bc_freeze_commit"] = read_manifest_commit(path.parent)

    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except Exception as exc:
        result["detail"] = f"load_failed: {type(exc).__name__}: {exc}"
        return result
    result["bc_loadable"] = True

    state = _state_dict_from(payload)
    result["bc_tensor_count"] = len(state)
    if not state:
        result["detail"] = "empty_state_dict"
        return result
    result["bc_nonempty_state"] = True

    if not check_architecture:
        result["detail"] = "architecture_check_skipped"
        return result

    ok, detail = _exact_match(method, state)
    result["bc_method_compatible"] = ok
    result["detail"] = detail
    return result


def bc_is_valid(result: dict) -> bool:
    return bool(
        result["bc_exists"]
        and result["bc_nonempty_file"]
        and result["bc_loadable"]
        and result["bc_nonempty_state"]
        and result["bc_method_compatible"]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT / "results" / "paper_config_runs" / "formal_budget_post_sixth_freeze_v1",
    )
    parser.add_argument("--method", default="all", choices=("all", *METHOD_SPECS))
    parser.add_argument("--seed", type=int, default=-1, help="-1 means all of 0 1 2")
    parser.add_argument("--expected-commit", default="", help="required freeze commit SHA")
    parser.add_argument(
        "--skip-architecture",
        action="store_true",
        help="only check file/loadability (fast path, does not build the env)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    args = parser.parse_args()

    methods = list(METHOD_SPECS) if args.method == "all" else [args.method]
    seeds = [0, 1, 2] if args.seed < 0 else [args.seed]

    results = [
        verify_bc(args.root, m, s, check_architecture=not args.skip_architecture)
        for m in methods
        for s in seeds
    ]

    commit_mismatch = []
    if args.expected_commit:
        commit_mismatch = [
            r for r in results if r["bc_freeze_commit"] != args.expected_commit
        ]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("| Method | Seed | Exists | Loadable | NonemptyState | ArchExact | Tensors | SHA256[:12] | Detail |")
        print("|---|---:|---|---|---|---|---:|---|---|")
        for r in results:
            print(
                f"| {r['method']} | {r['seed']} | "
                f"{'yes' if r['bc_exists'] else 'no'} | "
                f"{'yes' if r['bc_loadable'] else 'no'} | "
                f"{'yes' if r['bc_nonempty_state'] else 'no'} | "
                f"{'yes' if r['bc_method_compatible'] else 'no'} | "
                f"{r['bc_tensor_count']} | {r['bc_sha256'][:12]} | {r['detail']} |"
            )

    valid = sum(1 for r in results if bc_is_valid(r))
    total = len(results)
    print(f"\nBC loadable/compatible = {valid}/{total}")
    if args.expected_commit:
        print(
            f"freeze commit match = {total - len(commit_mismatch)}/{total} "
            f"(expected {args.expected_commit})"
        )

    if valid != total or commit_mismatch:
        for r in results:
            if not bc_is_valid(r):
                print(f"- INVALID {r['method']} seed{r['seed']}: {r['detail']}")
        for r in commit_mismatch:
            print(
                f"- COMMIT_MISMATCH {r['method']} seed{r['seed']}: "
                f"manifest={r['bc_freeze_commit'] or '(none)'}"
            )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
