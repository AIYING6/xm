"""Static P0.5 audit of B-line timing semantics and actor legality.

This program reads source text only.  It deliberately does not instantiate an
environment, step an environment, load a checkpoint, run a solver, or train a
policy.  Its purpose is to keep native environment semantics separate from
legal temporal state and from the additional continuity contract used in P0.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "configs" / "b_line_p05_environment_semantic_audit_freeze.json"


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_lf(path: Path, payload: str) -> None:
    path.write_bytes(payload.replace("\r\n", "\n").encode("utf-8"))


def source(path_text: str) -> tuple[Path, str, str]:
    path = ROOT / path_text
    text = path.read_text(encoding="utf-8")
    return path, text, hashlib.sha256(path.read_bytes()).hexdigest()


def require_markers(text: str, markers: tuple[str, ...], label: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise RuntimeError(f"{label} source markers missing: {missing}")


def audit() -> tuple[dict[str, Any], list[dict[str, str]]]:
    freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
    _, intercept, intercept_hash = source("envs/uav_intercept_3d_env.py")
    _, redundant, redundant_hash = source("envs/redundant_topology_uav_env.py")
    _, tatg_rollout, tatg_rollout_hash = source("algorithms/ri_gmappo/tatg_outer_rollout.py")
    _, redundant_runner, redundant_runner_hash = source("scripts/run_redundant_topology_uav_p2.py")

    require_markers(
        intercept,
        (
            "max_target_message_age_steps: int = 80",
            "if cache_age > float(self.config.max_target_message_age_steps):",
            "self._local_inbound_message_age(i) / self.config.max_steps",
            "self._local_target_cache_age(i) / self.config.max_steps",
            "age = self.message_age[i, j] / self.config.max_steps",
            '"node_failure_active": float(any(self._is_comm_failed(i)',
        ),
        "3D interception",
    )
    require_markers(
        tatg_rollout,
        (
            'edge_t = torch.as_tensor(graph_obs["edge_feat"]',
            'relation_t = torch.as_tensor(graph_obs["relation_adj"]',
            "actor_step = runner.act(",
        ),
        "TATG actor rollout",
    )
    require_markers(
        redundant,
        (
            "tau_max: int = 5",
            'valid = token["age"] <= self.config.tau_max and token["valid"]',
            "def support_action_mask(self, terminal: int)",
            "Relay actions are ignored; forwarding is a frozen network operation",
            '"active_adj": self.last_active.copy()',
        ),
        "redundant-topology",
    )
    require_markers(
        redundant_runner,
        (
            '"adj": np.stack([g["active_adj"] for g in graphs])',
            "def collect(agent:",
        ),
        "redundant-topology actor runner",
    )

    # The conclusion is intentionally conservative.  The sources contain a
    # native freshness deadline, but no native rule coupling a *continuous
    # route outage* to a mandatory relay-reconfiguration action.  In
    # particular, 3D has motion actions rather than a reconfigure command,
    # while the redundant environment explicitly ignores relay actions.
    rows = [
        {
            "item": "3D message/cache freshness",
            "classification": "environment_native_semantics",
            "finding": "Per-link message age and per-agent target-cache age advance with unavailable delivery; relay-dependent targeting rejects cache age beyond max_target_message_age_steps.",
            "actor_legality": "Actor-local observations include normalized inbound-message age and cache age; TATG actor also receives edge age and communication relations.",
            "effect": "Native information validity / targeting availability changes; it is not a route-outage termination or mandatory reconfiguration rule.",
        },
        {
            "item": "3D node-failure schedule",
            "classification": "environment_native_semantics",
            "finding": "A configured node failure has a start step and duration and suppresses communication delivery.",
            "actor_legality": "node_failure_active and failed_blue_agent appear in info telemetry, not the actor observation boundary; they must not be used as direct actor inputs.",
            "effect": "Failure is native, but no maximum consecutive outage or relay-reconfiguration action is imposed.",
        },
        {
            "item": "6-UAV cache freshness",
            "classification": "environment_native_semantics",
            "finding": "A routed objective token is valid only while age <= tau_max; stale tokens remove terminal objective actions through the existing legal action mask.",
            "actor_legality": "The current active adjacency is supplied to the role graph actor; terminal token availability is in local actor observations and action masks.",
            "effect": "Native cache age changes the real currently legal terminal-action set, but it is data freshness, not a measured consecutive route-outage duration.",
        },
        {
            "item": "Temporal reconstruction",
            "classification": "legally_derivable_internal_state",
            "finding": "An actor with its own past legal adjacency or age observations can deterministically retain a history summary without using future state or evaluation data.",
            "actor_legality": "Legal only when the update consumes the same actor-visible current topology/age features; it cannot consume info-only failure labels.",
            "effect": "Supports a future history-aware formulation, but does not create a native reconfiguration requirement by itself.",
        },
        {
            "item": "P0 maximum consecutive outage with relay reconfiguration",
            "classification": "newly_introduced_assumption",
            "finding": "The P0 three-slot continuity limit and its reconfigure_relay action are not jointly encoded by either current environment.",
            "actor_legality": "No legality issue can rescue a non-native action/constraint pair.",
            "effect": "The existing P0 counterexample cannot be promoted as an exact target-environment reconfiguration problem.",
        },
    ]
    result = {
        "protocol": freeze["protocol"],
        "verdict": "B_P05_SEMANTIC_PARTIAL",
        "source_sha256": {
            "uav_intercept_3d_env.py": intercept_hash,
            "redundant_topology_uav_env.py": redundant_hash,
            "tatg_outer_rollout.py": tatg_rollout_hash,
            "run_redundant_topology_uav_p2.py": redundant_runner_hash,
        },
        "checks": {
            "native_time_dependent_information_semantics": True,
            "native_cache_freshness_can_change_task_information_or_legal_terminal_actions": True,
            "actor_legal_age_or_topology_signal_exists": True,
            "info_only_failure_labels_excluded_from_actor_legality": True,
            "native_maximum_consecutive_route_outage_requirement": False,
            "native_mandatory_relay_reconfiguration_action": False,
            "p0_exact_outage_reconfiguration_pair_is_environment_native": False,
        },
        "conclusion": (
            "The scientific information-gap question remains plausible only after reformulation around native cache/message freshness. "
            "The existing P0 outage-duration/reconfigure-relay counterexample is not an exact target-environment statement."
        ),
        "allowed_next_step": "At most a new zero-training P0 reformulation audit grounded in a declared native freshness state and an existing action interface; no solver or P1 is authorized.",
        "environment_steps": 0,
        "ppo_updates": 0,
        "training_started": False,
        "evaluation_started": False,
        "automatic_continuation": False,
    }
    return result, rows


def render_report(result: dict[str, Any], rows: list[dict[str, str]]) -> str:
    lines = [
        "# B-line P0.5 environment semantic audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "This static audit reads source files only: zero environment construction or steps, PPO updates, solver calls, training, checkpoint loading, evaluation episodes, and evaluation-tape reads.",
        "",
        "## Decision",
        "",
        "The current environments do contain native, time-dependent information semantics: message/cache age, cache freshness limits, and—within the six-UAV environment—an action mask that removes actions lacking a fresh routed token. The relevant age/topology information is actor-legal in the existing interfaces, while `info`-only failure labels are excluded.",
        "",
        "However, neither audited environment contains the exact pair assumed in B-line P0: a maximum **consecutive route-outage** contract coupled to an available `reconfigure_relay` action. Therefore the P0 toy counterexample cannot be upgraded as an exact reconfiguration problem for the present environment.",
        "",
        "## Classification ledger",
        "",
        "| Item | Classification | Consequence |",
        "| --- | --- | --- |",
    ]
    for row in rows:
        lines.append(f"| {row['item']} | `{row['classification']}` | {row['effect']} |")
    lines += [
        "",
        "## Boundary",
        "",
        "This is not `B_P05_SEMANTIC_NO_GO`: a native history-sensitive freshness problem exists. It is not `B_P05_SEMANTIC_PASS`: the exact P0 continuity/reconfiguration assumption is new rather than environment-native.",
        "",
        "The only scientifically permitted follow-up is a fresh, zero-training P0 reformulation that uses an explicitly chosen native freshness state and an existing action interface. It must again establish whether same current snapshot but distinct legal histories force distinct decisions. Solver design, PPO, benchmark training, parameter changes, and environment/reward changes remain prohibited.",
        "",
    ]
    return "\n".join(lines)


def write_outputs(output_dir: Path, result: dict[str, Any], rows: list[dict[str, str]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    write_lf(output_dir / "B_P05_ENVIRONMENT_SEMANTIC_AUDIT_RESULT.json", canonical_json(result))
    fields = ("item", "classification", "finding", "actor_legality", "effect")
    with (output_dir / "B_P05_ENVIRONMENT_SEMANTIC_LEDGER.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    write_lf(output_dir / "B_P05_ENVIRONMENT_SEMANTIC_AUDIT.md", render_report(result, rows))
    hashes = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(output_dir.iterdir()) if path.is_file()
    }
    write_lf(output_dir / "B_P05_ENVIRONMENT_SEMANTIC_ARTIFACTS.json", canonical_json(hashes))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to run P0.5 audit without --execute")
    output_dir = Path(args.output_dir)
    if output_dir.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output_dir}")
    result, rows = audit()
    write_outputs(output_dir, result, rows)


if __name__ == "__main__":
    main()
