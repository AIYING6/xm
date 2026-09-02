# Telemetry master specification

Record from the first learner run: role-labelled positions/actions; reward components; mission progress; success/collision/timeout; failure-relative time; static and active directed adjacency; connected components; legal task paths; residual redundancy; message age/provenance/dropout; route/path use, switching and rerouting latency; pre/post-failure degradation and recovery; sampled group/probability; actor loss, critic loss, KL, entropy and clipping.

Write typed, schema-versioned files at fixed intervals and at every failure event. Telemetry is training-only/diagnostic and must be default-off trajectory equivalent when disabled. Evaluation produces outcomes but cannot feed online controls.
