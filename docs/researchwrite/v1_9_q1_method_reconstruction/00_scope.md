# v1.9 Q1 Method Reconstruction — Scope

**Mode:** compose.  
**Status:** PCRF implementation, static audit, and D1 engineering feasibility
gate are complete. D2 budget calibration is prepared but not launched; no
formal training, confirmatory evaluation, OOD evaluation, or manuscript claim
is authorized by this document.

## Objective

Design a new, mechanism-led research line for heterogeneous UAV coordination
under recipient-specific partial observability, delayed/lost communication, and
relay failure. The target is a defensible Q1-level contribution, not a
post-hoc attempt to make every metric favorable.

## Deliverable boundary

This foundation package establishes the scientific question, evidence boundary,
candidate mechanism, falsification criteria, comparison hierarchy, and staged
compute plan. It is not a paper draft and does not authorize any modification
to the frozen v1.8 formal repair execution.

## Readers and language

- Reader: author team deciding whether to open a new v1.9 research line.
- Language: Chinese, with stable English technical terms where useful.
- Stance: conservative, mechanism-first, evidence-bound.

## Non-negotiable constraints

1. v1.8 remains a separate execution and must not be overwritten, stopped, or
   reinterpreted by this v1.9 design package.
2. Every v1.9 actor uses only recipient-specific legal information: local
   sensing and delivered/cache-valid packets with provenance, age, and
   confidence. Critic/global simulator state remains actor-forbidden.
3. Any v1.9 implementation receives a fresh version number, fresh training,
   validation, and confirmatory anchors. It must not reuse a viewed
   confirmatory population.
4. The new method must be justified by an independently observable mechanism;
   adding modules solely to increase nominal performance is out of scope.
5. This package cannot claim that the current EA-RG is superior. The v1.8
   repair result is still pending.

## Deferred work

- architecture revisions beyond the audited PCRF candidate;
- formal sample-size/power calculation from completed v1.8 variance;
- exact v1.9 training budget and GPU cost;
- full literature review and venue selection;
- formal v1.9 experiment authorization.
