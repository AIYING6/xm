# PVF-EGTR three-stage research protocol

The workflow is intentionally compressed to three scientific stages. Technical smoke tests remain implementation checks, not additional scientific “levels.”

## Stage 1 — Development

Use the already completed ten matched 10M UTR/EGTR pairs. Generate two fresh, disjoint selector tapes (`730000–730099` and `731000–731099`) and apply the frozen selector. The already observed `720000–720099` evaluation is used only as a development outcome label.

This stage asks whether the selector has any practical discrimination at all:

- harmful EGTR checkpoints should mostly fall back to UTR;
- beneficial EGTR checkpoints should be promoted often enough to retain meaningful upside;
- no threshold or method parameter may be changed after results are read.

Because the candidate was conceived after the 10M outcomes were known, Stage 1 is retrospective development evidence only. It cannot confirm the method.

Hard stop: if the selector has material false promotions, selects almost no useful EGTR checkpoints, or produces no positive deployed development gain, close PVF-EGTR.

## Stage 2 — Independent prospective validation

Freeze five fresh matched training seeds and three disjoint episode namespaces before training:

- selector tape A: `740000–740099`;
- selector tape B: `741000–741099`;
- untouched outcome tape: `742000–742099`.

Train exactly UTR and frozen EGTR to the mature endpoint. Select one checkpoint per seed without access to the outcome tape. Evaluate UTR, EGTR, and the selected deployment on the untouched outcome tape, reporting the training seed as the independent unit.

Proceed only if PVF-EGTR has a positive mean paired gain, controlled lower tail and safety, and a nontrivial EGTR promotion rate. No result-dependent repair is allowed.

## Stage 3 — Final confirmation

Repeat the unchanged method on five new seeds with selector namespaces `760000–760099`, `761000–761099`, and untouched outcome namespace `762000–762099`.

The method is supported only if Stage 2 and Stage 3 independently agree. The two cohorts may be descriptively summarized together afterward, but pooled `n=10` cannot replace separate decisions.

## Why this is the highest-probability route

It asks the selector to solve the problem for which evidence exists: distinguish final paired checkpoint utility. It does not ask an online signal to predict failures that repeated mechanism studies could not predict. It also converts uncertainty into conservative fallback instead of another unconditional sampler or optimizer change.
