"""Technical pre-launch gate for the frozen Phase 2I-A2 development experiment."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_phase2ia2_development_validation import ARMS, SEEDS, episode_id


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    errors = []
    for arm, mode in ARMS.items():
        path = ROOT / "configs" / "development" / f"phase2ia2_{arm}.json"
        if not path.exists():
            errors.append(f"missing arm config: {path}")
            continue
        config = json.loads(path.read_text(encoding="utf-8"))
        if config.get("role_gate_mode") != mode or config.get("seed_set") != list(SEEDS):
            errors.append(f"config mismatch: {path}")
        print(f"{arm} config sha256: {digest(path)}")
    if episode_id(101, 0, 0) != 1_220_000 or episode_id(303, 3, 49) != 3_243_049:
        errors.append("development episode-ID formula mismatch")
    output_root = ROOT / "results" / "development" / "role_gate_phase2ia2" / "runs"
    output_root.mkdir(parents=True, exist_ok=True)
    probe = output_root / ".write_probe"
    probe.write_text("ok\n", encoding="utf-8")
    probe.unlink()
    if errors:
        raise SystemExit("Phase 2I-A2 pre-launch: NO-GO\n" + "\n".join(errors))
    print("Phase 2I-A2 technical pre-launch: PASS")


if __name__ == "__main__":
    main()
