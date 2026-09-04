# PVF-EGTR mathematical specification

## Objects

For training seed (s), train two matched policies under identical architecture, optimizer, environment, horizon, and initialization seed:

\[
\pi^U_s = \operatorname{Train}(s,\text{UTR}),\qquad
\pi^E_s = \operatorname{Train}(s,\text{frozen EGTR}).
\]

The policies differ only in the already frozen training sampler. No policy mixing, ensemble inference, online gate, checkpoint cherry-picking, or EGTR parameter change is permitted.

## Paired selector evidence

Let (T_A) and (T_B) be two disjoint selector tapes. Each tape has 100 paired episode IDs for each of the seven conditions `nominal/F0/TE/TL/DS/DL/CP`. Both policies are evaluated on the same IDs.

For tape (T), define:

\[
\Delta_{\mathrm{pert}}^T = J_{\mathrm{pert\ mean}}(\pi^E_s,T)-J_{\mathrm{pert\ mean}}(\pi^U_s,T),
\]

\[
\Delta_{\mathrm{worst}}^T = J_{\mathrm{pert\ worst}}(\pi^E_s,T)-J_{\mathrm{pert\ worst}}(\pi^U_s,T),
\]

\[
\Delta_{\mathrm{nom}}^T = J_{\mathrm{nominal}}(\pi^E_s,T)-J_{\mathrm{nominal}}(\pi^U_s,T).
\]

The primary paired effect also receives a one-sided 95% lower confidence bound (L_T), computed by a stratified paired bootstrap with exactly 10,000 resamples and RNG seed `20260904`. Episode resampling is used only to quantify evaluation noise within one trained pair; the training seed remains the independent scientific unit in cross-seed claims.

## Per-tape promotion predicate

Let the pre-existing practical margin be

\[
\epsilon_J=7.874919837916801.
\]

Tape (T) passes only if all conditions hold:

\[
\Delta_{\mathrm{pert}}^T>\epsilon_J,\quad L_T>0,
\]

\[
\Delta_{\mathrm{worst}}^T\ge-\epsilon_J,\quad
\Delta_{\mathrm{nom}}^T\ge-\epsilon_J,
\]

and EGTR-minus-UTR collision and timeout deltas are each at most `0.05` in the failure-group mean and at most `0.10` in every individual condition. Constraint violations must equal zero.

## Deployment rule

\[
\pi^{PVF}_s =
\begin{cases}
\pi^E_s,& \operatorname{Pass}(T_A)\land\operatorname{Pass}(T_B),\\
\pi^U_s,& \text{otherwise}.
\end{cases}
\]

Missing data, disagreement, borderline effects, or any safety failure always resolve to UTR. There is no third state and no manual override after outcomes are observed.

## Expected gain and remaining risk

Relative to UTR, the deployed gain is

\[
G^{PVF}_s=I_sG^E_s,
\]

where (I_s\in\{0,1\}) is the frozen selector decision. A false negative loses EGTR upside but returns to UTR; a false positive can still deploy a harmful EGTR checkpoint. Therefore the scientific target is not a theorem of non-negative gain, but prospectively demonstrated low false-promotion rate plus positive cross-seed mean/lower-tail gain.

## Cost

- Training: two mature trajectories per pipeline seed, rather than three in the completed UTR/Original/EGTR comparison.
- Selector: `2 arms × 2 tapes × 7 conditions × 100 episodes = 2,800 episodes` per pipeline seed.
- Deployment: one checkpoint and ordinary inference cost.

