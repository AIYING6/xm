"""Static, zero-rollout audit for a topology-distinct failure benchmark.

The audit intentionally distinguishes a physically possible communication
channel from a target-information route that is legal under the frozen
relay-dependent task. It does not import or instantiate the environment.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path


NODES = ("Scout", "Relay", "Attacker")
PRIMARY = (("Scout", "Relay"), ("Relay", "Attacker"))


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def reachable(edges: set[tuple[str, str]], source: str, target: str) -> bool:
    queue: deque[str] = deque([source])
    seen = {source}
    while queue:
        node = queue.popleft()
        for start, end in edges:
            if start == node and end not in seen:
                if end == target:
                    return True
                seen.add(end)
                queue.append(end)
    return source == target


def shortest_path_length(edges: set[tuple[str, str]], source: str, target: str) -> int | None:
    queue: deque[tuple[str, int]] = deque([(source, 0)])
    seen = {source}
    while queue:
        node, length = queue.popleft()
        if node == target:
            return length
        for start, end in edges:
            if start == node and end not in seen:
                seen.add(end)
                queue.append((end, length + 1))
    return None


def signatures(edges: set[tuple[str, str]]) -> dict[str, object]:
    closure = {(a, b): reachable(edges, a, b) for a in NODES for b in NODES if a != b}
    return {
        "edges": sorted(f"{a}->{b}" for a, b in edges),
        "in_degree": {node: sum(end == node for _, end in edges) for node in NODES},
        "out_degree": {node: sum(start == node for start, _ in edges) for node in NODES},
        "reachability": {f"{a}->{b}": ok for (a, b), ok in closure.items()},
        "scout_to_attacker_reachable": reachable(edges, "Scout", "Attacker"),
        "scout_to_attacker_shortest_path": shortest_path_length(edges, "Scout", "Attacker"),
        "primary_path_count": 1 if set(PRIMARY).issubset(edges) else 0,
    }


def md_table(headers: list[str], rows: list[list[str]]) -> str:
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(" --- " for _ in headers) + "|",
        *["| " + " | ".join(row) + " |" for row in rows],
    ])


def write(path: Path, content: str) -> None:
    path.write_bytes((content.rstrip() + "\n").encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/new_topology_failure_p0_audit_20260902.json")
    parser.add_argument("--output-dir", default="docs/new_topology_failure_p0_audit_20260902")
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    physical = {tuple(edge) for edge in config["physical_directed_channels"]}
    nominal_task = set(PRIMARY)
    candidates: dict[str, dict[str, object]] = {}

    def add(name: str, removed: set[tuple[str, str]], kind: str, note: str) -> None:
        task_edges = nominal_task - removed
        sig = signatures(task_edges)
        candidates[name] = {
            "name": name,
            "kind": kind,
            "removed_physical_channels": sorted(f"{a}->{b}" for a, b in removed),
            "fault_mask_zeroes": sorted(f"{a}->{b}" for a, b in removed),
            "task_graph": sig,
            "note": note,
            "mask_hash": digest({"zeroes": sorted(removed)}),
            "signature_hash": digest(sig),
        }

    for edge in sorted(physical):
        role = f"TD-{edge[0][0]}{edge[1][0]}"
        add(role, {edge}, "single_directed_edge", "enumerated from the physical blue-team communication layer")
    add("TD-RX", {("Scout", "Relay"), ("Attacker", "Relay")}, "relay_inbound_partial", "partial Relay receive-channel outage")
    add("TD-RT", {("Relay", "Scout"), ("Relay", "Attacker")}, "relay_outbound_partial", "partial Relay transmit-channel outage")
    add("TD-RN", {edge for edge in physical if "Relay" in edge}, "full_relay_node", "existing relay-node outage; direct Scout->Attacker recovery is separately enabled by frozen task semantics")
    add("TD-CUT", {("Scout", "Relay"), ("Relay", "Attacker")}, "compound_primary_cut", "removes both nominal target-information edges")

    # Normal task-information equivalence: any removal containing either
    # primary serial edge destroys the sole nominal target-information path.
    equivalent: dict[str, list[str]] = {"nominal_primary_path_intact": [], "primary_path_cut": [], "recovery_reconfigured": []}
    rejected: list[dict[str, str]] = []
    for name, item in candidates.items():
        removed = set(tuple(edge.split("->")) for edge in item["removed_physical_channels"])
        if name == "TD-RN":
            equivalent["recovery_reconfigured"].append(name)
            rejected.append({"candidate": name, "reason": "not a pure multiplicative edge mask: frozen Relay-node-failure semantics additionally permit a direct recovery route"})
        elif {("Scout", "Relay"), ("Relay", "Attacker")} & removed:
            equivalent["primary_path_cut"].append(name)
            rejected.append({"candidate": name, "reason": "cuts the only nominal legal Scout→Relay→Attacker target-information path; terminal stress reference, not a recoverable ordinary group"})
        else:
            equivalent["nominal_primary_path_intact"].append(name)
            rejected.append({"candidate": name, "reason": "does not alter the frozen nominal legal target-information path; no policy-free task-relevant structural effect established"})

    nominal_signature = signatures(nominal_task)
    verdict = {
        "protocol": config["protocol"],
        "verdict": "TOPOLOGY_CLASSES_INSUFFICIENT",
        "checks": {
            "physical_directed_channels_enumerated": True,
            "fault_masks_policy_independent_in_principle": True,
            "actor_information_boundary_preservable": True,
            "at_least_three_non_equivalent_recoverable_failure_classes": False,
            "existing_failure_interface_can_be_extended_locally": True,
            "requires_actor_reward_or_old_benchmark_rewrite": False,
            "training_started": False,
            "rollout_started": False,
            "evaluation_started": False,
        },
        "nominal_task_graph_hash": digest(nominal_signature),
        "candidate_masks_hash": digest(candidates),
        "retained_ordinary_failure_classes": [],
        "terminal_stress_references": equivalent["primary_path_cut"],
        "p1_authorized": False,
    }

    machine = {"verdict": verdict, "nominal_task_graph": nominal_signature, "candidates": candidates,
               "equivalence_classes": equivalent, "rejected": rejected}
    write(out / "NEW_TOPOLOGY_FAILURE_P0_AUDIT.json", json.dumps(machine, ensure_ascii=False, indent=2))

    write(out / "NEW_TOPOLOGY_FAILURE_P0_CONTRACT.md", """# Topology-Distinct Failure Benchmark — P0 contract

