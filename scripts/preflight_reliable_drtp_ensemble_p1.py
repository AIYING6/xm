"""Zero-training technical preflight for the proposed E-DRTP P1 pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from algorithms.ri_gmappo.reliability_ensemble import (
    pooled_categorical_action,
    uniform_probability_pool,
)


OUTPUT = ROOT / "docs" / "reliable_drtp_ensemble_p0" / "p1_preflight"
CANDIDATE_SEEDS = tuple(range(4601, 4620))
TEXT_EXTENSIONS = {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".csv", ".toml"}
SKIP_PARTS = {".git", "__pycache__", "node_modules"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def candidate_seed_hits() -> tuple[int, dict[str, list[str]]]:
    # A bare number is not seed provenance: it can occur in a float, SVG
    # coordinate, hash-derived value, or episode identifier. Require a
    # seed-labelled field or a seed-prefixed run path on the same line.
    patterns = {
        str(seed): re.compile(
            rf"(?i)(?:\b(?:train(?:ing)?_?)?seeds?\b[^0-9\r\n]{{0,24}}\b{seed}\b|\bseed[_-]?{seed}\b)"
        )
        for seed in CANDIDATE_SEEDS
    }
    hits: dict[str, list[str]] = {str(seed): [] for seed in CANDIDATE_SEEDS}
    scanned = 0
    for root_name in ("algorithms", "configs", "docs", "envs", "paper", "scripts"):
        root = ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            if any(part in SKIP_PARTS for part in path.parts):
                continue
            relative = str(path.relative_to(ROOT)).replace("\\", "/")
            # The frozen proposal necessarily declares these seeds; it is not
            # evidence that a seed was previously used.
            if relative.startswith("docs/reliable_drtp_ensemble_p0/"):
                continue
            if relative == "scripts/preflight_reliable_drtp_ensemble_p1.py":
                continue
            scanned += 1
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for seed, pattern in patterns.items():
                if pattern.search(text) and relative not in hits[seed]:
                    hits[seed].append(relative)
    return scanned, {seed: locations for seed, locations in hits.items() if locations}


def run_tensor_checks() -> dict[str, bool]:
    torch.manual_seed(4600)
    first = torch.randn(2, 3, 7)
    second = torch.randn(2, 3, 7)
    third = torch.randn(2, 3, 7)
    one_probs = uniform_probability_pool([first])
    one_action, _ = pooled_categorical_action([first], deterministic=True)
    pooled = uniform_probability_pool([first, second, third])
    reordered = uniform_probability_pool([third, first, second])
    pooled_action, _ = pooled_categorical_action([first, second, third], deterministic=True)
    return {
        "one_member_probability_equivalence": bool(torch.allclose(one_probs, torch.softmax(first, dim=-1))),
        "one_member_deterministic_action_equivalence": bool(torch.equal(one_action, torch.argmax(first, dim=-1))),
        "pooled_simplex": bool(torch.allclose(pooled.sum(dim=-1), torch.ones_like(pooled[..., 0]), atol=1e-6)),
        "pooled_nonnegative": bool((pooled >= 0).all()),
        "member_order_invariance": bool(torch.allclose(pooled, reordered)),
        "pooled_action_shape": tuple(pooled_action.shape) == (2, 3),
        "member_shape_rejection": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("NO-GO: explicit --execute is required")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise FileExistsError(f"refusing to overwrite: {args.output_dir}")

    checks = run_tensor_checks()
    try:
        uniform_probability_pool([torch.zeros(2, 3, 7), torch.zeros(2, 3, 6)])
    except ValueError:
        checks["member_shape_rejection"] = True
    scanned, seed_hits = candidate_seed_hits()
    ready = all(checks.values()) and not seed_hits
    verdict = "RELIABILITY_ENSEMBLE_P1_PREFLIGHT_PASS" if ready else "RELIABILITY_ENSEMBLE_P1_PREFLIGHT_FAIL"
    payload = {
        "protocol": "RELIABILITY-ENSEMBLE-P1-PREFLIGHT-V1",
        "verdict": verdict,
        "zero_training": True,
        "checkpoints_loaded": False,
        "rollouts_started": False,
        "evaluation_started": False,
        "distillation_started": False,
        "mainline_a_modified": False,
        "tensor_checks": checks,
        "candidate_seed_audit": {
            "seeds": list(CANDIDATE_SEEDS),
            "files_scanned": scanned,
            "seed_identifier_hits": seed_hits,
            "scope": "algorithms, configs, docs, envs, paper, scripts; cloud archives and result bundles still require a launch-time provenance audit",
        },
        "implementation_boundary": {
            "aggregation": "uniform categorical probability average followed by pooled deterministic argmax",
            "training_side_tape_access": "not implemented; any future training entry point must reject all evaluation tape identifiers",
            "distillation": "not implemented and not authorized",
            "historical_interfaces_changed": False,
        },
        "source_hashes": {
            "algorithms/ri_gmappo/reliability_ensemble.py": sha256(
                ROOT / "algorithms" / "ri_gmappo" / "reliability_ensemble.py"
            ),
            "scripts/preflight_reliable_drtp_ensemble_p1.py": sha256(Path(__file__)),
        },
    }
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "RELIABILITY_ENSEMBLE_P1_PREFLIGHT.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )
    report = [
        "# Reliable-DRTP ensemble P1 technical preflight",
        "",
        f"**Verdict:** {verdict}.",
        "",
        "This preflight uses synthetic logits only. It loads no experiment checkpoint, creates no environment, starts no rollout/evaluation/training, and does not implement distillation.",
        "",
        "## Interface checks",
        "",
    ]
    report.extend([f"- {'PASS' if value else 'FAIL'} — {name}" for name, value in checks.items()])
    report.extend([
        "",
        "## Candidate seed audit",
        "",
        f"- Candidate seeds: {CANDIDATE_SEEDS[0]}–{CANDIDATE_SEEDS[-1]}",
        f"- Text files scanned: {scanned}",
        f"- Identifier hits: {seed_hits if seed_hits else 'none'}",
        "",
        "This is not a final cloud provenance decision. The execution launcher must re-audit archived run manifests and supplied assets before any training starts.",
        "",
        "## Stop boundary",
        "",
        "A pass means only that the default-off pooling primitive and preliminary source registry are ready. It does not authorize P1 member training, E-DRTP evaluation, distillation, K selection, member selection, or any continuation.",
    ])
    (args.output_dir / "RELIABILITY_ENSEMBLE_P1_PREFLIGHT.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )
    print(json.dumps({"verdict": verdict, "output": str(args.output_dir), "zero_training": True}))


if __name__ == "__main__":
    main()
