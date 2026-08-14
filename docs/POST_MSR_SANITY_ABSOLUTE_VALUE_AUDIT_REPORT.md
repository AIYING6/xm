# Post-MSR Sanity and Absolute-Value Audit

## Scope

This is the zero-training Stage SVA audit required by `POST_MSR_SANITY_OOD_GAP_SCAN_AND_FINAL_ALGORITHM_DECISION.md`. No ENMM, new architecture, new loss, canonical seed, or formal five-seed training was started.

## Six-checkpoint absolute values

| group | seed | J_nominal | J_failure | Delta_J | exposure |
|---|---:|---:|---:|---:|---:|
| fl_nominal_expert | 1801 | 103.712179 | 34.921951 | 68.790228 | 1.0 |
| fl_nominal_expert | 1802 | 22.510347 | 10.384699 | 12.125648 | 1.0 |
| fl_f0_expert | 1801 | 80.724363 | 65.558993 | 15.165370 | 1.0 |
| fl_f0_expert | 1802 | 38.479867 | 63.387111 | -24.907243 | 1.0 |
| mixed50_sg | 1801 | 91.941832 | 104.633138 | -12.691306 | 0.99 |
| mixed50_sg | 1802 | 183.381681 | 171.978675 | 11.403006 | 1.0 |

The MSR empirical specialist references are `J_N_star=63.111263000269` and `J_F_star=64.473051863208`. They are empirical tape references, not theoretical optima.

The exact normalization is:

`C_N = pooled Mixed-50 J_nominal / pooled nominal-expert J_nominal = 2.181254979533`

`C_F = pooled Mixed-50 J_failure / pooled F0-expert J_failure = 2.145173878004`

`C_min = min(C_N, C_F) = 2.145173878004`

## Deterministic cross-tape replay

Ten IDs from each of FL tape `370000–370049` and MSR tape `380000–380099` were replayed under nominal and canonical F0 for all six checkpoints. The archived 370/380 rows were compared where available; Mixed-50 has no historical 370 evaluation, so its 370 replay is retained as a new diagnostic observation.

