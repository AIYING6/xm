from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper_latex"
MAIN = PAPER / "main.tex"
PROJECTS = [
    (ROOT / "paper_latex", ROOT / "paper_latex" / "references.bib"),
    (ROOT / "paper_latex_en", ROOT / "paper_latex" / "references.bib"),
    (ROOT / "paper_latex_3d_en", ROOT / "paper_latex_3d_en" / "references.bib"),
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collect_tex_files(project: Path) -> list[Path]:
    files = [project / "main.tex"]
    sections = project / "sections"
    files.extend(sorted(sections.glob("*.tex")))
    return files


def resolve_input(project: Path, base_path: Path, ref: str) -> Path | None:
    candidates = []
    raw = Path(ref)
    if base_path == project / "main.tex":
        candidates.append(project / f"{ref}.tex")
    candidates.extend(
        [
            (base_path.parent / raw).with_suffix(".tex"),
            (project / raw).with_suffix(".tex"),
            (ROOT / raw).with_suffix(".tex"),
        ]
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return None


def collect_referenced_tex_files(project: Path, initial_files: list[Path]) -> list[Path]:
    seen = {path.resolve() for path in initial_files}
    queue = [path.resolve() for path in initial_files]
    while queue:
        path = queue.pop(0)
        text = read(path)
        for ref in re.findall(r"\\input\{([^}]+)\}", text):
            candidate = resolve_input(project, path, ref)
            if candidate is not None and candidate not in seen:
                seen.add(candidate)
                queue.append(candidate)
    return sorted(seen)


def parse_bib_keys(path: Path) -> set[str]:
    text = read(path)
    return set(re.findall(r"@\w+\s*\{\s*([^,\s]+)", text))


def check_inputs(project: Path, main_text: str) -> list[str]:
    errors = []
    for ref in re.findall(r"\\input\{([^}]+)\}", main_text):
        candidate = resolve_input(project, project / "main.tex", ref)
        if candidate is None:
            errors.append(f"{project.relative_to(ROOT)} missing input: {project / f'{ref}.tex'}")
    return errors


def check_graphics(project: Path, tex_texts: list[tuple[Path, str]]) -> list[str]:
    errors = []
    graphic_paths = [project, ROOT / "results" / "figures"]
    for path, text in tex_texts:
        for graphic in re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", text):
            candidates = []
            raw = Path(graphic)
            if raw.suffix:
                candidates = [base / raw for base in graphic_paths]
            else:
                for suffix in [".pdf", ".png", ".jpg", ".jpeg"]:
                    candidates.extend(base / f"{graphic}{suffix}" for base in graphic_paths)
            if not any(candidate.exists() for candidate in candidates):
                errors.append(f"{path.relative_to(ROOT)} missing graphic: {graphic}")
    return errors


def check_nested_inputs(project: Path, tex_texts: list[tuple[Path, str]]) -> list[str]:
    errors = []
    main = project / "main.tex"
    for path, text in tex_texts:
        for ref in re.findall(r"\\input\{([^}]+)\}", text):
            if path == main.resolve():
                continue
            if resolve_input(project, path, ref) is None:
                errors.append(f"{path.relative_to(ROOT)} missing nested input: {ref}")
    return errors


def check_citations(tex_texts: list[tuple[Path, str]], bib_keys: set[str]) -> list[str]:
    errors = []
    cited = set()
    for _, text in tex_texts:
        for cite_cmd in re.findall(r"\\cite\{([^}]+)\}", text):
            cited.update(key.strip() for key in cite_cmd.split(",") if key.strip())
    missing = sorted(cited - bib_keys)
    if missing:
        errors.append("missing bib keys: " + ", ".join(missing))
    unused = sorted(bib_keys - cited)
    if unused:
        errors.append("unused bib keys: " + ", ".join(unused))
    return errors


def check_labels(tex_texts: list[tuple[Path, str]]) -> list[str]:
    errors = []
    labels = []
    refs = []
    for _, text in tex_texts:
        labels.extend(re.findall(r"\\label\{([^}]+)\}", text))
        refs.extend(re.findall(r"\\(?:ref|eqref)\{([^}]+)\}", text))
    dupes = sorted({label for label in labels if labels.count(label) > 1})
    if dupes:
        errors.append("duplicate labels: " + ", ".join(dupes))
    missing_refs = sorted(set(refs) - set(labels))
    if missing_refs:
        errors.append("missing labels for refs: " + ", ".join(missing_refs))
    return errors


def check_project(project: Path, bib_path: Path) -> tuple[int, int, list[str]]:
    main_path = project / "main.tex"
    if not main_path.exists():
        return 0, 0, [f"missing main: {main_path.relative_to(ROOT)}"]
    tex_files = collect_tex_files(project)
    tex_files = collect_referenced_tex_files(project, tex_files)
    tex_texts = [(path, read(path)) for path in tex_files]
    main_text = read(main_path)
    bib_keys = parse_bib_keys(bib_path)

    errors = []
    errors.extend(check_inputs(project, main_text))
    errors.extend(check_nested_inputs(project, tex_texts))
    errors.extend(check_graphics(project, tex_texts))
    errors.extend(check_citations(tex_texts, bib_keys))
    errors.extend(check_labels(tex_texts))
    return len(tex_files), len(bib_keys), errors


def main() -> None:
    errors = []
    total_tex_files = 0
    bib_key_counts = []
    for project, bib_path in PROJECTS:
        tex_count, bib_count, project_errors = check_project(project, bib_path)
        total_tex_files += tex_count
        bib_key_counts.append(bib_count)
        errors.extend(project_errors)

    print(f"checked tex files: {total_tex_files}")
    print("bib keys:", ", ".join(str(count) for count in bib_key_counts))
    if errors:
        print("FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)
    print("OK")


if __name__ == "__main__":
    main()
