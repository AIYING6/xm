# test_p3b_env_regression.py — P3-B env parameterized-policy extension regression.
#
# Verifies that adding target_policy="weaving_param" / "break_turn_param"
# (and the config fields target_heading_amp / target_break_turn_amp_rad) does
# NOT change any legacy target-policy behavior:
#   - legacy policies: straight, weaving, weaving_mild, weaving_tiny, break_turn
#   - compare trajectory under the SAME seed / initial state / action sequence
#     against the ORIGINAL env source (checked out from git HEAD~1, the commit
#     before the P3-B extension).
#
# This is a software regression test, NOT a calibration run.
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "envs" / "uav_intercept_3d_env.py"

_TRAJ_RUNNER = r"""
import sys, json
sys.path.insert(0, r"{tmpdir}")
import numpy as np
import uav_intercept_3d_env as m

acts = np.array({acts_json}, dtype=np.int64)
out = []
for cfg_kwargs in {cfg_list_json}:
    cfg = m.UAVIntercept3DConfig(**cfg_kwargs)
    env = m.UAVIntercept3DEnv(cfg)
    env.reset()
    traj = []
    for step in range(30):
        traj.append({{
            "red_pos": env.red_pos[0].tolist(),
            "red_heading": float(env.red_heading[0]),
            "red_gamma": float(env.red_gamma[0]),
            "red_speed": float(env.red_speed[0]),
            "blue_pos": env.blue_pos.tolist(),
            "step": int(env.step_count),
        }})
        env.step(acts[step])
    out.append(traj)
print("TRAJ_END")
print(json.dumps(out))
"""


def run_trajs(env_source: str, cfg_list: list[dict], actions: list[np.ndarray]) -> list[list[dict]]:
    """Run the same fixed action sequence under each cfg; returns per-cfg trajectories."""
    with tempfile.TemporaryDirectory() as td:
        Path(td, "uav_intercept_3d_env.py").write_text(env_source, encoding="utf-8")
        code = _TRAJ_RUNNER.format(
            tmpdir=td,
            acts_json=json.dumps([a.tolist() for a in actions]),
            cfg_list_json=json.dumps(cfg_list),
        )
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           cwd=str(ROOT), timeout=180)
        if r.returncode != 0:
            raise RuntimeError(f"trajectory run failed: {r.stderr[-2500:]}")
        lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
        return json.loads(lines[-1])


def _git_original_source() -> str:
    """env source BEFORE the P3-B extension (HEAD~1)."""
    r = subprocess.run(["git", "-C", str(ROOT), "show", "HEAD~1:envs/uav_intercept_3d_env.py"],
                       capture_output=True, text=True)
    assert r.returncode == 0, f"git show failed: {r.stderr}"
    return r.stdout


def _base_cfg(policy: str, extra: dict | None = None) -> dict:
    cfg = {
        "seed": 1208607,
        "target_policy": policy,
        "communication_dropout_prob": 0.3,
        "message_delay_steps": 2,
        "max_steps": 60,
    }
    if extra:
        cfg.update(extra)
    return cfg


def test_legacy_policy_trajectories_identical():
    orig = _git_original_source()
    new = ENV_FILE.read_text(encoding="utf-8")
    assert orig != new  # the extension exists
    rng = np.random.default_rng(20260808)
    actions = [rng.integers(0, 27, size=3) for _ in range(30)]
    for policy in ["straight", "weaving", "weaving_mild", "weaving_tiny", "break_turn"]:
        t_orig = run_trajs(orig, [_base_cfg(policy)], actions)[0]
        t_new = run_trajs(new, [_base_cfg(policy)], actions)[0]
        assert len(t_orig) == len(t_new) == 30
        for a, b in zip(t_orig, t_new):
            assert a == b, f"legacy trajectory mismatch at {policy} step {a['step']}"


def test_weaving_param_equals_mild_at_same_amp():
    new = ENV_FILE.read_text(encoding="utf-8")
    rng = np.random.default_rng(7)
    actions = [rng.integers(0, 27, size=3) for _ in range(30)]
    cfg_list = [
        _base_cfg("weaving_mild"),
        _base_cfg("weaving_param", {"target_heading_amp": 0.20}),
    ]
    out = run_trajs(new, cfg_list, actions)
    assert out[0] == out[1], "weaving_param(A_h=0.20) != weaving_mild"


