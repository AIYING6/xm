# T4 — Latent Support Representation Report

## Question and procedure

T4 asks whether support-relevant future continuity is differently represented in frozen policies, without treating diagnostic labels as actor inputs. A linear probe predicts the existing 16-step future-continuity label from three recorded/frozen representations:

- attacker raw legal observation;
- attacker SG latent (the shared graph encoder output);
- attacker pre-policy latent.

Splits are by deterministic episode identity (`episode_id mod 5`), not random rows. Each seed is evaluated independently; rows within an episode are not treated as independent training repetitions.

## Decodability results

| Representation | Mean AUC (five seeds) | Good mean AUC | Weak mean AUC | Good − weak |
|---|---:|---:|---:|---:|
| Raw actor observation | 0.964 | 0.978 | 0.962 | +0.016 |
| SG latent | 0.921 | 0.931 | 0.923 | +0.008 |
| Pre-policy latent | 0.960 | 0.976 | 0.970 | +0.006 |

All three representations encode substantial continuity-related information. Critically, neither latent representation shows a material good-versus-weak decoding advantage over the raw legal observation. The graph latent is modestly less decodable overall, while the pre-policy latent returns close to raw-observation performance.

## Interpretation boundary

This is evidence against a claim that weak-seed behavior is explained simply by an inability to represent support-related state. It is compatible with the T4 sensitivity result: good and weak policies may map similarly available information to different action distributions.

The probe does not prove that the latent causes the action or that continuity is the right target for a new method. It also does not reopen the T3 conclusion: additional temporal history had no material predictability advantage in the prior audit.

The complete per-seed AUC and balanced-accuracy values are retained in `t4_utilization_audit.json` under `latent_decodability`.
