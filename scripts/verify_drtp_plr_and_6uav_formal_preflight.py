"""Zero-training integrity gate for the PLR and 6-UAV formal packages."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.drtp_topology_sampler import FAILURE_GROUPS, GROUP_MEMBERS, NOMINAL_GROUP
from algorithms.ri_gmappo.plr_topology_sampler import PLRTopologySampler
from algorithms.redundant_topology_drtp_sampler import SixUAVDRTPTopologySampler
from scripts.run_redundant_topology_uav_p2 import GROUPS, make_env


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("explicit --execute is required")
    out = args.output_root
    if out.exists():
        raise FileExistsError(f"refusing to overwrite {out}")
    plr_path = ROOT / "configs" / "drtp_plr_external_formal_freeze_20260906.json"
    six_path = ROOT / "configs" / "drtp_6uav_cross_scale_formal_freeze_20260906.json"
    plr = json.loads(plr_path.read_text(encoding="utf-8"))
    six = json.loads(six_path.read_text(encoding="utf-8"))
    sampler = PLRTopologySampler(79011, 39063)
    initial = [sampler.select(0, index, 0) for index in range(12)]
    score_row = sampler.record_rollout_scores(
        np.ones((4, 4, 5), dtype=np.float32),
        np.asarray([["F0", "TE", "TL", "DS"]] * 4),
    )
    restored = PLRTopologySampler(79011, 39063)
    state = sampler.state_dict()
    restored.load_state_dict(state)
    env = make_env(69011, "nominal")
    _, _, graph = env.reset()
    six_sampler = SixUAVDRTPTopologySampler("drtp", 69011, 39063)
    six_state = six_sampler.state_dict()
    six_restored = SixUAVDRTPTopologySampler("drtp", 69011, 39063)
    six_restored.load_state_dict(six_state)
    expected_6uav = ("nominal", "R_upstream", "R_downstream", "C_relay_node", "C_balanced", "C_cross", "C_same_relay")
    checks = {
        "plr_failure_levels_exact": plr["plr_mapping"]["level"] == "one of six frozen DRTP failure groups",
        "plr_support_exact": tuple(FAILURE_GROUPS) == ("F0", "TE", "TL", "DS", "DL", "CP"),
        "plr_nominal_group_excluded_from_replay": NOMINAL_GROUP not in FAILURE_GROUPS,
        "plr_member_interface_retained": all(GROUP_MEMBERS[group] for group in FAILURE_GROUPS),
        "plr_runtime_restore_exact": restored.state_dict() == state,
        "plr_rollout_score_has_no_ppo_side_effect": score_row["record_type"] == "rollout_score_update",
        "six_uav_groups_exact": tuple(six["condition_interface"]["groups"]) == expected_6uav == tuple(GROUPS),
        "six_uav_graph_interface_complete": set(("node_features", "roles", "active_adj", "action_masks")).issubset(graph),
        "six_uav_drtp_runtime_restore_exact": six_restored.state_dict() == six_state,
        "six_uav_fresh_seed_ranges_disjoint": set(six["training"]["seeds"]).isdisjoint(six["training"]["reserved_independent_replication_seeds"]),
        "cross_line_seed_ranges_disjoint": set(plr["training"]["seeds"]).isdisjoint(six["training"]["seeds"]),
        "training_started": False,
        "evaluation_started": False,
    }
    technical_checks = {key: value for key, value in checks.items() if key not in {"training_started", "evaluation_started"}}
    payload = {
        "protocol": "DRTP-PLR-AND-6UAV-FORMAL-PREFLIGHT-V1",
        "verdict": "DRTP_PLR_AND_6UAV_PREFLIGHT_PASS" if all(technical_checks.values()) else "DRTP_PLR_AND_6UAV_PREFLIGHT_FAIL",
        "checks": checks,
        "plr_freeze_sha256": _sha(plr_path),
        "six_uav_freeze_sha256": _sha(six_path),
        "training_started": False,
        "automatic_continuation": False,
    }
    out.mkdir(parents=True)
    (out / "DRTP_PLR_AND_6UAV_FORMAL_PREFLIGHT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (out / "DRTP_PLR_AND_6UAV_FORMAL_PREFLIGHT.md").write_text(
        "# DRTP PLR + 6-UAV formal preflight\n\n"
        f"`{payload['verdict']}`\n\n```json\n{json.dumps(payload, indent=2)}\n```\n",
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))
    if payload["verdict"] != "DRTP_PLR_AND_6UAV_PREFLIGHT_PASS":
        raise RuntimeError("formal preflight failed")


if __name__ == "__main__":
    main()