| group | seed | tape | episode | condition | absolute J difference |
|---|---:|---|---:|---|---:|
| fl_nominal_expert | 1801 | fl370 | 370000 | nominal | 3.05566937e-06 |
| fl_nominal_expert | 1801 | fl370 | 370000 | relay_failure | 1.33924186e-06 |
| fl_nominal_expert | 1801 | fl370 | 370001 | nominal | 6.14672899e-07 |
| fl_nominal_expert | 1801 | fl370 | 370001 | relay_failure | 5.21540642e-07 |
| fl_nominal_expert | 1801 | fl370 | 370002 | nominal | 5.36441803e-07 |
| fl_nominal_expert | 1801 | fl370 | 370002 | relay_failure | 1.57393515e-06 |
| fl_nominal_expert | 1801 | fl370 | 370003 | nominal | 4.82425094e-07 |
| fl_nominal_expert | 1801 | fl370 | 370003 | relay_failure | 1.39512122e-06 |
| fl_nominal_expert | 1801 | fl370 | 370004 | nominal | 1.60932541e-06 |
| fl_nominal_expert | 1801 | fl370 | 370004 | relay_failure | 1.47521496e-06 |
| fl_nominal_expert | 1801 | fl370 | 370005 | nominal | 5.14090061e-07 |
| fl_nominal_expert | 1801 | fl370 | 370005 | relay_failure | 4.71249223e-07 |
| fl_nominal_expert | 1801 | fl370 | 370006 | nominal | 1.19954348e-06 |
| fl_nominal_expert | 1801 | fl370 | 370006 | relay_failure | 5.30853868e-07 |
| fl_nominal_expert | 1801 | fl370 | 370007 | nominal | 7.63684511e-08 |
| fl_nominal_expert | 1801 | fl370 | 370007 | relay_failure | 1.93715096e-07 |
| fl_nominal_expert | 1801 | fl370 | 370008 | nominal | 1.17719173e-06 |
| fl_nominal_expert | 1801 | fl370 | 370008 | relay_failure | 1.47894025e-06 |
| fl_nominal_expert | 1801 | fl370 | 370009 | nominal | 4.91738319e-07 |
| fl_nominal_expert | 1801 | fl370 | 370009 | relay_failure | 2.83122063e-07 |
| fl_nominal_expert | 1801 | msr380 | 380000 | nominal | 7.89761543e-07 |
| fl_nominal_expert | 1801 | msr380 | 380000 | relay_failure | 1.45658851e-06 |
| fl_nominal_expert | 1801 | msr380 | 380001 | nominal | 2.9169023e-06 |
| fl_nominal_expert | 1801 | msr380 | 380001 | relay_failure | 2.46427953e-06 |
| fl_nominal_expert | 1801 | msr380 | 380002 | nominal | 7.07805157e-07 |
| fl_nominal_expert | 1801 | msr380 | 380002 | relay_failure | 1.14552677e-06 |
| fl_nominal_expert | 1801 | msr380 | 380003 | nominal | 2.42143869e-08 |
| fl_nominal_expert | 1801 | msr380 | 380003 | relay_failure | 2.08616257e-07 |
| fl_nominal_expert | 1801 | msr380 | 380004 | nominal | 5.71832061e-07 |
| fl_nominal_expert | 1801 | msr380 | 380004 | relay_failure | 4.73111868e-07 |
| fl_nominal_expert | 1801 | msr380 | 380005 | nominal | 7.74860382e-07 |
| fl_nominal_expert | 1801 | msr380 | 380005 | relay_failure | 1.01141632e-06 |
| fl_nominal_expert | 1801 | msr380 | 380006 | nominal | 1.18790194e-06 |
| fl_nominal_expert | 1801 | msr380 | 380006 | relay_failure | 1.02631748e-06 |
| fl_nominal_expert | 1801 | msr380 | 380007 | nominal | 4.92669642e-07 |
| fl_nominal_expert | 1801 | msr380 | 380007 | relay_failure | 1.80117786e-06 |
| fl_nominal_expert | 1801 | msr380 | 380008 | nominal | 2.25007534e-06 |
| fl_nominal_expert | 1801 | msr380 | 380008 | relay_failure | 2.30967999e-07 |
| fl_nominal_expert | 1801 | msr380 | 380009 | nominal | 8.19563866e-08 |
| fl_nominal_expert | 1801 | msr380 | 380009 | relay_failure | 4.43309546e-07 |
| fl_nominal_expert | 1802 | fl370 | 370000 | nominal | 1.00582838e-07 |
| fl_nominal_expert | 1802 | fl370 | 370000 | relay_failure | 3.60235572e-06 |
| fl_nominal_expert | 1802 | fl370 | 370001 | nominal | 1.69500709e-07 |
| fl_nominal_expert | 1802 | fl370 | 370001 | relay_failure | 1.63912773e-06 |
| fl_nominal_expert | 1802 | fl370 | 370002 | nominal | 8.30739737e-07 |
| fl_nominal_expert | 1802 | fl370 | 370002 | relay_failure | 2.31713057e-06 |
| fl_nominal_expert | 1802 | fl370 | 370003 | nominal | 0 |
| fl_nominal_expert | 1802 | fl370 | 370003 | relay_failure | 3.50922346e-06 |
| fl_nominal_expert | 1802 | fl370 | 370004 | nominal | 1.52736902e-07 |
| fl_nominal_expert | 1802 | fl370 | 370004 | relay_failure | 3.01748514e-07 |
| fl_nominal_expert | 1802 | fl370 | 370005 | nominal | 1.47148967e-07 |
| fl_nominal_expert | 1802 | fl370 | 370005 | relay_failure | 1.62050128e-06 |
| fl_nominal_expert | 1802 | fl370 | 370006 | nominal | 1.62050128e-07 |
| fl_nominal_expert | 1802 | fl370 | 370006 | relay_failure | 1.32247806e-07 |
| fl_nominal_expert | 1802 | fl370 | 370007 | nominal | 1.12131238e-06 |
| fl_nominal_expert | 1802 | fl370 | 370007 | relay_failure | 2.0628795e-07 |
| fl_nominal_expert | 1802 | fl370 | 370008 | nominal | 2.22586095e-06 |
| fl_nominal_expert | 1802 | fl370 | 370008 | relay_failure | 3.62098217e-06 |
| fl_nominal_expert | 1802 | fl370 | 370009 | nominal | 1.11758709e-07 |
| fl_nominal_expert | 1802 | fl370 | 370009 | relay_failure | 1.51619315e-06 |
| fl_nominal_expert | 1802 | msr380 | 380000 | nominal | 2.25380063e-07 |
| fl_nominal_expert | 1802 | msr380 | 380000 | relay_failure | 1.58324838e-07 |
| fl_nominal_expert | 1802 | msr380 | 380001 | nominal | 6.70552254e-08 |
| fl_nominal_expert | 1802 | msr380 | 380001 | relay_failure | 2.15694308e-06 |
| fl_nominal_expert | 1802 | msr380 | 380002 | nominal | 2.35438347e-06 |
| fl_nominal_expert | 1802 | msr380 | 380002 | relay_failure | 8.38190317e-08 |
| fl_nominal_expert | 1802 | msr380 | 380003 | nominal | 2.27615237e-06 |
| fl_nominal_expert | 1802 | msr380 | 380003 | relay_failure | 1.98185444e-06 |
| fl_nominal_expert | 1802 | msr380 | 380004 | nominal | 7.82310963e-08 |
| fl_nominal_expert | 1802 | msr380 | 380004 | relay_failure | 1.57393515e-06 |
| fl_nominal_expert | 1802 | msr380 | 380005 | nominal | 4.78699803e-07 |
| fl_nominal_expert | 1802 | msr380 | 380005 | relay_failure | 9.92789865e-07 |
| fl_nominal_expert | 1802 | msr380 | 380006 | nominal | 1.04308128e-07 |
| fl_nominal_expert | 1802 | msr380 | 380006 | relay_failure | 1.37463212e-06 |
| fl_nominal_expert | 1802 | msr380 | 380007 | nominal | 1.99303031e-07 |
| fl_nominal_expert | 1802 | msr380 | 380007 | relay_failure | 3.16649675e-08 |
| fl_nominal_expert | 1802 | msr380 | 380008 | nominal | 1.89524144e-07 |
| fl_nominal_expert | 1802 | msr380 | 380008 | relay_failure | 1.67405233e-06 |
| fl_nominal_expert | 1802 | msr380 | 380009 | nominal | 1.65449455e-06 |
| fl_nominal_expert | 1802 | msr380 | 380009 | relay_failure | 1.56881288e-06 |
| fl_f0_expert | 1801 | fl370 | 370000 | nominal | 3.30433249e-06 |
| fl_f0_expert | 1801 | fl370 | 370000 | relay_failure | 9.35047865e-07 |
| fl_f0_expert | 1801 | fl370 | 370001 | nominal | 6.48200512e-07 |
| fl_f0_expert | 1801 | fl370 | 370001 | relay_failure | 2.4177134e-06 |
| fl_f0_expert | 1801 | fl370 | 370002 | nominal | 4.12389636e-06 |
| fl_f0_expert | 1801 | fl370 | 370002 | relay_failure | 1.65402889e-06 |
| fl_f0_expert | 1801 | fl370 | 370003 | nominal | 3.04728746e-06 |
| fl_f0_expert | 1801 | fl370 | 370003 | relay_failure | 1.9017607e-06 |
| fl_f0_expert | 1801 | fl370 | 370004 | nominal | 1.85891986e-06 |
| fl_f0_expert | 1801 | fl370 | 370004 | relay_failure | 2.39536166e-06 |
| fl_f0_expert | 1801 | fl370 | 370005 | nominal | 1.99815258e-06 |
| fl_f0_expert | 1801 | fl370 | 370005 | relay_failure | 1.17300078e-06 |
| fl_f0_expert | 1801 | fl370 | 370006 | nominal | 1.1920929e-06 |
| fl_f0_expert | 1801 | fl370 | 370006 | relay_failure | 1.79931521e-06 |
| fl_f0_expert | 1801 | fl370 | 370007 | nominal | 2.95042992e-06 |
| fl_f0_expert | 1801 | fl370 | 370007 | relay_failure | 2.32458115e-06 |
| fl_f0_expert | 1801 | fl370 | 370008 | nominal | 1.63167715e-06 |
| fl_f0_expert | 1801 | fl370 | 370008 | relay_failure | 7.4505806e-09 |
| fl_f0_expert | 1801 | fl370 | 370009 | nominal | 1.3881363e-06 |
| fl_f0_expert | 1801 | fl370 | 370009 | relay_failure | 9.01985914e-07 |
| fl_f0_expert | 1801 | msr380 | 380000 | nominal | 1.37463212e-06 |
| fl_f0_expert | 1801 | msr380 | 380000 | relay_failure | 2.11084262e-06 |
| fl_f0_expert | 1801 | msr380 | 380001 | nominal | 2.18302011e-06 |
| fl_f0_expert | 1801 | msr380 | 380001 | relay_failure | 1.32620335e-06 |
| fl_f0_expert | 1801 | msr380 | 380002 | nominal | 3.7252903e-08 |
| fl_f0_expert | 1801 | msr380 | 380002 | relay_failure | 7.87898898e-07 |
| fl_f0_expert | 1801 | msr380 | 380003 | nominal | 3.9585866e-06 |
| fl_f0_expert | 1801 | msr380 | 380003 | relay_failure | 1.78068876e-06 |
| fl_f0_expert | 1801 | msr380 | 380004 | nominal | 3.7252903e-07 |
| fl_f0_expert | 1801 | msr380 | 380004 | relay_failure | 1.18464231e-06 |
| fl_f0_expert | 1801 | msr380 | 380005 | nominal | 1.4603138e-06 |
| fl_f0_expert | 1801 | msr380 | 380005 | relay_failure | 4.09409404e-06 |
| fl_f0_expert | 1801 | msr380 | 380006 | nominal | 2.08616257e-07 |
| fl_f0_expert | 1801 | msr380 | 380006 | relay_failure | 2.6691705e-06 |
| fl_f0_expert | 1801 | msr380 | 380007 | nominal | 1.28336251e-06 |
| fl_f0_expert | 1801 | msr380 | 380007 | relay_failure | 2.45636329e-06 |
| fl_f0_expert | 1801 | msr380 | 380008 | nominal | 7.07805157e-07 |
| fl_f0_expert | 1801 | msr380 | 380008 | relay_failure | 2.31340528e-06 |
| fl_f0_expert | 1801 | msr380 | 380009 | nominal | 2.66823918e-07 |
| fl_f0_expert | 1801 | msr380 | 380009 | relay_failure | 1.29686669e-06 |
| fl_f0_expert | 1802 | fl370 | 370000 | nominal | 2.09733844e-06 |
| fl_f0_expert | 1802 | fl370 | 370000 | relay_failure | 2.82563269e-06 |
| fl_f0_expert | 1802 | fl370 | 370001 | nominal | 2.74181366e-06 |
| fl_f0_expert | 1802 | fl370 | 370001 | relay_failure | 2.52760947e-06 |
| fl_f0_expert | 1802 | fl370 | 370002 | nominal | 9.49949026e-07 |
| fl_f0_expert | 1802 | fl370 | 370002 | relay_failure | 3.05473804e-06 |
| fl_f0_expert | 1802 | fl370 | 370003 | nominal | 1.03190541e-06 |
| fl_f0_expert | 1802 | fl370 | 370003 | relay_failure | 2.31713057e-06 |
| fl_f0_expert | 1802 | fl370 | 370004 | nominal | 3.75881791e-06 |
| fl_f0_expert | 1802 | fl370 | 370004 | relay_failure | 3.28011811e-06 |
| fl_f0_expert | 1802 | fl370 | 370005 | nominal | 2.02842057e-06 |
| fl_f0_expert | 1802 | fl370 | 370005 | relay_failure | 2.53692269e-06 |
| fl_f0_expert | 1802 | fl370 | 370006 | nominal | 2.3804605e-06 |
| fl_f0_expert | 1802 | fl370 | 370006 | relay_failure | 2.48290598e-06 |
| fl_f0_expert | 1802 | fl370 | 370007 | nominal | 1.58557668e-06 |
| fl_f0_expert | 1802 | fl370 | 370007 | relay_failure | 2.07126141e-06 |
| fl_f0_expert | 1802 | fl370 | 370008 | nominal | 3.02866101e-06 |
| fl_f0_expert | 1802 | fl370 | 370008 | relay_failure | 5.11668622e-06 |
| fl_f0_expert | 1802 | fl370 | 370009 | nominal | 1.83284283e-06 |
| fl_f0_expert | 1802 | fl370 | 370009 | relay_failure | 2.08429992e-06 |
| fl_f0_expert | 1802 | msr380 | 380000 | nominal | 1.19674951e-06 |
| fl_f0_expert | 1802 | msr380 | 380000 | relay_failure | 3.29315662e-06 |
| fl_f0_expert | 1802 | msr380 | 380001 | nominal | 3.24100256e-06 |
| fl_f0_expert | 1802 | msr380 | 380001 | relay_failure | 4.42191958e-06 |
| fl_f0_expert | 1802 | msr380 | 380002 | nominal | 1.75461173e-06 |
| fl_f0_expert | 1802 | msr380 | 380002 | relay_failure | 8.69855285e-07 |
| fl_f0_expert | 1802 | msr380 | 380003 | nominal | 1.71875581e-06 |
| fl_f0_expert | 1802 | msr380 | 380003 | relay_failure | 1.77323818e-06 |
| fl_f0_expert | 1802 | msr380 | 380004 | nominal | 2.91317701e-06 |
| fl_f0_expert | 1802 | msr380 | 380004 | relay_failure | 1.08964741e-06 |
| fl_f0_expert | 1802 | msr380 | 380005 | nominal | 8.7544322e-07 |
| fl_f0_expert | 1802 | msr380 | 380005 | relay_failure | 1.10641122e-06 |
| fl_f0_expert | 1802 | msr380 | 380006 | nominal | 1.98185444e-06 |
| fl_f0_expert | 1802 | msr380 | 380006 | relay_failure | 3.39187682e-06 |
| fl_f0_expert | 1802 | msr380 | 380007 | nominal | 1.21910125e-06 |
| fl_f0_expert | 1802 | msr380 | 380007 | relay_failure | 4.59328294e-06 |
| fl_f0_expert | 1802 | msr380 | 380008 | nominal | 2.14204192e-06 |
| fl_f0_expert | 1802 | msr380 | 380008 | relay_failure | 2.08802521e-06 |
| fl_f0_expert | 1802 | msr380 | 380009 | nominal | 2.26078555e-06 |
| fl_f0_expert | 1802 | msr380 | 380009 | relay_failure | 1.69081613e-06 |
| mixed50_sg | 1801 | msr380 | 380000 | nominal | 2.90572643e-07 |
| mixed50_sg | 1801 | msr380 | 380000 | relay_failure | 8.94069672e-07 |
| mixed50_sg | 1801 | msr380 | 380001 | nominal | 2.00048089e-06 |
| mixed50_sg | 1801 | msr380 | 380001 | relay_failure | 1.66147947e-06 |
| mixed50_sg | 1801 | msr380 | 380002 | nominal | 7.07805157e-07 |
| mixed50_sg | 1801 | msr380 | 380002 | relay_failure | 1.19954348e-06 |
| mixed50_sg | 1801 | msr380 | 380003 | nominal | 9.31322575e-08 |
| mixed50_sg | 1801 | msr380 | 380003 | relay_failure | 3.40864062e-07 |
| mixed50_sg | 1801 | msr380 | 380004 | nominal | 5.28991222e-07 |
| mixed50_sg | 1801 | msr380 | 380004 | relay_failure | 9.31322575e-08 |
| mixed50_sg | 1801 | msr380 | 380005 | nominal | 8.41915607e-07 |
| mixed50_sg | 1801 | msr380 | 380005 | relay_failure | 1.66893005e-06 |
| mixed50_sg | 1801 | msr380 | 380006 | nominal | 2.17929482e-06 |
| mixed50_sg | 1801 | msr380 | 380006 | relay_failure | 1.78068876e-06 |
| mixed50_sg | 1801 | msr380 | 380007 | nominal | 1.04308128e-06 |
| mixed50_sg | 1801 | msr380 | 380007 | relay_failure | 1.2665987e-06 |
| mixed50_sg | 1801 | msr380 | 380008 | nominal | 1.16229057e-06 |
| mixed50_sg | 1801 | msr380 | 380008 | relay_failure | 1.24424696e-06 |
| mixed50_sg | 1801 | msr380 | 380009 | nominal | 6.40749931e-07 |
| mixed50_sg | 1801 | msr380 | 380009 | relay_failure | 3.89292836e-07 |
| mixed50_sg | 1802 | msr380 | 380000 | nominal | 7.89761543e-07 |
| mixed50_sg | 1802 | msr380 | 380000 | relay_failure | 9.68575478e-07 |
| mixed50_sg | 1802 | msr380 | 380001 | nominal | 2.60025263e-06 |
| mixed50_sg | 1802 | msr380 | 380001 | relay_failure | 1.57952309e-06 |
| mixed50_sg | 1802 | msr380 | 380002 | nominal | 3.94880772e-07 |
| mixed50_sg | 1802 | msr380 | 380002 | relay_failure | 1.14738941e-06 |
| mixed50_sg | 1802 | msr380 | 380003 | nominal | 3.27825546e-07 |
| mixed50_sg | 1802 | msr380 | 380003 | relay_failure | 6.78002834e-07 |
| mixed50_sg | 1802 | msr380 | 380004 | nominal | 1.34110451e-07 |
| mixed50_sg | 1802 | msr380 | 380004 | relay_failure | 3.57627869e-07 |
| mixed50_sg | 1802 | msr380 | 380005 | nominal | 1.34110451e-06 |
| mixed50_sg | 1802 | msr380 | 380005 | relay_failure | 7.00354576e-07 |
| mixed50_sg | 1802 | msr380 | 380006 | nominal | 1.29640102e-06 |
| mixed50_sg | 1802 | msr380 | 380006 | relay_failure | 1.49011612e-07 |
| mixed50_sg | 1802 | msr380 | 380007 | nominal | 1.69873238e-06 |
| mixed50_sg | 1802 | msr380 | 380007 | relay_failure | 2.1904707e-06 |
| mixed50_sg | 1802 | msr380 | 380008 | nominal | 2.16066837e-07 |
| mixed50_sg | 1802 | msr380 | 380008 | relay_failure | 1.02818012e-06 |
| mixed50_sg | 1802 | msr380 | 380009 | nominal | 8.49366188e-07 |
| mixed50_sg | 1802 | msr380 | 380009 | relay_failure | 6.2584877e-07 |

