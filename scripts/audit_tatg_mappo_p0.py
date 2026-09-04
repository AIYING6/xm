"""Static P0 audit for the new topology-transition-memory research problem."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def all_present(text: str, tokens: list[str]) -> bool:
    return all(token in text for token in tokens)


def collect_checks(root: Path) -> dict[str, bool]:
    trainer = (root / "algorithms/ri_gmappo/simple_ri_gmappo.py").read_text(encoding="utf-8")
    env = (root / "envs/uav_intercept_3d_env.py").read_text(encoding="utf-8")
    sampler = (root / "algorithms/ri_gmappo/tcr_topology_sampler.py").read_text(encoding="utf-8")
    actor_section = trainer[trainer.index("class RIActor(nn.Module):") : trainer.index("class RIGMAPPOAgent(nn.Module):")]
    return {
        "snapshot_graph_actor_exists": "class RIActor(nn.Module):" in trainer,
        "snapshot_actor_has_no_memory_module": "nn.GRU" not in actor_section and "nn.LSTM" not in actor_section,
        "actor_receives_current_legal_graph_tensors": all_present(
            actor_section,
            ["obs: torch.Tensor", "node_feat: torch.Tensor", "edge_feat: torch.Tensor | None", "adj: torch.Tensor"],
        ),
        "actor_does_not_receive_failure_schedule": "failure_start_step" not in actor_section and "failed_blue_agent" not in actor_section,
        "dynamic_failure_transition_exists": all_present(
            env,
            ["node_failure_start_step", "node_failure_duration_steps", "def _is_comm_failed"],
        ),
        "legal_temporal_proxies_exist": all_present(
            env,
            ["self._local_inbound_message_age(i)", "self._local_target_cache_age(i)"],
        ),
        "fixed_exposure_baseline_exists": "class FixedStratifiedTopologySampler" in sampler,
        "runtime_state_persistence_exists": all_present(trainer, ["runtime_state_checkpointing", "actor_critic_runtime_state"]),
    }


def result_from_checks(checks: dict[str, bool]) -> dict[str, object]:
    feasible = all(checks.values())
    return {
        "protocol": "TATG-MAPPO-P0-SEMANTIC-AND-NOVELTY-AUDIT-V1",
        "verdict": "TATG_P0_FEASIBLE_FOR_P1_INFORMATION_GAP_PROBE" if feasible else "TATG_P0_NO_GO",
        "checks": checks,
        "training_started": False,
        "evaluation_started": False,
        "environment_steps": 0,
        "ppo_updates": 0,
        "recurrent_policy_implemented": False,
        "automatic_continuation": False,
    }


def write_lf(path: Path, text: str) -> None:
    path.write_bytes(text.replace("\r\n", "\n").encode("utf-8"))


def render_report(result: dict[str, object]) -> str:
    lines = [
        "# TATG-MAPPO P0 semantic and novelty audit",
        "",
        f"**Verdict:** `{result['verdict']}`.",
        "",
        "P0 only establishes that a new, actor-legal information-sufficiency question is technically testable. It makes no claim that the current actor is insufficient, that memory improves return, or that a recurrent policy should be implemented.",
        "",
        "## Distinction from the closed DRTP stabilization programme",
        "",
        "This route does not seek a bad-seed precursor, change the training sampler, change group weights, project gradients, blend policies or select a checkpoint. Its unit of analysis is the environment-level information available to a single decentralized actor during a topology transition, not a post-hoc association with seed outcomes.",
        "",
        "## Static checks",
        "",
    ]
    lines.extend(f"- `{key}`: `{value}`" for key, value in result["checks"].items())
    lines += [
        "",
        "## P1 boundary",
        "",
        "P1 may use only fresh scripted, policy-neutral trajectories and legal actor tensors. It must compare a current snapshot with a fixed short history against a predeclared transition target, in two disjoint state cohorts. It must not use a learned policy, episode return, final quality label, checkpoint, or any evaluation tape. A P1 pass authorizes only an exact formula audit; a fail closes the entire TATG route before implementation.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("Refusing to write without --execute")
    output = Path(args.output_dir)
    if output.exists():
        raise SystemExit(f"Refusing to overwrite existing output: {output}")
    output.mkdir(parents=True)
    result = result_from_checks(collect_checks(ROOT))
    write_lf(output / "TATG_P0_RESULT.json", json.dumps(result, indent=2) + "\n")
    write_lf(output / "TATG_P0_REPORT.md", render_report(result))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
