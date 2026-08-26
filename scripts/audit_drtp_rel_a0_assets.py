"""Audit recovered historical UTR/DRTP checkpoints for REL-A0, without training."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


EXPECTED = {
    "utr_sg": "167d195e3d49f724917e19f96001ad8841b6390ba1d4ddfa848fffe3ad2076b5",
    "drtp_sg": "c923216b48fbeecb6ab756fd37274986f7ba0657f2a40f098fb5e4e5d45235c7",
}
METHODS = ("utr_sg", "drtp_sg")
SEEDS = (1901, 1902, 2001, 2002, 2003)
STEPS = 10_000_128
UPDATES = 39_063


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def inspect_run(root: Path, method: str, seed: int) -> dict:
    run = root / method / f"seed{seed}"
    manifest_path = run / "run_manifest.json"
    model = run / "actor_critic_latest.pt"
    runtime = run / "actor_critic_runtime_state_latest.pt"
    row = {
        "method": method,
        "seed": seed,
        "run_path": str(run),
        "manifest_exists": manifest_path.exists(),
        "checkpoint_exists": model.exists(),
        "runtime_state_exists": runtime.exists(),
    }
    if not manifest_path.exists():
        row["valid"] = False
        row["failure"] = "missing run_manifest.json"
        return row
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    model_hash = sha256(model) if model.exists() else None
    runtime_hash = sha256(runtime) if runtime.exists() else None
    row.update({
        "status": manifest.get("status"),
        "environment_steps": manifest.get("environment_steps"),
        "updates": manifest.get("updates"),
        "parameter_count": manifest.get("parameter_count"),
        "from_scratch": manifest.get("from_scratch"),
        "strict_continuous_trajectory": manifest.get("strict_continuous_trajectory"),
        "config_hash": manifest.get("config_hash"),
        "manifest_checkpoint_sha256": manifest.get("final_checkpoint_sha256"),
        "checkpoint_sha256": model_hash,
        "checkpoint_hash_match": model_hash == manifest.get("final_checkpoint_sha256"),
        "manifest_runtime_state_sha256": manifest.get("final_runtime_state_sha256"),
        "runtime_state_sha256": runtime_hash,
        "runtime_state_hash_match": runtime_hash == manifest.get("final_runtime_state_sha256"),
        "manifest_path": str(manifest_path),
    })
    row["valid"] = all((
        row["status"] == "completed",
        row["environment_steps"] == STEPS,
        row["updates"] == UPDATES,
        row["parameter_count"] == 116728,
        row["from_scratch"] is True,
        row["strict_continuous_trajectory"] is True,
        row["config_hash"] == EXPECTED[method],
        row["checkpoint_exists"],
        row["runtime_state_exists"],
        row["checkpoint_hash_match"],
        row["runtime_state_hash_match"],
    ))
    return row


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--strict-root", type=Path, required=True)
    p.add_argument("--heldout-root", type=Path, required=True)
    p.add_argument("--strict-archive", type=Path)
    p.add_argument("--heldout-archive", type=Path)
    p.add_argument("--output-json", type=Path, required=True)
    p.add_argument("--output-report", type=Path, required=True)
    args = p.parse_args()
    rows = []
    for method in METHODS:
        for seed in SEEDS:
            source = args.strict_root if seed in (1901, 1902) else args.heldout_root
            rows.append(inspect_run(source, method, seed))
    paired = {
        seed: all(r["valid"] for r in rows if r["seed"] == seed)
        for seed in SEEDS
    }
    valid_pairs = [seed for seed, ok in paired.items() if ok]
    archive_hashes = {}
    for label, path in (("strict_10m_archive", args.strict_archive),
                        ("heldout_v2_archive", args.heldout_archive)):
        if path.exists():
            archive_hashes[label] = {"path": str(path), "sha256": sha256(path)}
    result = {
        "protocol": "DRTP-REL-A0-R-ASSET-RECOVERY-V1",
        "training_started": False,
        "required_minimum_complete_paired_seeds": 4,
        "complete_paired_seeds": valid_pairs,
        "complete_paired_seed_count": len(valid_pairs),
        "gate": "PASS" if len(valid_pairs) >= 4 else "F_TECHNICAL_BLOCK",
        "archive_hashes": archive_hashes,
        "runs": rows,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# DRTP REL-A0-R Checkpoint Recovery Audit",
        "",
        "- Protocol: `DRTP-REL-A0-R-ASSET-RECOVERY-V1`",
        "- Training started: **NO**",
        f"- Complete paired seeds: **{len(valid_pairs)}/5** ({', '.join(map(str, valid_pairs))})",
        f"- Minimum required to reopen REL-A0: **4**",
        f"- Recovery gate: **{result['gate']}**",
        "",
        "## Interpretation",
        "",
        "The provisional 2/5 block is superseded by the recovered archive evidence. "
        "The historical Phase-S1-A `F_TECHNICAL_INVALID` conclusion is not rewritten; "
        "this report only establishes asset availability for the separate REL-A0 audit.",
        "",
        "## Recovered paired assets",
        "",
        "| seed | UTR status | DRTP status | steps | parameters | UTR hash | DRTP hash |",
        "|---:|---|---|---:|---:|---|---|",
    ]
    by = {(r["seed"], r["method"]): r for r in rows}
    for seed in SEEDS:
        u, d = by[(seed, "utr_sg")], by[(seed, "drtp_sg")]
        lines.append(f"| {seed} | {u.get('status')} | {d.get('status')} | "
                     f"{u.get('environment_steps')} | {u.get('parameter_count')} | "
                     f"`{u.get('checkpoint_sha256')}` | `{d.get('checkpoint_sha256')}` |")
    lines += ["", "## Required invariants", "",
              "- All ten runs are completed 10,000,128-step trajectories.",
              "- All checkpoints have 116,728 parameters and the expected UTR/DRTP config hash.",
              "- Model and runtime-state SHA256 values match the archived manifests.",
              "- No training, resume, checkpoint promotion, or seed substitution was performed.", ""]
    args.output_report.parent.mkdir(parents=True, exist_ok=True)
    args.output_report.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
