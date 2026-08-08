"""Config-level dry-run audit for the frozen v1.8 formal launch manifest."""
from __future__ import annotations

import re
import shlex
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "FORMAL_V1_8_LAUNCH_MANIFEST.md"
REQUIRED = {
    "--env-name": "3d_intercept", "--num-envs": "8", "--rollout-steps": "128",
    "--updates": "300", "--hidden-dim": "128", "--role-dim": "8", "--intent-dim": "8",
    "--ppo-epochs": "4", "--communication-dropout-prob": "0.3", "--message-delay-steps": "2",
    "--radar-dropout-prob": "0.1", "--failed-blue-agent": "1", "--node-failure-start-step": "40",
    "--node-failure-duration-steps": "80", "--eval-interval": "10", "--eval-episodes": "20",
}


def main() -> int:
    text = MANIFEST.read_text(encoding="utf-8")
    commands = re.findall(r"`(python scripts/train_ri_gmappo\.py[^`]+)`", text)
    errors = []
    expected = {(method, seed) for method in ("multi_relation", "single", "matched_nongraph") for seed in (0, 1, 2)}
    found = set()
    normalized = []
    for command in commands:
        method = re.search(r"--graph-encoder\s+(\S+)", command)
        seed = re.search(r"--seed\s+(\d+)", command)
        if not method or not seed:
            errors.append("command missing graph encoder or seed")
            continue
        found.add((method.group(1), int(seed.group(1))))
        tokens = shlex.split(command)
        parsed = {}
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if token.startswith("--") and i + 1 < len(tokens) and not tokens[i + 1].startswith("--"):
                parsed[token] = tokens[i + 1]; i += 2
            elif token.startswith("--"):
                parsed[token] = "true"; i += 1
            else:
                i += 1
        normalized.append({k: v for k, v in parsed.items() if k not in {"--seed", "--graph-encoder", "--eval-base-seed", "--out-dir"}})
        for flag, value in REQUIRED.items():
            match = re.search(re.escape(flag) + r"\s+(\S+)", command)
            if not match or match.group(1) != value:
                errors.append(f"{method.group(1)} seed {seed.group(1)}: {flag} != {value}")
        if "--strict-target-sensing" not in command or "--agent-target-info-bottleneck" not in command:
            errors.append(f"{method.group(1)} seed {seed.group(1)}: missing strict sensing/bottleneck")
    if found != expected:
        errors.append(f"run matrix mismatch: found={sorted(found)} expected={sorted(expected)}")
    if normalized and any(item != normalized[0] for item in normalized[1:]):
        errors.append("unintended command difference beyond seed/encoder/eval-base-seed/out-dir")
    if errors:
        print("FORMAL_V1_8_LAUNCH_MANIFEST_AUDIT: FAIL")
        print("\n".join(errors))
        return 1
    print("FORMAL_V1_8_LAUNCH_MANIFEST_AUDIT: PASS (9 runs, explicit persistent-failure config)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
