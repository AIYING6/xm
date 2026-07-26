from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = ROOT / "configs" / "paper"
REQUIRED = {
    "main_gate1.yaml",
    "mappo.yaml",
    "single_graph.yaml",
    "ea_rg_mappo.yaml",
    "param_matched_single.yaml",
    "happo.yaml",
    "ippo.yaml",
    "ablation_no_role_pair.yaml",
    "ablation_no_task_support.yaml",
    "ablation_no_role_identity.yaml",
    "checkpoint_selection_schema.yaml",
}
GRAPH_METHOD_CONFIGS = {
    "mappo.yaml",
    "single_graph.yaml",
    "ea_rg_mappo.yaml",
    "param_matched_single.yaml",
    "ablation_no_role_pair.yaml",
    "ablation_no_task_support.yaml",
    "ablation_no_role_identity.yaml",
}


def main() -> None:
    missing = sorted(name for name in REQUIRED if not (CONFIG_DIR / name).exists())
    if missing:
        raise SystemExit(f"missing paper config(s): {', '.join(missing)}")

    loaded = {}
    for path in sorted(CONFIG_DIR.glob("*.yaml")):
        try:
            loaded[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"invalid JSON-compatible YAML in {path}: {exc}") from exc

    main_cfg = loaded["main_gate1.yaml"]
    budget = main_cfg["training_budget"]
    rollout = main_cfg["rollout"]
    computed = rollout["num_envs"] * rollout["rollout_steps"] * rollout["updates_for_1m_steps"]
    if budget["unit"] != "environment_steps":
        raise SystemExit("main_gate1 training budget must use environment_steps")
    if computed < 1_000_000:
        raise SystemExit(f"updates_for_1m_steps under-runs 1M environment steps: {computed}")

    required_methods = {"MAPPO", "Single-Graph GAT-MAPPO", "EA-RG-MAPPO", "HAPPO-style"}
    present_methods = {cfg.get("method") for cfg in loaded.values()}
    missing_methods = sorted(required_methods - present_methods)
    if missing_methods:
        raise SystemExit(f"missing required method config(s): {', '.join(missing_methods)}")

    for name in GRAPH_METHOD_CONFIGS:
        cfg = loaded[name]
        for key in ("graph_encoder", "graph_relation_ablation", "graph_message_ablation", "graph_input_ablation"):
            if key not in cfg:
                raise SystemExit(f"{name} missing required graph key: {key}")
    schema = loaded["checkpoint_selection_schema.yaml"]
    if schema.get("selection_policy", {}).get("test_must_use_selection_csv") is not True:
        raise SystemExit("checkpoint selection schema must require test split to use validation selection CSV")

    print(f"paper config audit passed: {len(loaded)} configs")
    print(f"1M-step update approximation: {computed} environment steps")


if __name__ == "__main__":
    main()
