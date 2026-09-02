# Staged experiment plan

This is a conditional plan only. P0 stops here.

1. Independently establish a group-discriminative, policy-free structural quantity (without using performance labels).
2. Freeze one p0 and an external comparator mapping before training.
3. Run an exact-interface technical audit: default-off equivalence, RNG isolation, save/resume, and no evaluation leakage.
4. Only then consider a small fresh-seed pilot; no sweep, no automatic continuation.

Because step 1 did not pass, steps 2–4 are **not authorized**.
