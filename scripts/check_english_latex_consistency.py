from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper_latex_en"


REQUIRED_FILES = [
    "main.tex",
    "sections/01_introduction.tex",
    "sections/02_related_work.tex",
    "sections/03_problem.tex",
    "sections/04_method.tex",
    "sections/05_experiments.tex",
    "sections/06_discussion.tex",
    "sections/07_conclusion.tex",
    "sections/08_appendix_experiments.tex",
]


REQUIRED_MARKERS = [
    "EA-RG-MAPPO-S",
    "Edge-Aware Role Graph",
    "staged random-radius fine-tuning",
    "balanced accuracy",
    "not used as a main contribution",
    "not be treated as a full air-combat system",
    "new experimental validation",
]


REQUIRED_RESULT_MARKERS = [
    "0.926",
    "0.919",
    "0.890",
    "0.879",
    "0.054",
    "0.086",
    "300 evaluation episodes per seed",
    "100 episodes per seed",
    "50-episode-per-seed diagnostic",
    "30-episode diagnostic",
]


REQUIRED_INPUTS = [
    "../results/latex_training_settings_table",
    "../results/latex_final_comm_300_table",
    "../results/latex_final_300_paired_ci_table",
    "../results/latex_comm_dropout_robustness_table",
    "../results/latex_comm_dropout_paired_ci_table",
    "../results/latex_aggregate_robustness_table",
    "../results/latex_radius_interpolation_table",
    "../results/latex_ablation_comm_table",
    "../results/latex_speed_robustness_table",
    "../results/latex_edge_feature_ablation_table",
]


REQUIRED_GRAPHICS = [
    "method_overview_ea_rg_mappo_s.png",
    "final_300_success_rate.png",
    "final_300_collision_rate.png",
    "speed_robustness_success_r4.png",
    "speed_robustness_collision_r4.png",
    "speed_robustness_success_r8.png",
    "speed_robustness_collision_r8.png",
    "comm_dropout_success_rate.png",
    "comm_dropout_collision_rate.png",
    "radius_interpolation_success_rate.png",
    "radius_interpolation_collision_rate.png",
    "edge_feature_ablation_delta.png",
]


def main() -> None:
    errors = []
    texts = []
    for rel in REQUIRED_FILES:
        path = PAPER / rel
        if not path.exists():
            errors.append(f"missing english latex file: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip():
            errors.append(f"empty english latex file: {rel}")
        texts.append(text)

    full_text = "\n".join(texts)
    for marker in REQUIRED_MARKERS:
        if marker not in full_text:
            errors.append(f"missing required marker: {marker}")
    for marker in REQUIRED_RESULT_MARKERS:
        if marker not in full_text:
            errors.append(f"missing required result marker: {marker}")
    for ref in REQUIRED_INPUTS:
        if f"\\input{{{ref}}}" not in full_text:
            errors.append(f"missing required table input: {ref}")
    for graphic in REQUIRED_GRAPHICS:
        if graphic not in full_text:
            errors.append(f"missing required graphic: {graphic}")

    print(f"english latex files checked: {len(REQUIRED_FILES)}")
    print(f"required markers checked: {len(REQUIRED_MARKERS) + len(REQUIRED_RESULT_MARKERS)}")
    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
