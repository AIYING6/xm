# B3 seed provenance audit

Status: `PASS — UNUSED_FOR_SCIENTIFIC_RESULTS`.

Exact seed-semantic searches covered the workspace source, configurations,
documentation, diagnostics, results, archives, artifact paths, manifests,
checkpoint names, command lines, and reachable Git history. Searches looked
for `seed2701` through `seed2703`, JSON seed values, and explicit `--seed`
arguments; numeric occurrences such as training update 2701 were excluded.

No candidate was found in scientific training, development, held-out/formal
work, evaluation, performance-driven debugging, technical smoke, or an
abandoned scientific run. Therefore seeds 2701, 2702, and 2703 are eligible
as new paired B3 development seeds. They are not canonical or held-out.
