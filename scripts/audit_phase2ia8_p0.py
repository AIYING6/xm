"""Static P0 audit for the Phase2IA8 support instrumentation."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "development" / "phase2ia8_p0_audit"


def main() -> None:
    source = (ROOT / "envs" / "uav_intercept_3d_env.py").read_text(encoding="utf-8")
    checks = [
        ("support_field_present", '"chain_support_t"' in source),
        ("support_uses_attack_window", "np.max(self.attack_window)" in source),
        ("support_uses_tracking", "np.mean(self.detected_by)" in source),
        ("support_uses_existing_comm_predicate", "self._comm_has_chain_to_attacker()" in source),
        ("no_success_or_termination_change", "self.success = (self.neutralized if self.config.v16r_mission_mode else chain_closed)" in source and "self.done = bool(self.success or self.collision or self.constraint_violation or timeout)" in source),
    ]
    result = {"status": "PASS" if all(ok for _, ok in checks) else "FAIL", "checks": [{"gate": n, "status": "PASS" if ok else "FAIL"} for n, ok in checks], "training_started": False}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "P0_AUDIT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