Maximum replay difference: `5.11668622e-06`. Numerical tolerance: `0.0001`.

## Consistency checklist

| item | status | evidence |
|---|---|---|
| six evaluation manifests complete | PASS | six completed manifests, 200 raw and 100 paired rows each |
| common MSR tape | PASS | one tape hash `b403239d849cc9d80730c34248483fff77407d53111010d747649e0b89270d01` |
| checkpoint loading | PASS | archived SHA256 matched evaluation manifests |
| common SG architecture | PASS | Single-Graph, hidden dimension 115, 116,728 parameters |
| common environment/reward/horizon/information boundary | PASS | normalized frozen config keys matched |
| receiver/sender adjacency convention | PASS | same evaluator and unchanged graph packing path |
| terminal/exposure accounting | PASS | exposure retained as an outcome; no post-hoc filtering |
| deterministic replay | PASS | maximum absolute difference within `1e-4` |

## Why C_N and C_F exceed 2

The large normalized values are not caused by tape ID mismatch: the specialist checkpoints are stable between the 370 and 380 tapes, with maximum specialist relative change `0.108174`. The result is driven by the Mixed-50 absolute scores being high on the 380 tape while the two specialist references, especially seed1802, are low. Thus the normalization is valid as an empirical diagnostic, but it is too reference-dependent to be used as the sole final-method objective.

## SVA decision

**SVA-1** — evaluator/configuration semantics are consistent, replay is deterministic within tolerance, and specialist cross-tape instability does not exceed the pre-registered 20% SVA-2 threshold. Proceed to the authorized zero-training OOD gap scan.
