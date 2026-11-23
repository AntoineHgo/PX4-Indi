#!/usr/bin/env python3
"""Self-test of bench/offb_vel_check.py on synthetic ground truth with known answers (G7 checker self-test, S194).

  python3 -I indi_flight/bench/tests/test_offb_vel_check.py     (numpy only; exit 0 = pass, 1 = failure)

S215: the checker now prints a verdict and exits 0 PASS / 1 FAIL / 2 INVALID, checks LOC, reports "never reached", uses a 1 s mean for
final |vx| and reports empty topics; tests for these are at the end of CASES (each fails on the S194 checker). Older text: the checker was a print-only script (no functions, no verdict). pyulog is replaced by a fake module holding synthetic
vehicle_local_position_groundtruth, the script is run with runpy, its printed numbers are parsed and judged here against
the GATES.md G5.5 offb_vel_step limits: RMS(vx-2) over last 3 s of the step <= 0.2, |vx| at end of 4 s hold <= 0.1,
max |dz| <= 0.3. Mutation checks run the same cases against mutated COPIES of the checker and require a detection.
"""
import contextlib
import io
import json
import os
import re
import runpy
import sys
import tempfile
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.join(HERE, "..", "offb_vel_check.py")
CHECKER = [REAL]
DT = 0.02
T_SETTLE, T_STEP, T_HOLD = 2.0, 5.0, 10.0   # step 5 s, hold 4 s after
LIM_RMS, LIM_VEND, LIM_DZ = 0.2, 0.1, 0.3


def make(rms=0.0, vend=0.0, dz=0.0, rise_err=0.0, vend_last_only=False, step_vx=None):
    """Truth log. Last 3 s of the step: vx = 2 +- rms (alternating, RMS exactly rms). First 2 s: rise_err offset.
    Hold: vx = 0 except last sample = vend. One sample with |dz| = dz in the z window."""
    t = np.arange(0.0, 16.0, DT)
    vx = np.zeros(t.size)
    st = (t >= T_STEP) & (t < T_HOLD)
    vx[st] = 2.0 + rise_err
    late = st & (t > T_STEP + 2)
    k = np.arange(late.sum())
    vx[late] = 2.0 + rms * np.where(k % 2 == 0, 1.0, -1.0)
    h = (t >= T_HOLD) & (t < T_HOLD + 4.0)
    hi = np.flatnonzero(h)
    if vend_last_only:
        vx[hi[-1]] = vend
    else:
        vx[hi[t[hi] >= T_HOLD + 3.0]] = vend        # last 1 s of the hold
    if step_vx is not None:
        vx[st] = step_vx
    z = np.full(t.size, -10.0)
    z[np.flatnonzero((t >= 7.0))[0]] = -10.0 - dz
    n = t.size
    return {"timestamp": (t * 1e6).astype(np.uint64), "vx": vx, "vy": np.zeros(n), "z": z, "x": np.cumsum(vx) * DT}


LAST_CODE = [None]


def make_att(tilt_deg=0.0, t_on=7.0, dur=0.0):
    """vehicle_attitude_groundtruth at 100 Hz; tilt (about x) of tilt_deg during [t_on, t_on+dur)."""
    t = np.arange(0.0, 16.0, 0.01)
    a = np.where((t >= t_on) & (t < t_on + dur), np.radians(tilt_deg), 0.0) / 2
    return {"timestamp": (t * 1e6).astype(np.uint64), "q[0]": np.cos(a), "q[1]": np.sin(a), "q[2]": np.zeros(t.size), "q[3]": np.zeros(t.size)}


def run(gt, att=None):
    d = tempfile.mkdtemp()
    ev = [{"name": "settle", "t_us": T_SETTLE * 1e6}, {"name": "vstep", "t_us": T_STEP * 1e6}, {"name": "vhold", "t_us": T_HOLD * 1e6}]
    json.dump({"events": ev}, open(d + "/run.json", "w"))
    open(d + "/flight.ulg", "w").close()
    fake = types.ModuleType("pyulog")

    class ULog:
        def __init__(self, *a, **k):
            self.data_list = [types.SimpleNamespace(name="vehicle_local_position_groundtruth", data=gt, multi_id=0),
                              types.SimpleNamespace(name="vehicle_attitude_groundtruth", data=att if att is not None else make_att(), multi_id=0)]
    fake.ULog = ULog
    old_mod, old_argv = sys.modules.get("pyulog"), sys.argv
    sys.modules["pyulog"], sys.argv = fake, [CHECKER[0], d]
    buf = io.StringIO()
    LAST_CODE[0] = None
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(CHECKER[0], run_name="__main__")
    except SystemExit as e:
        LAST_CODE[0] = e.code
    finally:
        sys.argv = old_argv
        if old_mod is None:
            del sys.modules["pyulog"]
        else:
            sys.modules["pyulog"] = old_mod
    return buf.getvalue()


