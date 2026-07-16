from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


PUBLISHABLE_FILES = [
    "paper_latex/main.tex",
    "paper_latex/sections/01_introduction.tex",
    "paper_latex/sections/02_related_work.tex",
    "paper_latex/sections/03_problem.tex",
    "paper_latex/sections/04_method.tex",
    "paper_latex/sections/05_experiments.tex",
    "paper_latex/sections/06_discussion.tex",
    "paper_latex/sections/07_conclusion.tex",
    "paper_latex/sections/08_appendix_experiments.tex",
    "paper_latex_en/main.tex",
    "paper_latex_en/sections/01_introduction.tex",
    "paper_latex_en/sections/02_related_work.tex",
    "paper_latex_en/sections/03_problem.tex",
    "paper_latex_en/sections/04_method.tex",
    "paper_latex_en/sections/05_experiments.tex",
    "paper_latex_en/sections/06_discussion.tex",
    "paper_latex_en/sections/07_conclusion.tex",
    "paper_latex_en/sections/08_appendix_experiments.tex",
    "docs/paper_manuscript_zh_v1.md",
    "docs/english_abstract_and_contributions.md",
    "docs/english_introduction_draft.md",
    "docs/english_related_work_draft.md",
    "docs/english_problem_method_draft.md",
    "docs/english_experiments_draft.md",
    "docs/english_discussion_conclusion_draft.md",
    "docs/english_manuscript_draft.md",
]

WORKFLOW_DOCS = [
    "docs/current_progress_and_next_plan.md",
    "docs/evidence_chain_status.md",
    "docs/paper_asset_index.md",
    "docs/reproducibility_manifest.md",
]


NEGATION_MARKERS = [
    "不",
    "不能",
    "不应",
    "不要",
    "尚未",
    "未",
    "不足",
    "不等同",
    "不直接",
    "不将",
    "不依赖",
    "不能作为",
    "不能冒充",
    "not",
    "Not",
    "Do not",
    "cannot",
]


OLD_ROUTE_BANNED = [
    "RI-GMAPPO 还未实现",
    "目标意图预测模块是下一步核心",
    "目标意图感知的角色图多智能体强化学习框架",
]


OVERCLAIM_PATTERNS = [
    "全面超过",
    "全面最优",
    "所有指标上全面",
    "已验证完整 6DOF",
    "已验证完整空战",
    "实现了高精度目标意图",
    "高精度目标意图识别模块",
    "证明 intent head 不是摆设",
    "verified full 6DOF",
    "full 6DOF air combat has been verified",
    "high-accuracy target intent recognition",
    "outperforms all baselines on all metrics",
]


REQUIRED_PUBLISHABLE_MARKERS = [
    "EA-RG-MAPPO-S",
    "balanced accuracy",
]


def read_lines(rel: str) -> list[str]:
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


def has_negation_context(line: str) -> bool:
    return any(marker in line for marker in NEGATION_MARKERS)


def check_publishable_text() -> list[str]:
    errors = []
    combined_text = []
    for rel in PUBLISHABLE_FILES:
        text = "\n".join(read_lines(rel))
        combined_text.append(text)

        for lineno, line in enumerate(text.splitlines(), start=1):
            for phrase in OLD_ROUTE_BANNED:
                if phrase in line:
                    errors.append(f"{rel}:{lineno}: stale route phrase `{phrase}`")
            for phrase in OVERCLAIM_PATTERNS:
                if phrase in line and not has_negation_context(line):
                    errors.append(f"{rel}:{lineno}: overclaim without boundary marker `{phrase}`")
    full_text = "\n".join(combined_text)
    for marker in REQUIRED_PUBLISHABLE_MARKERS:
        if marker not in full_text:
            errors.append(f"publishable text: missing required marker `{marker}`")
    return errors


def check_workflow_boundary_docs() -> list[str]:
    errors = []
    for rel in WORKFLOW_DOCS:
        text = "\n".join(read_lines(rel))
        for phrase in OLD_ROUTE_BANNED:
            if phrase in text:
                errors.append(f"{rel}: stale route phrase remains `{phrase}`")

    # These documents are expected to preserve explicit claim boundaries.
    evidence = "\n".join(read_lines("docs/evidence_chain_status.md"))
    for required in [
        "不应主张",
        "高精度目标意图识别",
        "完整 6DOF",
        "自动一致性检查",
    ]:
        if required not in evidence:
            errors.append(f"docs/evidence_chain_status.md: missing claim-boundary marker `{required}`")
    return errors


def main() -> None:
    errors = []
    errors.extend(check_publishable_text())
    errors.extend(check_workflow_boundary_docs())

    print("text risk files checked:", len(PUBLISHABLE_FILES) + len(WORKFLOW_DOCS))
    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
