"""Static P0.5 semantic-contract generator; it never imports or runs an environment."""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = ROOT / "configs" / "p0_5_semantic_contract_20260902.json"
OUT = ROOT / "docs" / "p0_5_semantic_contract_20260902"

S, R, T = range(2), range(2), range(2)
EDGES = tuple(("SR", s, r) for s in S for r in R) + tuple(("RT", r, t) for r in R for t in T)


def edge_name(e):
    return f"S{e[1] + 1}->R{e[2] + 1}" if e[0] == "SR" else f"R{e[1] + 1}->T{e[2] + 1}"


def permute(edge, ps, pr, pt):
    kind, a, b = edge
    return (kind, ps[a], pr[b]) if kind == "SR" else (kind, pr[a], pt[b])


PERMS = tuple(itertools.product(itertools.permutations(S), itertools.permutations(R), itertools.permutations(T)))


def canonical(mask):
    return min(tuple(sorted(permute(e, *p) for e in mask)) for p in PERMS)


def signature(mask):
    active = set(EDGES) - set(mask)
    paths = [(s, r, t) for s in S for r in R for t in T if ("SR", s, r) in active and ("RT", r, t) in active]
    per_pair = [[sum(1 for x in paths if x[0] == s and x[2] == t) for t in T] for s in S]
    reachable = sum(x > 0 for row in per_pair for x in row)
    terminal_coverage = sum(any(per_pair[s][t] > 0 for s in S) for t in T)
    scout_coverage = sum(any(per_pair[s][t] > 0 for t in T) for s in S)
    relay_disjoint = min((max(row) for row in per_pair), default=0)
    indeg_r = [sum(("SR", s, r) in active for s in S) for r in R]
    outdeg_r = [sum(("RT", r, t) in active for t in T) for r in R]
    return {"paths": len(paths), "reachable_pairs": reachable, "per_pair": per_pair,
            "relay_disjoint_max": relay_disjoint, "relay_in": indeg_r, "relay_out": outdeg_r,
            "terminal_coverage": terminal_coverage, "scout_coverage": scout_coverage,
            "any_legal_route": bool(paths)}


def enumerate_classes():
    classes = {}
    for n in (0, 1, 2):
        for mask in itertools.combinations(EDGES, n):
            key = canonical(mask)
            classes.setdefault(key, []).append(mask)
    records = []
    for i, (rep, members) in enumerate(sorted(classes.items(), key=lambda x: (len(x[0]), x[0])), 1):
        sig = signature(rep)
        # Two-edge masks are conservative Critical candidates even if a route remains.
        # R/C is finalized only after the separate physical-feasibility controller exists.
        tier = "I" if not sig["any_legal_route"] else ("R" if len(rep) <= 1 else "C")
        records.append({"id": f"E{i:02d}", "mask_type": "edge", "order": len(rep), "representative": "; ".join(map(edge_name, rep)) or "nominal",
                        "member_masks": len(members), "paths": sig["paths"], "reachable_pairs": sig["reachable_pairs"],
                        "per_pair": "/".join(map(str, sum(sig["per_pair"], []))),
                        "relay_disjoint": sig["relay_disjoint_max"], "terminal_coverage": sig["terminal_coverage"],
                        "scout_coverage": sig["scout_coverage"], "any_legal_route": sig["any_legal_route"], "tier_candidate": tier})
    node_masks = {
        "relay_node_R1": tuple(("SR", s, 0) for s in S) + tuple(("RT", 0, t) for t in T),
        "both_relays": EDGES,
        "all_upstream_cut": tuple(("SR", s, r) for s in S for r in R),
        "all_downstream_cut": tuple(("RT", r, t) for r in R for t in T),
    }
    for index, (label, mask) in enumerate(node_masks.items(), 1):
        sig = signature(mask)
        tier = "I" if not sig["any_legal_route"] else "C"
        records.append({"id": f"N{index:02d}", "mask_type": "node_or_cut", "order": len(mask), "representative": label,
                        "member_masks": 2 if label == "relay_node_R1" else 1, "paths": sig["paths"],
                        "reachable_pairs": sig["reachable_pairs"], "per_pair": "/".join(map(str, sum(sig["per_pair"], []))),
                        "relay_disjoint": sig["relay_disjoint_max"], "terminal_coverage": sig["terminal_coverage"],
                        "scout_coverage": sig["scout_coverage"], "any_legal_route": sig["any_legal_route"], "tier_candidate": tier})
    return records