def test_break_turn_param_equals_legacy_at_pi_half():
    import math
    new = ENV_FILE.read_text(encoding="utf-8")
    rng = np.random.default_rng(9)
    actions = [rng.integers(0, 27, size=3) for _ in range(30)]
    cfg_list = [
        _base_cfg("break_turn"),
        _base_cfg("break_turn_param", {"target_break_turn_amp_rad": 0.5 * math.pi}),
    ]
    out = run_trajs(new, cfg_list, actions)
    assert out[0] == out[1], "break_turn_param(0.5pi) != break_turn"


def test_p3b_rng_derivation_is_deterministic():
    """Frozen RNG derivation: SHA256-based base seeds, then three seeds each.
    Calibration and formal seeds MUST be disjoint."""
    import hashlib
    cal = hashlib.sha256(b"P3B-CALIBRATION-v1.0").hexdigest()
    for_ = hashlib.sha256(b"P3B-FORMAL-v1.0").hexdigest()
    cal_base = int(cal[:8], 16)
    for_base = int(for_[:8], 16)
    cal_seeds = [cal_base, cal_base + 1, cal_base + 2]
    for_seeds = [for_base, for_base + 1, for_base + 2]
    # reproducibility
    assert int(hashlib.sha256(b"P3B-CALIBRATION-v1.0").hexdigest()[:8], 16) == cal_base
    assert int(hashlib.sha256(b"P3B-FORMAL-v1.0").hexdigest()[:8], 16) == for_base
    # determinism & disjointness
    assert len(set(cal_seeds)) == 3 and len(set(for_seeds)) == 3
    assert not set(cal_seeds) & set(for_seeds)
    # fixed values committed at freeze (hard-assert to prevent silent change)
    assert cal_seeds == [3048223591, 3048223592, 3048223593]
    assert for_seeds == [974060719, 974060720, 974060721]


def test_p3b_severity_bands_and_selection():
    """Frozen bands and primary selection rule."""
    def select(cands: list[tuple[float, float]]) -> tuple[float, float] | None:
        mod = [(q, m) for (q, m) in cands if 0.50 <= q < 0.80]
        if not mod:
            return None
        best = min(mod, key=lambda x: (abs(x[0] - 0.65), x[1]))
        return best

    # moderate candidate closest to 0.65 wins
    assert select([(0.55, 2.0), (0.70, 1.0)]) == (0.70, 1.0)  # |0.70-0.65|=0.05 < |0.55-0.65|=0.10
    # tie -> smaller shift magnitude
    assert select([(0.60, 2.0), (0.70, 1.0)]) == (0.70, 1.0)  # both dist 0.05 -> smaller shift
    assert select([(0.65, 3.0), (0.65, 1.0)]) == (0.65, 1.0)
    # none in moderate -> None (family yields no primary)
    assert select([(0.85, 1.0), (0.10, 2.0)]) is None


def test_p3b_c_structural_metrics_nominal_distribution():
    """Nominal structural qualification produced a sane distribution:
    p_affected>0 (edge really exists), 0<delta_p_path<=1, p_alt>0."""
    from pathlib import Path
    csv_path = Path("docs/statistics/p3a_ood_results_v1_1/p3b_c_structural_nominal.csv")
    if not csv_path.exists():
        import subprocess
        r = subprocess.run([sys.executable, "scripts/p3b_c_structural.py", "--nominal", "--n-ep", "10"],
                           capture_output=True, text=True, cwd=str(ROOT))
        assert r.returncode == 0, r.stderr[-2000:]
    import csv as _csv
    with csv_path.open("r", encoding="utf-8") as f:
        rows = list(_csv.DictReader(f))
    assert rows, "no structural rows"
    pa = [float(r["p_affected"]) for r in rows]
    dp = [float(r["delta_p_path"]) for r in rows]
    alt = [float(r["p_alt"]) for r in rows]
    assert all(0.0 <= x <= 1.0 for x in pa + dp + alt)
    assert any(x > 0.0 for x in pa), "p_affected must be >0 somewhere (edge really exists)"
    assert any(x > 0.0 for x in dp), "delta_p_path must be >0 somewhere (shift changes topology)"
    assert any(x > 0.0 for x in alt), "p_alt must be >0 somewhere (alternate path remains)"
