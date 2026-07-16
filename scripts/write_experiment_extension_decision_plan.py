from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "results" / "experiment_extension_decision_plan.csv"
OUT_MD = ROOT / "docs" / "experiment_extension_decision_plan.md"


@dataclass(frozen=True)
class ExperimentOption:
    option_id: str
    priority: str
    status: str
    experiment: str
    purpose: str
    current_evidence: str
    dependency: str
    estimated_cost: str
    decision_rule: str
    paper_use: str


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def build_options() -> list[ExperimentOption]:
    lag_data_exists = (ROOT.parent / "LAG" / "envs" / "JSBSim" / "data").exists()
    final_main_ready = exists("results/final_comm_300_summary.csv") and exists("results/final_300_paired_statistics.csv")
    lag_adapter_ready = exists("results/lag_role_graph_adapter_test.csv") and exists("results/lag_role_graph_wrapper_test.csv")

    return [
        ExperimentOption(
            "E1",
            "high",
            "ready" if final_main_ready else "blocked",
            "Five-seed final 300-episode evaluation extension",
            "Increase statistical credibility if the target venue or adviser asks for stronger seed evidence.",
            "Current main evidence: 3 seeds, 300 episodes per seed, final table and paired descriptive intervals pass all gates.",
            "Requires two additional trained/evaluable seeds per method, or a deliberate decision to evaluate only available checkpoints if training already exists.",
            "High: 2 extra seeds x 3 methods x 4 radii x 300 episodes, plus checkpoint management if new training is required.",
            "Run only if reviewer/adviser requests stronger statistics, or if targeting a stricter venue than Drones/Aerospace/JIRS.",
            "Strengthens main-result confidence; does not change the core innovation.",
        ),
        ExperimentOption(
            "E2",
            "high",
            "blocked" if not lag_data_exists else "ready",
            "Real LAG/JSBSim reset-one-step role-graph probe",
            "Convert the current LAG-like adapter smoke test into a real JSBSim interface validation.",
            f"Adapter ready={lag_adapter_ready}; current probe reports JSBSim data present={lag_data_exists}.",
            "Requires LAG envs/JSBSim/data and missing import path fixes before real env reset.",
            "Medium once dependencies exist: one-step/reset probe plus 100-step graph-stat CSV.",
            "Do this before any claim about 6DOF validation or before starting LAG training.",
            "Supports migration-readiness evidence; still not enough for a full 6DOF performance claim.",
        ),
        ExperimentOption(
            "E3",
            "medium",
            "deferred",
            "Retrained edge-feature structural ablation",
            "Separate the effect of edge features from evaluation-time feature masking.",
            "Current evidence includes training-time communication ablation and evaluation-time edge masking diagnostic.",
            "Requires retraining no-edge/partial-edge variants under matching budget.",
            "High: new training runs and final evaluations; risk of consuming time without changing main conclusion.",
            "Run only if reviewers question whether evaluation-time masking is sufficient for mechanism analysis.",
            "Could upgrade mechanism evidence from diagnostic to stronger ablation, but is not necessary for the current core claim.",
        ),
        ExperimentOption(
            "E4",
            "medium",
            "ready",
            "Longer communication-dropout evaluation",
            "Increase robustness diagnostic confidence under degraded communication links.",
            "Current dropout diagnostic: 50 episodes per seed, all tested dropout probabilities pass lower-collision checks.",
            "Requires only existing checkpoints and evaluation script.",
            "Medium: can extend from 50 to 100 or 300 episodes per seed at radii 4 and 8.",
            "Run if dropout robustness becomes a central claim rather than appendix support.",
            "Strengthens appendix robustness; avoid replacing the 300-episode main table.",
        ),
        ExperimentOption(
            "E5",
            "low",
            "deferred",
            "Full 6DOF LAG training with EA-RG-MAPPO-S",
            "Evaluate whether the finite-communication role graph method transfers beyond the 2D pursuit environment.",
            "Only interface-level LAG adapter and synthetic smoke tests are currently available.",
            "Requires E2 success, MultiDiscrete action head adaptation, JSBSim training stability, and new metrics.",
            "Very high: environment debugging, action-head redesign, slow training, and new baselines.",
            "Start only after the current 2D paper is submitted or if the first target journal requires stronger realism.",
            "Potential second paper or major revision; should not be forced into the current manuscript prematurely.",
        ),
        ExperimentOption(
            "E6",
            "low",
            "deferred",
            "Missile/radar/human-UAV cooperative system extension",
            "Move from cooperative pursuit to a richer air-combat system model.",
            "Current paper has no validated missile, radar, or human-UAV teaming experiment.",
            "Requires 6DOF environment, sensor/weapon models, human/leader policy abstraction, and new safety constraints.",
            "Very high: essentially a new system-level research project.",
            "Do not start until E5 has a stable baseline and a clear second-paper question.",
            "Future-work roadmap only; never use as current validation evidence.",
        ),
        ExperimentOption(
            "E7",
            "medium",
            "ready",
            "Journal-template migration experiment-free pass",
            "Convert the current evidence-backed English manuscript into the selected journal template.",
            "Manuscript evidence, numeric consistency, label/reference, and completeness audits all pass.",
            "Requires target journal decision and full LaTeX toolchain for PDF compilation.",
            "Medium: formatting, declarations, figure/table placement, bibliography style.",
            "Do before running expensive new experiments unless a target venue explicitly requires more realism/statistics.",
            "Turns the current work into a submission package without changing experimental claims.",
        ),
    ]


