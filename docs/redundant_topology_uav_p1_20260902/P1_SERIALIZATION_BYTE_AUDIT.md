# Serialization byte audit

Actual bytes: {"summary": {"raw": 284, "compressed": 208, "ratio": 0.7323943661971831}, "event_window": {"raw": 353, "compressed": 196, "ratio": 0.5552407932011332}, "full_trajectory": {"raw": 738, "compressed": 425, "ratio": 0.575880758807588}, "environment_state": {"raw": 2661, "compressed": 1283, "ratio": 0.48214956783164226}, "checkpoint_proxy": {"raw": 2756, "compressed": 1343, "ratio": 0.487300435413643}}
Projection for 236M steps: {"p50_gb": 0.204045932, "conservative_gb": 0.408091864, "worst_reasonable_gb": 0.714160762}
A 0.5 TB durable allocation is sufficient under this schema projection; 1 TB leaves operational headroom. Re-measure after any schema change.
