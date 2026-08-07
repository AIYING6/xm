# Canonical consistency audit

| method | metric | canonical | audit ref | diff |
|---|---|---|---|---|
| full_ea_rg | success | 0.9850 | 0.9850 | 0.00000 | tol=0.001
| full_ea_rg | recovery | 0.9706 | 0.9706 | 0.00003 | tol=0.001
| full_ea_rg | wilson | 0.9384 | 0.9384 | 0.00003 | tol=0.001
| full_ea_rg | t_succ | 46.1380 | 46.1000 | 0.03803 | tol=0.5
| full_ea_rg | t_rec | 10.8173 | 10.8000 | 0.01726 | tol=0.5
| full_ea_rg | collision | 0.0000 | 0.0000 | 0.00000 | tol=0.001
| mappo | success | 0.9708 | 0.9708 | 0.00003 | tol=0.001
| mappo | recovery | 0.9471 | 0.9471 | 0.00004 | tol=0.001
| mappo | wilson | 0.9114 | 0.9114 | 0.00001 | tol=0.001
| mappo | t_succ | 51.0195 | 51.0000 | 0.01955 | tol=0.5
| mappo | t_rec | 17.4243 | 17.4000 | 0.02435 | tol=0.5
| mappo | collision | 0.0000 | 0.0000 | 0.00000 | tol=0.001
| happo | success | 1.0000 | 1.0000 | 0.00000 | tol=0.001
| happo | recovery | 1.0000 | 1.0000 | 0.00000 | tol=0.001
| happo | wilson | 0.9820 | 0.9820 | 0.00004 | tol=0.001
| happo | t_succ | 49.8683 | 49.9000 | 0.03167 | tol=0.5
| happo | t_rec | 16.3092 | 16.3000 | 0.00923 | tol=0.5
| happo | collision | 0.0000 | 0.0000 | 0.00000 | tol=0.001
| param_matched_single | success | 0.9967 | 0.9967 | 0.00003 | tol=0.001
| param_matched_single | recovery | 0.9949 | 0.9949 | 0.00005 | tol=0.001
| param_matched_single | wilson | 0.9749 | 0.9749 | 0.00001 | tol=0.001
| param_matched_single | t_succ | 57.6286 | 57.6000 | 0.02865 | tol=0.5
| param_matched_single | t_rec | 26.2390 | 26.2000 | 0.03905 | tol=0.5
| param_matched_single | collision | 0.0000 | 0.0000 | 0.00000 | tol=0.001

mismatches beyond tolerance: 0