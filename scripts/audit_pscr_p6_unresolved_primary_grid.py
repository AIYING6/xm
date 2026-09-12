"""Q0 for an unresolved-primary reliability--commitment task.

The decision is moved before current primary service is normally complete.
Forecast staging can then consume time needed by the active request, creating
an actual public-belief trade-off rather than a free future pre-position.
"""
from __future__ import annotations

import argparse
import copy
import csv
import itertools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from envs.pscr_adversarial_service_env import PSCRConfig
from envs.pscr_contingency_service_env import CONTINGENCY_STAGE, PSCRContingencyServiceEnv
from envs.pscr_service_reconfiguration_env import FORECAST_STAGE, FUTURE_SERVICE, PRIMARY_SERVICE, SAFE_HOLD

INTENTS = {"primary": PRIMARY_SERVICE, "forecast": FORECAST_STAGE, "contingency": CONTINGENCY_STAGE, "defer": SAFE_HOLD}
X_OFFSETS, URGENT_PROBABILITY = (-1_000.0, 0.0, 1_000.0), 0.55


def make_env(seed: int, r: float, cell: tuple[float, float, float, int]) -> PSCRContingencyServiceEnv:
    primary, future, lateral, arrival = cell
    return PSCRContingencyServiceEnv(PSCRConfig(seed=seed, primary_forward_distance=primary, future_forward_distance=future, future_lateral_distance=lateral, contingency_forward_distance=11_000.0, future_arrival_step=arrival, future_deadline_urgent_step=arrival + 33, forecast_reliability_choices=(r,), adversary_profile="bounded_mixture"))


def at_commit(seed: int, r: float, cell: tuple[float, float, float, int]) -> PSCRContingencyServiceEnv:
    env = make_env(seed, r, cell); env.reset()
    while env.step_count < cell[3] - 24:
        env.step(np.full(env.num_agents, PRIMARY_SERVICE, dtype=np.int64))
    return env


def branch_value(state: PSCRContingencyServiceEnv, intent: int, sector: int, urgent: bool, x_offset: float) -> float:
    env = copy.deepcopy(state)
    env.future_position = np.asarray((env.config.future_forward_distance + x_offset, sector * env.config.future_lateral_distance, 5_000.0), dtype=np.float32)
    env.future_urgent = urgent; env.future_active = False; env.future_completed = env.future_expired = False; env.future_hold = 0; env._chain_steps["future"] = 0
    while not env.done: env.step(np.full(env.num_agents, FUTURE_SERVICE if env.future_active else intent, dtype=np.int64))
    return float(env.terminal_summary()["weighted_service_value"])


def posterior(state: PSCRContingencyServiceEnv, r: float) -> dict[str, float]:
    out = {name: 0.0 for name in INTENTS}
    for aligned, p_sector in ((True, r), (False, 1.0-r)):
        sector = state.forecast_sector if aligned else -state.forecast_sector
        for urgent, p_urgent in ((True, URGENT_PROBABILITY), (False, 1.0-URGENT_PROBABILITY)):
            for x in X_OFFSETS:
                for name, intent in INTENTS.items(): out[name] += p_sector*p_urgent/len(X_OFFSETS)*branch_value(state, intent, sector, urgent, x)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--states", type=int, default=2); parser.add_argument("--execute", action="store_true"); args = parser.parse_args()
    if not args.execute: raise SystemExit("refusing without --execute")
    if args.output.exists(): raise FileExistsError(args.output)
    grid = tuple(itertools.product((6_500.0, 8_500.0), (12_000.0, 14_000.0), (13_000.0,), (72, 84)))
    rows: list[dict[str, object]]=[]; summary: list[dict[str, object]]=[]
    for cell in grid:
        values={(r,n):[] for r in (.90,.10) for n in INTENTS}
        for r in (.90,.10):
            for offset in range(args.states):
                result=posterior(at_commit(95_000+offset,r,cell),r)
                for n,v in result.items(): values[(r,n)].append(v); rows.append({"primary_forward":cell[0],"future_forward":cell[1],"lateral":cell[2],"arrival":cell[3],"reliability":r,"state_seed":95_000+offset,"intent":n,"public_posterior_value":v})
        mean={(r,n):float(np.mean(values[(r,n)])) for r in (.90,.10) for n in INTENTS}
        rec={"primary_forward":cell[0],"future_forward":cell[1],"lateral":cell[2],"arrival":cell[3],"commit_step":cell[3]-24}
        for r in (.90,.10):
            for n in INTENTS: rec[f"r{r}_{n}"]=mean[(r,n)]
        rec["high_forecast_preferred"]=mean[(.90,"forecast")] > max(mean[(.90,"primary")],mean[(.90,"contingency")],mean[(.90,"defer")])+.05
        rec["low_primary_preferred"]=mean[(.10,"primary")] > max(mean[(.10,"forecast")],mean[(.10,"contingency")],mean[(.10,"defer")])+.05
        rec["gate_pass"]=bool(rec["high_forecast_preferred"] and rec["low_primary_preferred"]); summary.append(rec)
    passing=[r for r in summary if r["gate_pass"]]; args.output.mkdir(parents=True)
    for name,data in (("PSCR_P6_ROWS.csv",rows),("PSCR_P6_SUMMARY.csv",summary)):
        with (args.output/name).open("w",newline="",encoding="utf-8") as h: w=csv.DictWriter(h,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
    report={"protocol":"PSCR-P6-UNRESOLVED-PRIMARY-Q0","diagnostic_only":True,"states_per_reliability":args.states,"grid_cells":len(grid),"passing_cells":passing,"verdict":"PSCR_P6_IDENTIFIABILITY_PASS" if passing else "PSCR_P6_IDENTIFIABILITY_FAIL","interpretation":"Pass establishes a public-belief resource-allocation conflict only; it does not establish learned-method efficacy."}
    (args.output/"PSCR_P6_REPORT.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8"); print(json.dumps(report,indent=2))


if __name__ == "__main__": main()
