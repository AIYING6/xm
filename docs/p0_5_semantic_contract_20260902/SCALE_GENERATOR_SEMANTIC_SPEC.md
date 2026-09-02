# Scale-generator semantic specification

Input configuration supplies role counts, objective count (= terminal count), layered edge templates, capacity per role, physical geometry templates, deadline rule, action schema, safety radius, freshness parameter, static-failure registry and telemetry cadence. Derived fields include all dimensions, legal paths, normalizers, canonical failure masks and manifests. A generator validation rejects non-layered edges, bypass edges, inconsistent counts and hand-coded per-scale logic.
