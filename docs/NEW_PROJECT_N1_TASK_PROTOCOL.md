# N1 task protocol: outcome, timing, and execution-information contract

**Status:** `N1_TASK_PROTOCOL_FROZEN__READY_FOR_N2_LEARNABILITY_AND_BASELINE_CHECK`.

N1 defines what the new simulated standoff-neutralization task measures. It
does not name a learning method, change a reward, construct a baseline, or
authorize training.

## 1. Frozen mission-outcome taxonomy

Every episode receives exactly one mutually exclusive terminal outcome:

| Code | Meaning | Evaluator source |
|---|---|---|
| `NEUTRALIZED` | Four consecutive legal `engage_commit` transitions in the true standoff envelope. This is the only mission success. | true kinematics + action |
| `COLLISION` | Any blue--target or blue--blue collision. | true positions |
| `CONSTRAINT_FAILURE` | Altitude or world-boundary constraint violation of a blue aircraft. | true kinematics |
| `TARGET_ESCAPE` | Target true XY position crosses the frozen escape radius before neutralization. | true target position |
| `TIMEOUT` | No prior terminal outcome by the administrative horizon. | evaluator clock |

Priority is frozen, highest first:

1. `COLLISION`;
2. `CONSTRAINT_FAILURE`;
3. `NEUTRALIZED`;
4. `TARGET_ESCAPE`;
5. `TIMEOUT`.

Thus a same-step collision or constraint violation defeats a putative
neutralization. A same-step valid neutralization defeats target escape. Neither
`chain_closed` nor physical-engagement readiness is a terminal outcome or a
success synonym.

The N1 nominal task enables N0 neutralization and sets
`target_escape_radius=35,000 m`. This is inside the existing target
boundary-steering threshold, so escape is a real terminal evaluator state
rather than a post-hoc coordinate label.

## 2. Method-independent timing calibration

The timing calibration uses an evaluator-only scripted controller, not a
learning policy and not a future baseline. It reads true simulator kinematics
solely to show physical reachability and uses `engage_commit` only inside the
same true envelope that defines the task. Its negative control samples random
legacy flight actions with `engage_commit=0` for every agent.

Before executing the formal calibration, the following are frozen:

| Item | Frozen value |
|---|---|
| Controllers | `scripted_oracle`; `random_no_commit` |
| Episodes per controller | 48 |
| Episode seeds | 610000--610047, paired across controllers |
| Target motion | existing deterministic `evasive` policy |
| Calibration maximum horizon | 360 transitions |
| Escape radius | 35,000 m |
| Completion hold | 4 transitions |
| Data used | true simulator state for oracle only; no trained policy or actor observation |

The preliminary 8-episode controller smoke run is engineering-only and is
excluded from all timing quantiles and all task decisions.

Let \(q_{0.90}\) be the empirical 90th percentile of the 48 scripted-oracle
`NEUTRALIZED` times. The primary restricted evaluation window is selected once
by the following mechanical rule:

\[
\tau_{\rm primary}=20\left\lceil\frac{q_{0.90}+20}{20}\right\rceil.
\]

If the oracle does not neutralize at least 80% of its episodes, or if this
rule yields a value outside 120--260 transitions, N1 is **NO-GO** and no
learning method may be connected. Otherwise this value is frozen as the new
primary window. The episode administrative horizon remains 360 transitions;
any later secondary window must be selected before method training.

The N1 reachability GO criterion additionally requires the negative control to
have neutralization incidence at most 10 percentage points of the oracle's
incidence. This tests "reachable but not trivial" without comparing learning
algorithms.

### Calibration result and frozen time semantics

The formal 48 paired-seed calibration passed. `scripted_oracle` produced 47/48
`NEUTRALIZED` episodes (97.9%), with times 88--180, median 103 and P90 158.8
transitions; its one remaining episode was `TARGET_ESCAPE`. `random_no_commit`
produced 0/48 neutralizations and 48/48 `TARGET_ESCAPE` outcomes. No collision,
constraint failure or timeout occurred in either controller. These are task
calibration facts, not learning-method results.

The mechanical rule gives

\[
\tau_{\rm primary}=20\left\lceil\frac{158.8+20}{20}\right\rceil=180.
\]

Therefore the primary future task endpoint is **restricted mean time to
neutralization at 180 transitions**:

\[
\operatorname{RMTN}_{180}=E[\min(T_N,180)],
\]

where \(T_N\) is the first `NEUTRALIZED` transition and is treated as infinity
when collision, constraint failure, target escape, or no neutralization before
the restriction horizon occurs. Every such episode contributes 180. Lower is
better. This is a task-specific restricted-time estimand, not a Kaplan--Meier
claim: simulator follow-up is complete, so terminal outcomes are retained in
the denominator rather than censored away. Future reports must also decompose
neutralization incidence, collision incidence, constraint-failure incidence,
target-escape incidence, and active-unneutralized probability by 180. The
administrative episode horizon is fixed at 360 transitions.

## 3. Recipient-specific actor information contract

### Execution-time actor inputs

At decision time, each blue actor may use only:

- its own physical state, own role and its own previous action/history;
- local target measurements produced by its sensor at that transition;
- delivered, cache-valid packet snapshots addressed to it, including sender
  status, age, confidence and provenance masks;
- local delivery/drop/delay/failure indicators that the recipient can observe;
- graph nodes, edges and relation masks built exclusively from those same
  recipient-legal fields; and
- for an attacker/interceptor only, the action choice `engage_commit`.

The new target lifecycle, true neutralization eligibility, hold counter,
target escape flag, collision state and evaluator outcome are never actor
features. `engage_commit` is an action, not an information channel.

### Explicitly forbidden actor inputs

Actors must not use simulator-global target/teammate truth when not locally
sensed or delivered, another actor's cache, undelivered/dropped/expired packet
payload, global graph aggregates, `chain_closed`, evaluator terminal labels,
or any controller/oracle state.

### Communication semantics

The existing validated contract carries forward unchanged:

- C evidence means actually delivered **and cache-valid** communication;
- target packets with age `<= max_target_message_age_steps` are eligible;
- packets with age above that bound are excluded from C availability, C nodes,
  C adjacency and the actor C branch rather than merely down-weighted;
- packet loss, delay and relay failure cannot refresh a recipient cache from
  simulator truth.

### Centralized training boundary

A future centralized critic may receive explicitly declared training-only
state, but it must not feed actor features, graph nodes/edges, action masks,
or any execution-time recurrent state. This must be re-tested counterfactually
before a method is authorized.

## 4. N1 deterministic contract checks

Before N1 passes, deterministic checks must show that: target escape is a
terminal outcome; neutralization beats simultaneous escape but not collision;
an ineligible role cannot create an effective commit; and evaluator lifecycle
state cannot change observations or graph inputs.

## N1 verdict rule

**PASS —** the formal calibration meets both reachability criteria, the timing
rule resolves mechanically to 180, and all four N1 deterministic contract
checks pass. The project may enter
`N1_TASK_PROTOCOL_FROZEN__READY_FOR_N2_LEARNABILITY_AND_BASELINE_CHECK`.
N2 remains a method-blind learnability/baseline gate; it is not authorization
to invent or train a new main method. Any N2 failure is a stop condition, not a
reason to alter the frozen task or timing semantics.
