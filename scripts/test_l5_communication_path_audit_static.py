"""Static guardrails for the L5 relay-path audit implementation."""
from __future__ import annotations

import ast
from pathlib import Path


SOURCE = Path(__file__).with_name("audit_l5_communication_path_identifiability.py")


def main() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    names = {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert {"_run_reference", "_verify_physical_replay", "_summarize", "main"} <= names
    text = SOURCE.read_text(encoding="utf-8")
    assert "train_ri_gmappo" not in text
    assert "provenance_erasure_changes_legal_information" in text
    assert "physical_dynamics_invariant_when_relay_communication_disabled" in text
    print("L5_COMMUNICATION_PATH_AUDIT_STATIC_TEST: PASS (no training; provenance and fixed-action replay present)")


if __name__ == "__main__":
    main()