def write_csv(options: list[ExperimentOption]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    fields = list(ExperimentOption.__dataclass_fields__.keys())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for option in options:
            writer.writerow(option.__dict__)


def write_report(options: list[ExperimentOption]) -> None:
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    for option in options:
        counts[option.status] = counts.get(option.status, 0) + 1
    lines = [
        "# Experiment Extension Decision Plan",
        "",
        f"Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "Purpose:",
        "",
        "```text",
        "Prioritize optional next experiments after the current EA-RG-MAPPO-S evidence chain.",
        "The plan separates paper-strengthening experiments from future-system extensions so the current manuscript does not expand beyond what is feasible.",
        "```",
        "",
        "## Summary",
        "",
        "```text",
        f"options = {len(options)}",
        *[f"{key} = {value}" for key, value in sorted(counts.items())],
        "```",
        "",
        "## Recommended Order",
        "",
        "```text",
        "1. First choose target journal and template route.",
        "2. If the target is practical Q2 (Drones/Aerospace/JIRS), prioritize template/PDF migration before expensive new experiments.",
        "3. If adviser/reviewer asks for stronger evidence, choose between E1 five-seed extension and E2 real LAG reset probe.",
        "4. Treat full 6DOF training and missile/radar/human-UAV teaming as later projects, not current-paper requirements.",
        "```",
        "",
        "## Options",
        "",
        "| ID | Priority | Status | Experiment | Purpose | Dependency | Cost | Decision rule | Paper use |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for option in options:
        lines.append(
            f"| {option.option_id} | {option.priority} | {option.status} | {option.experiment} | "
            f"{option.purpose} | {option.dependency} | {option.estimated_cost} | "
            f"{option.decision_rule} | {option.paper_use} |"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "```text",
            "Rules, masks, and engineering constraints may support experiments but should not be written as the main innovation.",
            "Do not start missile/radar/human-UAV extensions until a real 6DOF baseline is stable.",
            "Do not claim LAG/JSBSim validation until a real reset/step probe and evaluation output exist.",
            "```",
            "",
        ]
    )
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    options = build_options()
    write_csv(options)
    write_report(options)
    print(OUT_CSV)
    print(OUT_MD)
    print(f"options: {len(options)}")
    for status in sorted({option.status for option in options}):
        print(f"{status}: {sum(1 for option in options if option.status == status)}")


if __name__ == "__main__":
    main()