This independent line audits only the existing environment's graph, information legality, and candidate fault masks. Original DRTP, the old F0/TE/TL/DS/DL/CP benchmark, A-line results, policies, rewards, observations, seeds, rollouts, and evaluations are untouched.

P0 asks whether the current three-blue-UAV task naturally supports at least three topology-distinct, recoverable, policy-independent failure classes. It does not design a sampler or algorithm and cannot enter training automatically.
""")

    write(out / "CURRENT_GRAPH_SEMANTICS_AUDIT.md", f"""# Current graph semantics audit

`A[receiver, sender] = 1`: row `receiver` aggregates information from column `sender`. The GAT masks scores by this adjacency and computes a receiver-wise weighted sum over senders.

The physical blue-team communication layer may contain all six directed channels when geometry/range/dropout allow it:

{', '.join(sorted(f'{a}→{b}' for a, b in physical))}.

Communication is recalculated each step from inter-agent distance, range, node-failure state, and communication-dropout RNG. The graph's communication relation contains delivered communication; task-support is never an independent hidden channel because it requires delivered communication first.

Under the relay-dependent information contract, the nominal legal target-information route is `Scout → Relay → Attacker`. Direct `Scout → Attacker` cache delivery is rejected in nominal operation and becomes legal only as a recovery route during the existing full Relay-node-failure state. Actor input is limited to `obs`, `share_obs`, and the legal graph observation; simulator state, fault labels, full cache provenance, and unmasked topology cannot be passed as an actor feature.
""")

    enum_rows = []
    for name, item in candidates.items():
        enum_rows.append([name, str(item["kind"]), ", ".join(item["fault_mask_zeroes"]), str(item["task_graph"]["scout_to_attacker_reachable"]), item["mask_hash"][:12]])
    write(out / "LEGAL_EDGE_AND_NODE_FAILURE_ENUMERATION.md", f"""# Legal edge and node failure enumeration

The following candidates are enumerated from actual blue-team channels; their masks are deterministic and policy-independent. A future implementation would have to apply the mask **before both message delivery/cache updates and graph construction**. The current OOD prune hook occurs after some cache processing, so it is insufficient by itself as a strict information-failure interface.

{md_table(["Candidate", "Kind", "Masked directed channels", "Nominal S→A task path remains", "Mask hash"], enum_rows)}

This enumeration is descriptive only. It neither implements the mask nor authorizes a new benchmark.
""")

    eq_rows = [[label, ", ".join(values) or "none", reason] for label, values, reason in [
        ("primary path intact", equivalent["nominal_primary_path_intact"], "no frozen nominal target-information path change"),
        ("primary path cut", equivalent["primary_path_cut"], "all remove at least one edge of the sole serial target-information route"),
        ("recovery reconfigured", equivalent["recovery_reconfigured"], "full node loss also enables a special direct recovery legality rule"),
    ]]
    write(out / "FAILURE_GRAPH_EQUIVALENCE_AUDIT.md", f"""# Failure-graph equivalence audit

{md_table(["Equivalence class", "Candidates", "Task-relevant interpretation"], eq_rows)}

At the primary target-information layer, names such as one-way Relay output loss, the corresponding compound loss, and full primary cut cannot create distinct ordinary training groups: each removes one edge of the only nominal serial route. Naming them separately would manufacture apparent variety without adding a recoverable topology class.
""")

    write(out / "TASK_RELEVANT_REACHABILITY_AUDIT.md", f"""# Task-relevant reachability audit

