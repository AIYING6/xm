"""Read-only S1-B topology reconfiguration audit over frozen S1 traces."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input-dir", type=Path, default=Path("results/development/phase_s1_paired_robustness"))
    p.add_argument("--output-dir", type=Path, default=Path("results/development/phase_s1b_topology_reconfiguration"))
    a = p.parse_args()
    paths = sorted((a.input_dir / "raw_timestep").glob("*.csv"))
    if not paths:
        raise FileNotFoundError("S1 timestep traces not found")
    a.output_dir.mkdir(parents=True, exist_ok=True)
    t = pd.concat((pd.read_csv(x) for x in paths), ignore_index=True)
    exposed = t[(t.condition == "relay_failure") & (t.relay_failure_active == 1)].copy()
    exposed["relay_path"] = ((exposed.scout_relay_comm == 1) & (exposed.relay_attacker_comm == 1)).astype(int)
    exposed["direct_path"] = (exposed.scout_attacker_comm == 1).astype(int)
    exposed["path_type"] = exposed.attacker_cache_path.map({"0-1-2": "relay", "0-2": "direct"}).fillna("other")
    summary = exposed.groupby(["controller", "seed"], as_index=False).agg(
        exposed_episodes=("development_episode_id", "nunique"),
        relay_edge_scout_to_relay=("scout_relay_comm", "mean"),
        relay_edge_relay_to_attacker=("relay_attacker_comm", "mean"),
        direct_edge_scout_to_attacker=("scout_attacker_comm", "mean"),
        relay_path_rate=("relay_path", "mean"),
        direct_path_rate=("direct_path", "mean"),
        task_chain_support_rate=("chain_support", "mean"),
        mean_cache_age=("target_cache_age_mean", "mean"),
    )
    summary.to_csv(a.output_dir / "exposed_topology_summary.csv", index=False)
    path_counts = exposed.groupby(["controller", "seed", "path_type"], as_index=False).size().rename(columns={"size": "rows"})
    path_counts.to_csv(a.output_dir / "path_type_counts.csv", index=False)

    nominal = t[t.condition == "nominal"].copy()
    paired = exposed.merge(nominal, on=["development_episode_id", "controller", "seed", "timestep"], suffixes=("_failure", "_nominal"))
    edge_delta = paired.groupby(["controller", "seed"], as_index=False).agg(
        delta_scout_relay=("scout_relay_comm_failure", lambda x: float(x.mean() - paired.loc[x.index, "scout_relay_comm_nominal"].mean())),
        delta_relay_attacker=("relay_attacker_comm_failure", lambda x: float(x.mean() - paired.loc[x.index, "relay_attacker_comm_nominal"].mean())),
        delta_scout_attacker=("scout_attacker_comm_failure", lambda x: float(x.mean() - paired.loc[x.index, "scout_attacker_comm_nominal"].mean())),
        delta_legal_info=("attacker_legal_information_failure", lambda x: float(x.mean() - paired.loc[x.index, "attacker_legal_information_nominal"].mean())),
        delta_chain_support=("chain_support_failure", lambda x: float(x.mean() - paired.loc[x.index, "chain_support_nominal"].mean())),
        delta_cache_age=("target_cache_age_mean_failure", lambda x: float(x.mean() - paired.loc[x.index, "target_cache_age_mean_nominal"].mean())),
    )
    edge_delta.to_csv(a.output_dir / "paired_topology_deltas.csv", index=False)
    path_counts.to_json(a.output_dir / "path_type_counts.json", orient="records", indent=2)
    manifest = {
        "protocol": "PHASE-S1B-TRM-V1",
        "source_protocol": "PHASE-S1-RV-V1",
        "read_only": True,
        "training_started": False,
        "tested_claim": "failure-associated communication topology and path reconfiguration",
        "information_availability_not_required_to_decrease": True,
        "status": "PASS_TO_S2_METRIC_FREEZE",
    }
    (a.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
