"""Preflight for the prospective T1 telemetry-native reference launch."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.simple_ri_gmappo import RIGMAPPOAgent, train_ri_gmappo  # noqa: E402
from scripts.create_t1_telemetry_native_tape import TAPE_START  # noqa: E402
from scripts.run_t1_telemetry_native_single import SEEDS, training_config  # noqa: E402
from scripts.telemetry_native_t0 import NOMINAL, make_env  # noqa: E402
from scripts.telemetry_native_t1 import MATCHED_SG_PARAMETER_COUNT  # noqa: E402


PROTOCOL = "T1-TELEMETRY-NATIVE-PREFLIGHT-V1"
T1_ANCHOR_PARENT = "89f1d6a^"


def build_parameter_probe() -> int:
    env = make_env(0, NOMINAL)
    _, share, graph = env.reset()
    agent = RIGMAPPOAgent(
        obs_dim=env.obs_dim, node_feat_dim=graph["node_feat"].shape[-1], edge_feat_dim=graph["edge_feat"].shape[-1],
        share_obs_dim=share.shape[-1], action_dim=env.action_dim, num_agents=env.num_agents,
        num_roles=max(4, int(np.max(graph["role"])) + 1), hidden_dim=115, role_dim=8, intent_dim=8,
        graph_encoder="single", role_gate_mode="none", use_intent_context=False,
    )
    return sum(parameter.numel() for parameter in agent.parameters() if parameter.requires_grad)


def historical_seed_absence() -> bool:
    """Check the tracked project state before the first T1 contract commit."""
    # Git grep uses ERE, not Python regular expressions.  Match only the
    # syntactic seed/tape forms so a measurement such as ``0.920000`` cannot
    # be mistaken for the reserved tape ID.
    pattern = r"seed[=:_ -]*220[1-5]|\"seed\"[[:space:]]*:[[:space:]]*220[1-5]|SEEDS[^\n]*220[1-5]|920000[-–]920099"
    command = ["git", "grep", "-n", "-E", pattern, T1_ANCHOR_PARENT, "--", "docs", "scripts", "algorithms", "envs", "tests", "configs"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode == 1:
        return True
    if result.returncode != 0:
        raise RuntimeError(f"historical seed provenance query failed: {result.stderr.strip()}")
    return not bool(result.stdout.strip())


def exact_runtime_continuation() -> bool:
    """One-update split versus two-update reference, using T1's unchanged config."""
    with tempfile.TemporaryDirectory(prefix="t1_runtime_preflight_") as folder:
        root = Path(folder)
        continuous, split = root / "continuous", root / "split"
        left = training_config(2201, continuous); left.updates = 2; left.device = "cpu"; left.save_interval = 1; left.runtime_state_save_interval = 1
        train_ri_gmappo(left)
        first = training_config(2201, split); first.updates = 1; first.device = "cpu"; first.save_interval = 1; first.runtime_state_save_interval = 1
        train_ri_gmappo(first)
        resumed = training_config(2201, split); resumed.updates = 1; resumed.device = "cpu"; resumed.save_interval = 1; resumed.runtime_state_save_interval = 1
        resumed.append_log, resumed.update_offset = True, 1
        resumed.runtime_state_resume = str(split / "actor_critic_runtime_state_latest.pt")
        train_ri_gmappo(resumed)
        a = torch.load(continuous / "actor_critic_latest.pt", map_location="cpu", weights_only=True)
        b = torch.load(split / "actor_critic_latest.pt", map_location="cpu", weights_only=True)
        return set(a) == set(b) and all(torch.equal(a[key], b[key]) for key in a)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.output_root.exists() and any(args.output_root.iterdir()):
        raise FileExistsError(f"refusing to launch T1 into nonempty output root: {args.output_root}")
    tests = subprocess.run([sys.executable, "-m", "pytest", "-q", "tests/test_t0_telemetry_native.py", "tests/test_t1_telemetry_native_checkpoint_adapter.py"], cwd=ROOT)
    checks = {
        "t0_t1_tests": tests.returncode == 0,
        "tracked_historical_seed_and_tape_absence": historical_seed_absence(),
        "reserved_seeds": tuple(SEEDS) == (2201, 2202, 2203, 2204, 2205),
        "reserved_tape_namespace": TAPE_START == 920000,
        "matched_sg_parameter_count": build_parameter_probe() == MATCHED_SG_PARAMETER_COUNT,
        "strict_runtime_continuation": exact_runtime_continuation(),
        "long_training_started": False,
        "canonical_seeds_used": False,
        "held_out_seeds_used": False,
    }
    args.output_root.mkdir(parents=True, exist_ok=False)
    output = args.output_root / "preflight_manifest.json"
    result = {"protocol": PROTOCOL, "status": "PASS" if all(value is True for key, value in checks.items() if key not in {"long_training_started", "canonical_seeds_used", "held_out_seeds_used"}) else "FAIL", "checks": checks}
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
