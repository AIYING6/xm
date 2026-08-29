"""Zero-training integrity check for the frozen S1 Stage-1 package."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
import run_drtp_stabilization_s1_single as s1  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    freeze = json.loads((ROOT / "configs/drtp_stabilization_s0_freeze.json").read_text(encoding="utf-8"))
    tape = json.loads(s1.TAPE.read_text(encoding="utf-8"))
    assert s1.UPDATES * s1.NUM_ENVS * s1.ROLLOUT_STEPS == 499_968
    assert s1.MILESTONES == {976: "250k", 1953: "500k"}
    assert s1.ARMS == {"utr_sg": "utr", "drtp_sg": "drtp", "drtp_tr_sg": "drtp_tr"}
    assert s1.SEEDS == (2901, 2902, 2903)
    assert float(freeze["delta_q_l1"]) == 0.02513300038143937
    assert float(freeze["epsilon_J"]) == 7.874919837916801
    assert tape["tape_hash"] == "2ff360d6e240f6f9e3b7a5b74dc56db54da601e391bc259a5a51719d83fa7461"
    assert len(tape["episode_ids"]) == 100 and tape["episode_ids"] == list(range(530000, 530100))
    assert [item["name"] for item in tape["conditions"]] == ["nominal", "F0_44_80", "T28_28_80", "D120_44_120", "C28_120"]
    configs = {}
    for arm in s1.ARMS:
        for seed in s1.SEEDS:
            cfg = s1.training_config(arm, seed, ROOT / "_s1_preflight_no_output")
            assert cfg.updates == s1.UPDATES and cfg.milestone_updates == s1.MILESTONES
            assert cfg.drtp_sampler_mode == s1.ARMS[arm] and cfg.drtp_sampler_seed == seed
            assert cfg.evaluation_enabled is False and cfg.runtime_state_checkpointing is True
            configs[f"{arm}/seed{seed}"] = {"mode": cfg.drtp_sampler_mode, "updates": cfg.updates}
    print(json.dumps({"status": "S1_PREFLIGHT_PASS", "freeze_sha256": sha256(s1.FREEZE),
                      "tape_sha256": sha256(s1.TAPE), "trajectories": configs,
                      "local_training_started": False}, indent=2))


if __name__ == "__main__":
    main()
