# Phase S3 Cloud Scheduling Amendment — Nine-Way Concurrency

**Amendment ID:** `PHASE-S3-TMDS-V1-A1`  
**Status:** FROZEN BEFORE CLOUD LAUNCH

## Change

The AutoDL single-4090 cloud launcher schedules all nine already frozen S3
development-only runs concurrently. Each process uses one CPU thread on the
16-vCPU host. This replaces the previous 6+3 batch schedule.

## Unchanged scientific contract

This amendment changes only process scheduling. It does not change any method,
development seed, training budget, environment, business-grounded geometry,
failure semantics, reward, endpoint, checkpoint rule, final paired evaluation,
or S3 decision rule. Every run remains 200,192 environment steps and evaluates
only its fixed final checkpoint on 100 nominal/failure pairs.

## Operational boundary

Nine processes deliberately oversubscribe one RTX 4090. Throughput may be
lower than the six-way schedule and an out-of-memory or technical failure must
preserve logs and prevent auto-shutdown. A failed run must not be restarted,
excluded, or replaced without a separately documented amendment.