def verdict(out):
    f = lambda pat: float(re.search(pat, out).group(1))  # noqa: E731
    rms = f(r"last 3 s RMS ([0-9.]+)")
    vend = f(r"final \|vx\| ([0-9.]+)")
    dz = f(r"max \|dz\| ([0-9.]+)")
    return {"rms": rms, "vend": vend, "dz": dz, "rms_ok": rms <= LIM_RMS, "vend_ok": vend <= LIM_VEND, "dz_ok": dz <= LIM_DZ}


def v(**kw):
    return verdict(run(make(**kw)))


def test_nominal_passes():
    r = v(rms=0.05, vend=0.02, dz=0.05)
    assert r["rms_ok"] and r["vend_ok"] and r["dz_ok"], r
    assert abs(r["rms"] - 0.05) < 1e-3 and abs(r["vend"] - 0.02) < 1e-3 and abs(r["dz"] - 0.05) < 1e-3, r


def test_rms_limit():
    assert not v(rms=0.21)["rms_ok"]
    assert v(rms=0.19)["rms_ok"]
    assert v(rms=0.19)["vend_ok"] and v(rms=0.19)["dz_ok"]


def test_rms_uses_last_3s_only():
    # large offset only in the first 2 s of the step (rise): must not count against the last-3 s RMS
    r = v(rms=0.05, rise_err=-0.9)
    assert r["rms_ok"] and abs(r["rms"] - 0.05) < 1e-3, r


def test_end_vx_limit():
    assert not v(vend=0.11)["vend_ok"]
    assert v(vend=0.09)["vend_ok"]
    assert not v(vend=-0.11)["vend_ok"]       # abs
    assert v(vend=-0.09)["vend_ok"]


def test_dz_limit():
    assert not v(dz=0.31)["dz_ok"]
    assert v(dz=0.29)["dz_ok"]
    assert not v(dz=-0.31)["dz_ok"]           # abs (drop vs climb)
    assert v(dz=-0.29)["dz_ok"]


def test_criteria_independent():
    r = v(rms=0.21, vend=0.09, dz=0.29)
    assert (r["rms_ok"], r["vend_ok"], r["dz_ok"]) == (False, True, True), r
    r = v(rms=0.19, vend=0.11, dz=0.29)
    assert (r["rms_ok"], r["vend_ok"], r["dz_ok"]) == (True, False, True), r
    r = v(rms=0.19, vend=0.09, dz=0.31)
    assert (r["rms_ok"], r["vend_ok"], r["dz_ok"]) == (True, True, False), r


def go(att=None, **kw):
    out = run(make(**kw), att)
    return out, LAST_CODE[0]


def test_verdict_and_exit_code():              # S215: S194 checker printed no verdict and never exited non-zero
    out, c = go(rms=0.05, vend=0.02, dz=0.05)
    assert c == 0 and "RESULT PASS" in out, (c, out)
    for kw in ({"rms": 0.21}, {"vend": 0.11}, {"dz": 0.31}):
        out, c = go(**kw)
        assert c == 1 and "RESULT FAIL" in out, (kw, c, out)


def test_loc_tilt_and_height():                # S215: LOC = tilt > 60 deg for > 0.2 s, or height drop > 2 m (GATES LOC)
    out, c = go(att=make_att(70.0, 7.0, 0.3))
    assert c == 1 and "FAIL no_loc" in out and "-> LOC" in out, (c, out)
    out, c = go(att=make_att(70.0, 7.0, 0.1))  # short excursion: not LOC
    assert c == 0, (c, out)
    out, c = go(att=make_att(50.0, 7.0, 1.0))  # below 60 deg: not LOC
    assert c == 0, (c, out)
    out, c = go(dz=-2.1)
    assert c == 1 and "-> LOC" in out, (c, out)
    out, c = go(dz=-1.9)                       # dz limit 0.3 fails, but not LOC
    assert c == 1 and "-> no LOC" in out, (c, out)


