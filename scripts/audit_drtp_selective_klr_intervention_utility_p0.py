"""Audit whether a KLR archive can support exact historical A/B intervention branches.

This script is deliberately read-only: it opens a result tarball, checks the
trigger telemetry and saved-state granularity, and emits an audit JSON.  It
never imports the environment, restores a checkpoint, evaluates a policy, or
trains a model.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "algorithms" / "ri_gmappo" / "simple_ri_gmappo.py"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_csv(bundle: tarfile.TarFile, member: str) -> list[dict[str, str]]:
    source = bundle.extractfile(member)
    if source is None:
        raise RuntimeError(f"cannot read {member}")
    return list(csv.DictReader(io.TextIOWrapper(source, encoding="utf-8")))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    archive = args.archive.resolve()
    if not archive.is_file():
        raise FileNotFoundError(archive)
    source_text = SOURCE.read_text(encoding="utf-8")
    with tarfile.open(archive, "r:gz") as bundle:
        members = [item.name for item in bundle.getmembers() if item.isfile()]
        logs = sorted(
            member for member in members
            if "/runs/drtp_klr_sg/seed" in member and member.endswith("/train_log.csv")
        )
        if len(logs) != 10:
            raise RuntimeError(f"expected ten KLR train logs, found {len(logs)}")
        trigger_rows: dict[str, int] = {}
        attempted_rows: dict[str, int] = {}
        for member in logs:
            seed = member.split("/seed", 1)[1].split("/", 1)[0]
            rows = read_csv(bundle, member)
            if not rows:
                raise RuntimeError(f"empty train log: {member}")
            required = {"policy_guard_triggered", "policy_steps_attempted"}
            if not required <= set(rows[0]):
                raise RuntimeError(f"missing KLR telemetry columns in {member}")
            trigger_rows[seed] = sum(int(float(row["policy_guard_triggered"])) for row in rows)
            attempted_rows[seed] = sum(int(float(row["policy_steps_attempted"])) for row in rows)

        exact_trigger_snapshots = [
            member for member in members
            if "/runs/drtp_klr_sg/" in member
            and ("trigger_state" in member or "pre_trigger" in member or "intervention_snapshot" in member)
        ]
        runtime_snapshots = [
            member for member in members
            if "/runs/drtp_klr_sg/" in member and "runtime_state" in member
        ]
        milestone_runtime_only = bool(runtime_snapshots) and all(
            "milestone_250k" in member or "milestone_500k" in member or "latest" in member
            for member in runtime_snapshots
        )

    state_capture_markers = {
        "actor_transaction": "actor_state_before = copy.deepcopy(agent.actor.state_dict())" in source_text,
        "actor_optimizer_transaction": "actor_optimizer_state_before = _snapshot_optimizer_parameter_states" in source_text,
        "full_model_optimizer_transaction": "transaction_optimizer_state_before = copy.deepcopy(optimizer.state_dict())" in source_text,
        "environment_runtime_capture": "environment_states.append(runtime_state())" in source_text,
        "python_numpy_torch_rng_capture": all(
            marker in source_text
            for marker in ("random.getstate()", "np.random.get_state()", "torch.get_rng_state()")
        ),
    }
    historical_exact_feasible = bool(exact_trigger_snapshots)
    decision = (
        "HISTORICAL_EXACT_COUNTERFACTUAL_FEASIBLE"
        if historical_exact_feasible
        else "HISTORICAL_EXACT_COUNTERFACTUAL_NOT_FEASIBLE"
    )
    payload = {
        "protocol": "DRTP-SELECTIVE-KLR-INTERVENTION-UTILITY-P0-V1",
        "archive": archive.name,
        "archive_sha256": sha256(archive),
        "read_only": True,
        "training_started": False,
        "evaluation_started": False,
        "algorithm_modification_authorized": False,
        "source_sha256": sha256(SOURCE),
        "trigger_population": {
            "rule": "all archived post-step KL > 0.02 guard events",
            "seeds": sorted(trigger_rows),
            "trigger_count_by_seed": trigger_rows,
            "attempt_count_by_seed": attempted_rows,
            "total_triggers": sum(trigger_rows.values()),
            "total_attempts": sum(attempted_rows.values()),
        },
        "archive_state_granularity": {
            "runtime_state_files": len(runtime_snapshots),
            "milestone_runtime_only": milestone_runtime_only,
            "exact_trigger_snapshot_files": exact_trigger_snapshots,
        },
        "prospective_infrastructure_markers": state_capture_markers,
        "decision": decision,
        "reason": (
            "The archive contains only milestone/latest runtime states and no pre-trigger snapshot linked to each KLR event. "
            "A later checkpoint cannot recreate an exact accept-versus-rollback counterfactual."
            if not historical_exact_feasible
            else "Exact trigger-linked snapshots were found; a separate protocol is still required before branch execution."
        ),
        "next_authorized_scope": (
            "none; a prospective trigger-snapshot instrumentation contract requires separate human authorization"
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"decision": decision, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
