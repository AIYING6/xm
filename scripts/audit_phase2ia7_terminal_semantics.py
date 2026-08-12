"""Static semantic audit: chain closure, success, and episode termination."""
from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / "envs" / "uav_intercept_3d_env.py"
OUT = ROOT / "results" / "development" / "phase2ia7_terminal_semantics_audit"


def main() -> None:
    source = ENV.read_text(encoding="utf-8")
    # The audit is deliberately source-level: it proves the relationship before
    # interpreting any new result. Both legacy stepping interfaces share it.
    required = {
        "chain_closed derived from attack_hold": "chain_closed = self.attack_hold >= self.config.attack_hold_steps",
        "non-v16 success equals chain_closed": "self.success = (self.neutralized if self.config.v16r_mission_mode else chain_closed)",
        "success terminates episode": "self.done = bool(self.success or self.collision or self.constraint_violation or timeout)",
    }
    checks = [{"claim": claim, "pass": needle in source} for claim, needle in required.items()]
    result = {
        "status": "PASS" if all(item["pass"] for item in checks) else "FAIL",
        "semantic_consequence": "Under default non-v16 mode, the first chain_closed timestep is terminal. A requirement for four consecutive chain_closed observations is unreachable.",
        "checks": checks,
        "training_started": False,
        "canonical_data_used": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "terminal_semantics_audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