def test_never_reaches_90pct():                # S215: argmax of all-False printed 0.00 s
    out, c = go(step_vx=1.0)
    assert "time to 90% of 2 m/s: 0.00" not in out and "never reached" in out, out


def test_final_vx_is_a_mean():                 # S215: one end sample was used
    out, c = go(vend=0.5, vend_last_only=True)  # a single outlier sample among the 50 of the last 1 s: mean 0.01
    assert abs(verdict(out)["vend"] - 0.01) < 1e-3 and c == 0, (c, out)
    out, c = go(vend=0.11)                     # 1 s at 0.11 -> mean 0.11 fails
    assert c == 1 and not verdict(out)["vend_ok"], (c, out)


def test_empty_topic_is_invalid_not_a_crash():  # S215: IndexError
    empty = {k: np.array([]) for k in ("timestamp", "vx", "vy", "z", "x")}
    try:
        out, c = run(empty), LAST_CODE[0]
    except IndexError as e:
        raise AssertionError("IndexError on empty topic: %s" % e)
    assert c == 2 and "INVALID" in out, (c, out)
    out = run(make(), att={k: np.array([]) for k in ("timestamp", "q[0]", "q[1]", "q[2]", "q[3]")})
    assert LAST_CODE[0] == 2 and "INVALID" in out, out


CASES = [test_nominal_passes, test_rms_limit, test_rms_uses_last_3s_only, test_end_vx_limit, test_dz_limit, test_criteria_independent,
         test_verdict_and_exit_code, test_loc_tilt_and_height, test_never_reaches_90pct, test_final_vx_is_a_mean, test_empty_topic_is_invalid_not_a_crash]

# (description, old text, new text) applied to a COPY of the checker; each must make >= 1 case fail
MUTATIONS = [
    ("step reference 2.0 -> 2.1", "vx[m] - 2.0", "vx[m] - 2.1"),
    ("last-3 s window t0+2 -> t0+1 (RMS over 4 s incl. rise)", "err[t[m] > t0 + 2]", "err[t[m] > t0 + 0.5]"),
    ("end-of-hold window start t2 - END_WIN_S -> t1 (whole hold mean)", "(t >= t2 - END_WIN_S)", "(t >= t1)"),
    ("LOC tilt limit 60 -> 80 deg", "LOC_TILT_DEG, LOC_TILT_S, LOC_DROP_M = 60.0", "LOC_TILT_DEG, LOC_TILT_S, LOC_DROP_M = 80.0"),
    ("LOC duration 0.2 s -> 0 s", "LOC_TILT_DEG, LOC_TILT_S, LOC_DROP_M = 60.0, 0.2", "LOC_TILT_DEG, LOC_TILT_S, LOC_DROP_M = 60.0, 0.0"),
    ("exit code of FAIL -> 0", "sys.exit(0 if res else 1)", "sys.exit(0)"),
    ("dz reference offset by +0.1 m", "zref = -gt[\"z\"][zp].mean()", "zref = -gt[\"z\"][zp].mean() + 0.1"),
    ("dz abs dropped", "np.abs(zz - zref).max()", "(zz - zref).max()"),
]


def mutation_detected(old, new):
    src = open(REAL).read()
    assert old in src, "mutation target not found: " + old
    d = tempfile.mkdtemp()
    p = os.path.join(d, "offb_vel_check_mut.py")
    open(p, "w").write(src.replace(old, new, 1))
    CHECKER[0] = p
    try:
        for f in CASES:
            try:
                f()
            except Exception:
                return True
        return False
    finally:
        CHECKER[0] = REAL


def test_mutations_detected():
    missed = [d for d, o, n in MUTATIONS if not mutation_detected(o, n)]
    assert not missed, "undetected mutations: %s" % missed


def main():
    for f in CASES:
        f()
    for d, o, n in MUTATIONS:
        det = mutation_detected(o, n)
        print("mutation %-70s detected=%s" % (d, det))
        assert det, d
    print("test_offb_vel_check OK")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("FAIL", e)
        sys.exit(1)