The frozen nominal legal target-information graph contains `{', '.join(f'{a}→{b}' for a, b in PRIMARY)}`. Its Scout→Attacker reachability is `True`, shortest legal path length is `2`, and the number of frozen primary paths is `1`.

A candidate that masks `Scout→Relay` or `Relay→Attacker` produces zero nominal legal primary paths. The other four physical one-way channels do not change this frozen primary reachability. Thus a simple policy-free severity based on primary-path loss is well-defined, but it has only two values here: `0` (no primary-path change) and `1` (complete cut). It cannot form a multi-level recoverable ladder.
""")

    write(out / "RECOVERABILITY_AND_DEGENERACY_AUDIT.md", """# Recoverability and degeneracy audit

- Candidates that leave `Scout→Relay→Attacker` intact are rejected as non-impacting under the frozen primary information semantics.
- Candidates that remove either serial primary edge are task cuts. They can be retained only as terminal stress references, not mixed with ordinary recoverable training groups.
- Full Relay-node loss is distinct only because the current environment activates a direct `Scout→Attacker` recovery legality rule. It is a policy-independent state transition, but not a pure edge-deletion mask; mixing it with ordinary fixed edge masks would conflate topology deletion with a change in route legality.

The current system therefore has no set of three or more non-degenerate, non-equivalent, recoverable failure classes under its existing information contract.
""")

    write(out / "TOPOLOGY_SEVERITY_FORMULATION.md", """# Topology-severity formulation

A policy-free structural quantity is possible for the primary graph:

`S_f = 1 - P(G_f) / P(G_0)`, where `P` is the count of frozen legal Scout→Attacker target-information paths.

Here `P(G_0)=1`. A primary-edge cut has `S_f=1`; an off-path channel failure has `S_f=0`. This is a valid structural diagnostic, but it is binary and does not create an exposure/training prior. Structural severity is not learning value, and no sampler prior is defined in P0.
""")

    write(out / "NO_LEAKAGE_AND_INFORMATION_BOUNDARY_AUDIT.md", """# No-leakage and information-boundary audit

Used: source-code semantics, roles, fixed legal paths, and deterministic fault-mask definitions.

Not used: trajectories, positions, communication realizations, dropout draws, policy actions, rewards, completed returns, training/evaluation/held-out tapes, checkpoints, seed performance, or historical method rankings.

A correct future mask must be an environment-side channel constraint and must be applied before message/cache propagation. The actor can observe only its resulting legal observations and graph, never a fault class label or an unmasked communication state.
""")

    write(out / "NEW_FAILURE_BENCHMARK_SPEC.md", """# New failure benchmark specification

**No new ordinary benchmark is emitted.** The candidate namespace `TD-*` remains an audit-only inventory because the current graph supports only a binary primary-path distinction plus a special recovery-reconfigured Relay-node condition.

Creating a genuine topology-distinct severity ladder would require an independently designed task graph with at least one additional legal, task-relevant recovery path (for example, another relay or an explicitly legal redundant channel). That is a new task/interface research design, not a relabeling of the old six conditions.
""")

    write(out / "OLD_VS_NEW_FAILURE_SEMANTICS.md", """# Old versus new failure semantics

The old F0/TE/TL/DS/DL/CP conditions remain frozen: each applies a timed full Relay-node failure and differs mainly by onset/duration. They are not modified or reinterpreted.

The proposed TD audit instead enumerates edge/node channel masks. It demonstrates why those masks cannot yet be promoted to a benchmark in the present three-UAV relay-dependent task: meaningful primary edge masks are all cuts, while non-cut masks lack a policy-free task impact. This is an independent negative benchmark-design result, not a revision of old experiments.
""")

    write(out / "FUTURE_EXPERIMENT_PLAN.md", """# Future experiment plan (not authorized)

If an independently designed task graph later supplies at least three recoverable topology-distinct classes, freeze the graph and masks first; then verify mask timing, actor legality, save/resume, and static structural equivalence before any training. Only after that may a separate study compare uniform exposure, Original DRTP, and external curriculum/robust baselines.

No future training, algorithm, sampler, or benchmark-interface change is authorized by this P0 audit.
""")

    write(out / "P0_FINAL_VERDICT.md", """# P0 final verdict

`TOPOLOGY_CLASSES_INSUFFICIENT`

The code admits deterministic, policy-independent communication-channel masks in principle, and a local channel-mask interface would not require altering the actor, reward, or old A-line benchmark. However, the frozen three-UAV relay-dependent task contains only one nominal legal target-information path: `Scout → Relay → Attacker`.

Consequently, all task-relevant single-edge failures cut that path and are terminal-stress equivalents; all other physical directed-edge failures leave it intact with no policy-free primary task impact. Full Relay-node loss is a separate recovery-reconfigured condition rather than a pure deletion mask. The required minimum of three non-degenerate, topology-distinct recoverable ordinary classes is not met.

P0 stops here. No new benchmark, training, rollout, evaluation, algorithm, or automatic next stage is authorized.
""")

    print(json.dumps(verdict, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
