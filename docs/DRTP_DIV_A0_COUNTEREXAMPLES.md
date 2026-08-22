# DRTP-DIV-A0 — Counterexamples to a Single Rescue Mechanism

* **Weight-volatility counterexample:** strong seed 1901 has total q variation
  14.904, whereas weak seed 2002 has 12.270. Excess volatility is not required
  for weak outcome.
* **Concentration counterexample:** q concentration above 0.30 is present in
  every seed, including strong seed 2003 (0.971 fraction) and weak seed 1902
  (0.844 fraction). It is not a discriminative failure condition.
* **PPO counterexample:** weak and strong seeds overlap in early KL, clipping,
  value loss, and explained variance. No shared optimizer abnormality occurs.
* **Policy-distance counterexample:** at 0.5M, weak mean TV/JS (0.458/0.159)
  are below strong mean TV/JS (0.535/0.221). Large early policy distance is not
  the weak-seed precursor.
* **Coordination counterexample:** any coordination-first story would require
  trajectory data that were not stored; final timeout alone cannot identify its
  behavioral cause.

These counterexamples block a falsifiable, single-mechanism repair proposal.

