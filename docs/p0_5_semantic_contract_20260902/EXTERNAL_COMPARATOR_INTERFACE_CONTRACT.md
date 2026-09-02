# External comparator interface contract

Main future families are Plain SG-MAPPO, UTR, original DRTP-style adaptive exposure, PLR-style prioritized curriculum, EPOpt-style CVaR robust training, and at most one evidence-nominated candidate. All share backbone, training support, total environment steps, actor information, evaluation tape and checkpoint policy.

PLR level is `(failure structure, timing, duration, geometry member)` and reads training-only learning signals. EPOpt-style MAPPO selects/weights trajectory groups by training-return lower tail from that same source; its epsilon, unit of selection, update schedule and data accounting must be frozen in an implementation audit. Group-DRO remains optional, not a claimed drop-in.
