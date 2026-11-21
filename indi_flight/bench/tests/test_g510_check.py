#!/usr/bin/env python3
"""Self-test of g510_check.analyse on synthetic data with a known answer: python3 bench/tests/test_g510_check.py"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g510_check as g

ev = dict(sat=10.0, rec=15.0, agg=25.0, aghold=31.0, end=41.0)
sp = {"rec": np.array([3.0, 0, -3.0]), "agg": np.array([23.0, 0, -7.0])}
t = np.arange(0, 41.0, 0.01)


def make(dz_sag=1.0, sat_ok=True, settle=2.0):
    pos = np.zeros((len(t), 3))
    pos[:, 2] = -3.0
    # SAT part: x -> 3 at t=15+settle (linear ramp from 10), z sags 1 m at t=14 then recovers
    pos[:, 0] = np.where(t < 10, 0, np.clip((t - 10) / (5 + settle - 0) * 3.0, 0, 3.0))
    pos[:, 2] += dz_sag * np.exp(-((t - 14) / 2) ** 2)  # NED: +z = down
    pos[t >= 25, 0] = 3.0 + np.clip((t[t >= 25] - 25) / 8.0 * 20.0, 0, 20.0)
    pos[t >= 25, 2] = -3.0 - np.clip((t[t >= 25] - 25) / 8.0 * 4.0, 0, 4.0)
    tm = np.arange(0, 41.0, 0.01)
    cmd = np.full((len(tm), 4), 0.137)
    if sat_ok:
        cmd[(tm >= 10) & (tm < 14)] = 0.274      # saturated 4 of 5 s of SAT
        cmd[(tm >= 25) & (tm < 27)] = 1.0        # saturated 2 of 6 s of AGG, last sample at 27 s
    return pos, np.full(len(t), 5.0), tm, cmd


pos, tilt, tm, cmd = make()
r = g.analyse(t, pos, tilt, tm, cmd, ev, sp)
assert abs(r["alt_loss_m"] - 1.0) < 0.02, r["alt_loss_m"]
assert abs(r["tilt_max_deg"] - 5.0) < 1e-9
assert abs(r["sat_frac_sat_part"] - 0.8) < 0.01 and abs(r["sat_frac_agg_part"] - 2 / 16) < 0.01 and r["sat_frac_rec_part"] == 0.0
assert abs(r["last_sat_agg_s"] - 27.0) < 0.02
assert r["verdict"]["back_sat"] and not r["loc"] and not r["invalid"], r
# SAT x reaches 3 m at t = 10 + 7 = 17: within 0.3 m from x = 2.7, t = 16.3; the 1 m z sag is gone by then -> about 1.3 s
assert 1.0 < r["back_s_sat"] < 3.5, r["back_s_sat"]
# AGG: reaches 0.3 m of (23, -4) at t = 25 + 8 - 0.3 / 20 * 8 ~= 32.9 s -> 5.9 s after the last saturated sample: FAIL
assert 5.5 < r["back_s_agg"] < 6.5 and not r["verdict"]["back_agg"] and not r["pass"], r["back_s_agg"]
# slower settle: SAT back time > 5 s -> fail
pos2, *_ = make(settle=12.0)
assert not g.analyse(t, pos2, tilt, tm, cmd, ev, sp)["verdict"]["back_sat"]
# altitude loss over the limit and tilt over the limit
pos3, *_ = make(dz_sag=2.5)
r3 = g.analyse(t, pos3, np.full(len(t), 25.0), tm, cmd, ev, sp)
assert not r3["verdict"]["alt_loss"] and not r3["verdict"]["tilt"]
# no saturation -> invalid; ground touch -> loc
pos4, tilt4, tm4, cmd4 = make(sat_ok=False)
assert len(g.analyse(t, pos4, tilt4, tm4, cmd4, ev, sp)["invalid"]) == 2
assert g.analyse(t, pos, np.full(len(t), 70.0), tm, cmd, ev, sp)["loc"]
# back_time: never back -> None
assert g.back_time(t, np.full(len(t), 1.0), 15.0, 25.0) is None
# S175 Q9 a: tilt limit = MPC_TILTMAX_AIR + 5 (45 + 5 = 50 deg): 48 deg passes, 52 fails; default (no param) stays 20 deg
assert g.analyse(t, pos, np.full(len(t), 48.0), tm, cmd, ev, sp, tilt_lim_deg=50.0)["verdict"]["tilt"]
assert not g.analyse(t, pos, np.full(len(t), 52.0), tm, cmd, ev, sp, tilt_lim_deg=50.0)["verdict"]["tilt"]
assert not g.analyse(t, pos, np.full(len(t), 48.0), tm, cmd, ev, sp)["verdict"]["tilt"]
assert g.analyse(t, pos, np.full(len(t), 48.0), tm, cmd, ev, sp, tilt_lim_deg=50.0)["tilt_limit_deg"] == 50.0
print("test_g510_check: OK")
