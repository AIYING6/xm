"""Zero-training preflight for the MAPPO-NoGraph external-reference contract."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from create_drtp_utr_q2_formal_tape import EPISODES, TAPE_START, frozen_manifest  # noqa: E402
from run_drtp_mappo_external_single import HIDDEN_DIM, SEEDS, parameter_count, training_config  # noqa: E402
from run_drtp_utr_q2_formal_single import training_config as utr_config  # noqa: E402


PROTOCOL = "DRTP-MAPPO-NOGRAPH-EXTERNAL-REFERENCE-5SEED-PREFLIGHT-V1"
ALLOWED = {"seed", "out_dir", "device", "drtp_sampler_seed", "hidden_dim", "graph_encoder"}


def normalized(cfg) -> dict:
    data = asdict(cfg)
    for key in ALLOWED:
        data.pop(key, None)
    return data


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path); args = parser.parse_args()
    configs = [training_config(seed, Path("unused") / f"seed{seed}") for seed in SEEDS]
    utr = utr_config("utr_sg", SEEDS[0], Path("unused") / "utr")
    tape = frozen_manifest()
    count = parameter_count(configs[0])
    checks = {
        "five_frozen_paired_seeds": tuple(SEEDS) == (2301, 2302, 2303, 2304, 2305),
        "canonical_seeds_prohibited": not set(SEEDS).intersection({0, 1, 2, 3, 4}),
        "strict_common_10m_budget": all(c.updates == 39063 and c.num_envs == 4 and c.rollout_steps == 64 for c in configs),
        "same_s2_ppo_reward_failure_contract_as_utr": all(normalized(c) == normalized(utr) for c in configs),
        "no_graph_actor_only": all(c.graph_encoder == "no_graph" and c.hidden_dim == HIDDEN_DIM for c in configs),
        "fixed_utr_exposure": all(c.drtp_sampler_mode == "utr" and c.fixed_f0_probability is None for c in configs),
        "runtime_persistence_from_start": all(c.runtime_state_checkpointing and c.runtime_state_resume is None and c.resume is None for c in configs),
        "same_frozen_formal_tape": tape["tape_hash"] == "84e31ed185ced0608a30c9cb9f9659c7423c952e4603aac53cf691c54fc64ac2" and tape["episode_ids"] == list(range(TAPE_START, TAPE_START + EPISODES)),
        "same_twelve_conditions": len(tape["conditions"]) == 12,
        "parameter_count_determined": count > 0,
        "no_training_started_by_preflight": True,
    }
    result = {"protocol": PROTOCOL, "checks": checks, "mappo_nograph_parameter_count": count,
              "tape_hash": tape["tape_hash"], "training_started": False, "pass": all(checks.values())}
    encoded = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    if not result["pass"]: raise SystemExit(1)


if __name__ == "__main__":
    main()
