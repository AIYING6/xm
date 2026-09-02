# Storage and serialization plan

The existing 50 GB disk is scratch only. Reserve 0.5--1 TB durable object storage provisionally for the full programme. Before P1, a serialization-byte audit on the finalized schema must measure summary, event window, diagnostic full trajectory and checkpoint bytes; then freeze cadence, compression, retention, archival and checksum policy. If durable storage is unavailable, verdict becomes `RESOURCE_PLAN_NOT_READY` and no key telemetry may be discarded to proceed.