def md(name, text):
    (OUT / name).write_bytes((text.strip() + "\n").encode("utf-8"))


def main():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)
    classes = enumerate_classes()
    with (OUT / "FAILURE_GRAPH_EQUIVALENCE_CLASSES.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(classes[0])); w.writeheader(); w.writerows(classes)
    path_rows = []
    for s, r, t in itertools.product(S, R, T):
        path_rows.append({"path_id": f"P{s+1}{r+1}{t+1}", "route": f"S{s+1}->R{r+1}->T{t+1}",
                          "scout_token": "yes", "relay_forward": "yes", "terminal_receive": "yes",
                          "freshness_gate": "age <= tau_max", "actor_usable": "yes: valid provenance feature", "mission_effect": "yes: enables one objective action"})
    with (OUT / "PATH_LEGALITY_MATRIX.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(path_rows[0])); w.writeheader(); w.writerows(path_rows)
    truth = [
        ["small", 4, "1/2/1", 1, 2, 4, "SxR + RxT", "team-normalized", "pair-normalized", "R/C/I from same rules", "config-derived"],
        ["main", 6, "2/2/2", 2, 8, 4, "SxR + RxT", "team-normalized", "pair-normalized", "R/C/I from same rules", "config-derived"],
        ["large", 8, "2/3/3", 3, 18, 6, "SxR + RxT", "team-normalized", "pair-normalized", "R/C/I from same rules", "config-derived"],
    ]
    with (OUT / "SEMANTIC_TRUTH_TABLE.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["scale", "N", "S/R/T", "objectives", "legal_routes", "legal_edges", "support_graph", "reward", "collision", "failure_tiers", "dimensions"]); w.writerows(truth)

    md("P0_5_SEMANTIC_FREEZE_CONTRACT.md", """
# P0.5 new-environment semantic freeze

**Authorization:** `P0_5_NEW_ENVIRONMENT_SEMANTIC_CONTRACT_FREEZE`  
**Verdict:** `SEMANTIC_CONTRACT_READY`  
**Next step:** not authorized.

This contract defines a new, isolated `redundant_topology_uav` benchmark family. It does not import, patch or execute the legacy 3-UAV environment. No policy, rollout, evaluation, seed, PPO parameter or candidate algorithm was created.

The family has one configuration rule: role counts determine the number of mission objectives, bipartite task-support edges, objective capacity, observation/critic dimensions, reward normalization, collision exposure denominator and failure enumeration. No `if N == 6` task rule is permitted.
""")
    md("ROLE_CAPABILITY_CONTRACT.md", """
# Role capability contract

| Role | CAN | CANNOT | observation / communication | success and failure meaning |
|---|---|---|---|---|
| Scout | acquire one objective token per decision interval; sense and timestamp target estimate; transmit to a legal relay | terminal action; invent target truth | local flight state plus its sensed objective; emits provenance-tagged token | loss reduces parallel sensing capacity; surviving Scout can cover outstanding objectives sequentially |
| Relay | receive, cache, deduplicate and forward valid Scout-originated tokens | sense target ground truth; terminal action | local flight/radio/cache state; forwards only legal fresh tokens | loss reduces routing capacity/redundancy; no bypass is opened |
| Terminal | receive fresh valid relay-forwarded token; execute one assigned/unassigned objective action per interval | scout-level remote observation; fabricate valid support | local flight state plus valid token age/provenance | loss reduces parallel execution capacity; survivor may complete remaining objective if deadline margin permits |

Instances within a role are exchangeable: no agent-ID ability, observation feature or reward bonus exists. Their real value is finite per-interval capacity: multiple Scouts can acquire multiple objectives, Relays provide independent forwarding branches, and Terminals complete multiple objectives in parallel or sequentially after failure.
""")
    md("MISSION_OBJECTIVE_CONTRACT.md", """
# Mission-objective contract

At a scale with `K = n_terminal` objectives, each objective has a spatially distinct target state and progress `p_k in [0,1]`. A Scout can acquire at most one fresh objective token per interval; a Terminal can advance at most one objective per interval. Any Scout may acquire any objective and any Terminal may execute any outstanding objective, provided it holds fresh, legal relay-forwarded support. This is workload redundancy rather than hidden specialization.

Mission success requires completion of all K objectives before the fixed physical deadline with valid support at each terminal completion. The deadline is selected by future scripted physical-feasibility tests, not learner score. Small/main/large therefore have 1/2/3 objectives respectively; this is the same capacity rule, not three hand-written tasks.
""")
    md("LEGAL_TASK_SUPPORT_GRAPH_CONTRACT.md", """
# Legal task-support graph contract

`G_task_0` is directed and layered: every Scout-to-Relay and every Relay-to-Terminal edge is legal; Scout-to-Terminal edges are illegal. For 2S+2R+2T, all eight `S_i -> R_j -> T_k` paths are legal. Each appears in `PATH_LEGALITY_MATRIX.csv` and has the same token-generation, relay, freshness, actor and mission-action semantics.

An actor can use a route only through a received message with source, route, age and validity fields. The graph is therefore task-active: without a fresh legal route, a terminal cannot claim supported completion. There is no direct Scout-to-Terminal recovery exception.
""")
    md("MESSAGE_PROVENANCE_AND_FRESHNESS_CONTRACT.md", """
# Message provenance and freshness contract

`m = (objective_id, target_estimate, source_scout, t_sense, relay_route, t_receive, age, validity)`, where `age = t_now - t_sense`. A terminal may use support iff `valid == true`, `age <= tau_max`, source/relay fields match an active legal route, and the objective remains outstanding.

Failed-edge packets are not created. Cache updates reject packets whose legal edge is masked. Repeated forwarding preserves earliest sensing time and route history; duplicates are deterministically deduplicated by `(objective_id, source_scout, t_sense)`. A route switch changes provenance but never makes stale support fresh. `tau_max` is a physical parameter to freeze from scripted feasibility geometry before P1, not a performance-tuned learner knob.
""")
    md("STATIC_FAULT_RADIO_GRAPH_SEPARATION.md", """
# Static fault, legal-task and radio graph separation

`G_task_0` is the static directed legal support graph. A deterministic structural mask creates `G_task_f = G_task_0 ⊙ M_f`. `G_radio_t` contains only distance/LOS/dropout/radio availability. Active communication is `G_active_t,f = G_task_f ⊙ G_radio_t`.

The fault mask is applied before packet creation, cache update and graph-message construction. A dynamic radio outage cannot be relabeled as a structural fault; conversely, a structurally masked edge cannot leave cached/new messages available merely because radio connectivity is good.
""")
    md("FAILURE_FAMILY_ENUMERATION.md", """
# Failure-family enumeration

Primary labels are structural; onset and duration are separate factors. Candidate main-scale families are: F1 upstream single edge; F2 downstream single edge; F3 relay-node loss; F4 balanced diagonal upstream compound; F5 cross-layer compound; F6 same-relay mixed compound. The static quotient enumerates every zero-, one- and two-edge mask under independent Scout/Relay/Terminal permutations and adds canonical relay-node and cut-set masks in `FAILURE_GRAPH_EQUIVALENCE_CLASSES.csv`.

Node loss is represented as its deterministic incident-edge mask and is classified separately only when the role-resource loss changes physical feasibility. Both-relay loss, all upstream cut and all downstream cut are Tier-I candidates. Every two-edge quotient class is conservatively a **Tier-C candidate** until the scripted controller establishes capacity and deadline margin; it is not promoted merely because a graph route survives. The final R/C/I label additionally requires future scripted physical feasibility; P0.5 does not claim it has run that test.
""")
    md("RECOVERABILITY_CONTRACT.md", """
# Recoverability contract

`Recoverable = structural feasibility AND physical feasibility`.

Structural feasibility requires at least one legal residual Scout-to-Relay-to-Terminal support route together with remaining role capacity that could serve all outstanding objectives by reassignment. Whether a surviving terminal can complete several objectives sequentially is **not** inferred from reachability alone: it is decided by the future deterministic physical-feasibility controller under the frozen deadline. Tier R has meaningful alternate capacity/margin; Tier C remains a candidate with one effective branch or tight time/capacity margin; Tier I has no legal route or insufficient required role resource. Tier I is a lower-bound reference, not an ordinary robustness-mean condition.
""")
    md("R_C_I_CLASSIFICATION_RULES.md", """
# R/C/I rules

| Tier | deterministic structural rule | future physical rule |
|---|---|---|
| R | each required objective can be assigned a terminal with at least two or dynamically substitutable legal support options/capacity margin | scripted controller completes under pre-frozen geometry |
| C | all objectives remain structurally supportable but a relay branch, role capacity or deadline margin is singular/tight | scripted controller completes only within reduced margin |
| I | all legal routes for a required assignment cut, both relays unavailable, all ingress/egress cut, or no terminal resource | no legal scripted success trajectory may be asserted |
""")
    md("SCRIPTED_FEASIBILITY_TEST_PLAN.md", """
# Scripted feasibility test plan (future only)

Implement no learner. For each canonical R/C/I mask and pre-hashed geometry, a deterministic controller will assign outstanding objectives, select a shortest valid active support route, respect token freshness, and issue bounded pursuit/terminal actions. Log route availability, token age, objective completion and deadline margin. Pass conditions: all R examples complete; C examples demonstrate reduced but nonzero margin; I examples fail only through the frozen legal/physical criterion. This plan must pass before RL is attached.
""")
    md("TOPOLOGY_SIGNATURE_SPEC.md", """
# Topology signature specification

For every mask compute directed edge set; role-labelled in/out degrees; SCCs; source-terminal reachable-pair count; total legal paths; paths per S--T pair; edge-/relay-node-disjoint routes; shortest legal path; cut edges/nodes; minimal task cut; residual redundancy. Signatures are descriptive only. No scalar severity score and no severity-to-sampling rule is permitted.
""")
    md("REWARD_SEMANTIC_CONTRACT.md", """
# Reward semantic contract

With K objectives, `p_bar(t) = (1/K) sum_k p_k(t)`, `r_progress = p_bar(t+1)-p_bar(t)`, and `r_complete = newly_completed/K`. The frozen skeleton is `r = w_p*r_progress + w_s*r_complete - w_c*C_pair - w_b*boundary_cost`. Weights are physical design constants to be justified by units/ranges before P1 and may not be tuned from RL performance.

The default is a shared team reward. If role shaping becomes necessary, it is averaged within each role before addition. No direct reward is granted for topology redundancy, number of paths or severity.
""")
    md("REWARD_SCALE_INVARIANCE_PROOF.md", """
# Reward scale-invariance proof

`p_bar`, `newly_completed/K`, role averages and `C_pair` are all bounded in `[0,1]` irrespective of N or K. Hence duplicating objectives/agents cannot multiply their aggregate reward magnitude. A scale may alter task duration or geometry, but it cannot alter the numerical meaning of one unit of normalized progress, completion, collision exposure or boundary cost. Physical deadline comparability is separately frozen in the scenario configuration.
""")
    md("SAFETY_AND_METRIC_CONTRACT.md", """
# Safety and metric contract

At N UAVs, `C_t = sum_{i<j} 1[d_ij < d_safe] / choose(N,2)` and `C_pair = mean_t C_t`; also report `C_any`, the episode any-collision indicator. Timeout is an unmet all-objective deadline under the scale's frozen physical time budget. Task-path availability is the fraction of Scout--Terminal pairs with a fresh legal route; residual redundancy is current route count divided by nominal route count, averaged over pairs. All-pairs radio closure is never the main communication metric.
""")
    md("RECOVERY_METRIC_CONTRACT.md", """
# Recovery metric contract

At failure time `t_f`, record `L_route = t_alternate_path_active - t_f`, `L_message = t_fresh_alternate_support_arrives - t_f`, and `L_task = t_first_post_failure_progress - t_f`. Also retain path switch, rerouting decision, token arrival, cache invalidation and objective recovery events. Undefined latency is recorded as censored/unrecovered, not silently dropped.
""")
    md("SCALE_GENERATOR_SEMANTIC_SPEC.md", """
# Scale-generator semantic specification

Input configuration supplies role counts, objective count (= terminal count), layered edge templates, capacity per role, physical geometry templates, deadline rule, action schema, safety radius, freshness parameter, static-failure registry and telemetry cadence. Derived fields include all dimensions, legal paths, normalizers, canonical failure masks and manifests. A generator validation rejects non-layered edges, bypass edges, inconsistent counts and hand-coded per-scale logic.
""")
    md("ROLE_PERMUTATION_AUDIT_SPEC.md", """
# Role-permutation audit specification

Before learner training, test each within-role swap (S1/S2, R1/R2, T1/T2) while simultaneously permuting state rows, legal edges, objective assignments, message provenance and action indices. Actor outputs must permute correspondingly; critic value must be invariant to the matching global permutation. This detects hidden array-index capabilities. Parameter sharing is within role only.
""")
    md("SG_MAPPO_NEW_ENVIRONMENT_INTERFACE.md", """
# SG-MAPPO new-environment interface

Preserve graph-attention CTDE: configuration-derived node count, role inventory/embedding, per-role sharing, observation dimensions, shared critic dimensions, action validity and generalized failure sampler. Train 4/6/8 separately; mixed-scale vectorized batches are explicitly out of scope. Add provenance/age/validity as legal received-message features, not actor-side failure IDs. No new GNN, transformer, critic family or action hack is approved.
""")
    md("EXTERNAL_COMPARATOR_INTERFACE_CONTRACT.md", """
# External comparator interface contract

Main future families are Plain SG-MAPPO, UTR, original DRTP-style adaptive exposure, PLR-style prioritized curriculum, EPOpt-style CVaR robust training, and at most one evidence-nominated candidate. All share backbone, training support, total environment steps, actor information, evaluation tape and checkpoint policy.

PLR level is `(failure structure, timing, duration, geometry member)` and reads training-only learning signals. EPOpt-style MAPPO selects/weights trajectory groups by training-return lower tail from that same source; its epsilon, unit of selection, update schedule and data accounting must be frozen in an implementation audit. Group-DRO remains optional, not a claimed drop-in.
""")
    md("STRUCTURAL_OOD_FREEZE_CONTRACT.md", """
# Structural OOD freeze contract

Hash TRAIN, DEV, HELD-OUT and STRUCTURAL-OOD memberships, geometry, onset, duration and evaluation seeds before learner training. Held-out contains unseen members within a structural equivalence family. Structural OOD withholds an entire family, such as cross-layer compounds, higher-order compounds, node+edge compositions, unseen redundancy signatures or 6-to-8 transfer. Role-permutation variants alone are never OOD.
""")
    md("OOD_EQUIVALENCE_AUDIT.md", """
# OOD equivalence audit

Each proposed OOD condition is first quotient-tested under role-preserving isomorphism and task signature. It is OOD only if no TRAIN canonical class has the same signature and semantic consequence. The registry stores its nearest training signature to make any generalization claim falsifiable.
""")
    md("TELEMETRY_RETENTION_CONTRACT.md", """
# Telemetry retention contract

Tier 1 permanently stores episode/update summaries, outcomes, failure ID, sampling probability, PPO statistics and topology summary. Tier 2 permanently stores fixed high-frequency windows around failure/path loss/switch/fresh support/recovery. Tier 3 stores full step trajectories only for a pre-hashed diagnostic registry, never selected after observing results. Every artifact has schema, manifest, compression and checksum.
""")
    md("STORAGE_AND_SERIALIZATION_PLAN.md", """
# Storage and serialization plan

The existing 50 GB disk is scratch only. Reserve 0.5--1 TB durable object storage provisionally for the full programme. Before P1, a serialization-byte audit on the finalized schema must measure summary, event window, diagnostic full trajectory and checkpoint bytes; then freeze cadence, compression, retention, archival and checksum policy. If durable storage is unavailable, verdict becomes `RESOURCE_PLAN_NOT_READY` and no key telemetry may be discarded to proceed.
""")
    md("P0_5_GO_NO_GO_CHECKLIST.md", """
# P0.5 GO/NO-GO checklist

- [x] role value comes from finite workload capacity, not hidden IDs
- [x] all 8 main-scale routes have legal common semantics
- [x] no direct bypass exception
- [x] task/fault/radio graphs are separate and mask ordering is explicit
- [x] low-order mask quotient produced; >=3 recoverable candidate families exist
- [x] R/C/I double definition and scripted-test plan are frozen
- [x] reward, safety, recovery and scale normalizers are defined
- [x] one configuration generator defines 4/6/8 semantics
- [x] SG-MAPPO change is limited to necessary generalization
- [x] PLR/EPOpt fairness interfaces and structural OOD contract exist
- [x] telemetry and storage plan exist
- [x] legacy A-line is untouched

The final implementation prerequisite is to operationalize the scripted feasibility and serialization-byte audits; neither audit has been executed in P0.5.
""")
    md("P0_5_FINAL_VERDICT.md", """
# P0.5 final verdict

## `SEMANTIC_CONTRACT_READY`

The 2S+2R+2T main design now has homogeneous within-role agents with non-duplicative workload capacity, two objectives, eight task-legal routes, no recovery bypass, structural/radio separation, normalized reward and safety semantics, a low-order equivalence quotient, and a unified 4/6/8 generator contract.

READY means the scientific semantic contract is adequate to *request* isolated P1 environment implementation. It does **not** authorize implementation, scripted scenarios, learner training, rollouts, evaluation, cloud jobs or an algorithm choice. Storage remains a resource gate that must be measured before formal experiments.
""")
    payload = {
        "protocol": cfg["protocol"], "authorization": cfg["authorization"], "namespace": cfg["namespace"],
        "main_scale": cfg["main_scale"], "scale_family": cfg["scale_family"],
        "mission_objectives": {"rule": "K equals terminal count", "capacity": "one objective per Scout/Terminal per interval"},
        "legal_paths": {"main_count": 8, "direct_bypass": False, "freshness": "age <= tau_max"},
        "message_contract": {"provenance": True, "failure_mask_before_packet": True},
        "failure_families": ["upstream_edge", "downstream_edge", "relay_node", "balanced_upstream_compound", "cross_layer_compound", "same_relay_mixed"],
        "equivalence_classes": classes, "recoverability_tiers": {"R": "structural+physical feasible", "C": "feasible with tight margin", "I": "no legal or physical success"},
        "reward_formula": "wp*progress + ws*completion - wc*pair_collision - wb*boundary", "safety_metrics": ["C_pair", "C_any", "timeout"],
        "recovery_metrics": ["L_route", "L_message", "L_task"], "ood_partitions": ["TRAIN", "DEV", "HELD_OUT", "STRUCTURAL_OOD"],
        "comparators": ["Plain SG-MAPPO", "UTR", "Original DRTP-style", "PLR-style", "EPOpt-style"],
        "telemetry": {"tiers": ["summary", "event_window", "prehashed_full_trajectory"]},
        "storage": {"durable_requirement": "0.5-1 TB provisional", "measurement_required": "serialization-byte audit"},
        "hard_gate_results": {"six_uav_task_justified": True, "all_paths_semantic": True, "unified_generator": True, "legacy_unchanged": True, "training_started": False},
        "verdict": cfg["final_verdict"], "next_step_authorized": False,
        "config_sha256": hashlib.sha256(CFG.read_bytes()).hexdigest()
    }
    (OUT / "P0_5_SEMANTIC_CONTRACT.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
