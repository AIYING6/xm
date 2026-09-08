# 6-UAV V3.1 UTR learnability pilot contract

V3.1 follows the V3 read-only diagnosis. V3's completed-task-only reward led all three UTR endpoints to time out despite legal masks, effective fault injection and observed message delivery. V3.1 preserves the six agents, role actions, actor/critic architecture, PPO implementation, information boundary, relay capacity, fault transition, topology groups, horizon and completion bonus.

The only task-level change is a normalized distance-progress reward for a terminal **only when** its assigned objective receives same-transition legal support. Unassisted terminal actions remain unable to progress. This makes the existing physical movement state visible to PPO before full objective completion; it neither restores hidden failure state nor changes DRTP.

This package runs a scripted Q0 then a UTR-only three-seed 1M pilot. A pass requires two nominal endpoints with success at least 0.5, perturbed success below 0.9 and above 0.1. It does not authorize DRTP training, a cross-scale comparison, or a manuscript claim.
