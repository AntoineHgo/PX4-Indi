#!/usr/bin/env python3
"""Self-test of bench/passthrough_check.py on synthetic logs with known answers (G7 checker self-test, S194).

  python3 -I indi_flight/bench/tests/test_passthrough_check.py     (numpy only; exit 0 = pass, 1 = failure)

The checker is a print-only script (no verdict). Its pass criterion (design/impl_s133_offboard_passthrough.md, ACRO row):
the pass-through window (pos/vel/alt control flags all off) exists, and 0 vehicle_attitude_setpoint samples and 0
indi_pos_status samples fall inside it. pyulog is replaced by a fake module, the script is run with runpy, the printed
counts are parsed and judged here. Mutation checks run the cases against mutated COPIES of the checker.
"""
import contextlib
import io
import os
import re
import runpy
import sys
import tempfile
import types

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REAL = os.path.join(HERE, "..", "passthrough_check.py")
CHECKER = [REAL]
T_OFF0, T_OFF1 = 5.0, 15.0     # pos/vel/alt all off in [5, 15)


def us(t):
    return (np.asarray(t) * 1e6).astype(np.uint64)


def make(att_in_off=(), pos_in_off=(), always_off=False, drop_pos=False, keep_on=None):
    """Control mode at 100 Hz over 0..20 s. att_sp / indi_pos_status at 50 Hz outside the off window plus the given
    extra sample times (placed inside the window)."""
    tc = np.arange(0.0, 20.0, 0.01)
    off = np.ones(tc.size, bool) if always_off else (tc >= T_OFF0) & (tc < T_OFF1)
    on = ~off
    vc = {"timestamp": us(tc)}
    for f in ("flag_control_position_enabled", "flag_control_velocity_enabled", "flag_control_altitude_enabled"):
        vc[f] = on.copy()
    if keep_on:                             # e.g. altctl/velocity-only: that flag stays on, so not pass-through
        vc[keep_on] = np.ones(tc.size, bool)
    vc["flag_control_attitude_enabled"] = np.ones(tc.size, bool)
    ts = np.arange(0.005, 20.0, 0.02)       # off the control-mode sample grid
    ts_on = ts[(ts < T_OFF0) | (ts >= T_OFF1)] if not always_off else ts[:0]
    att = np.sort(np.concatenate([ts_on, np.asarray(att_in_off, float)]))
    pos = np.sort(np.concatenate([ts_on, np.asarray(pos_in_off, float)]))
    L = {"vehicle_control_mode": vc,
         "vehicle_status": {"timestamp": us(tc), "nav_state": np.full(tc.size, 14, np.uint8)},
         "vehicle_attitude_setpoint": {"timestamp": us(att)}}
    if not drop_pos:
        L["indi_pos_status"] = {"timestamp": us(pos)}
    return L


def run(logs):
    fake = types.ModuleType("pyulog")

    class ULog:
        def __init__(self, *a, **k):
            self.data_list = [types.SimpleNamespace(name=n, data=d, multi_id=0) for n, d in logs.items()]
    fake.ULog = ULog
    old_mod, old_argv = sys.modules.get("pyulog"), sys.argv
    sys.modules["pyulog"], sys.argv = fake, [CHECKER[0], "x.ulg"]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            runpy.run_path(CHECKER[0], run_name="__main__")
    finally:
        sys.argv = old_argv
        if old_mod is None:
            del sys.modules["pyulog"]
        else:
            sys.modules["pyulog"] = old_mod
    return buf.getvalue()


def verdict(out):
    off, n = map(int, re.search(r"all-three-off: (\d+) of (\d+)", out).groups())
    att = int(re.search(r"att_sp samples while pos/vel/alt all off: (\d+) of", out).group(1))
    m = re.search(r"indi_pos_status samples while all off: (\d+) of", out)
    pos = int(m.group(1)) if m else None
    return {"off": off, "n": n, "att": att, "pos": pos, "ok": off > 0 and att == 0 and pos == 0}


def v(**kw):
    return verdict(run(make(**kw)))


def test_nominal_passes():
    r = v()
    assert r["off"] == 1000 and r["n"] == 2000 and r["att"] == 0 and r["pos"] == 0 and r["ok"], r


def test_att_sp_in_window_fails():
    assert not v(att_in_off=[10.005])["ok"]                 # one sample just beyond (limit is 0)
    r = v(att_in_off=[6.005, 7.005, 8.005])
    assert r["att"] == 3 and not r["ok"], r
    assert v(att_in_off=[])["ok"]                           # just inside: zero samples


def test_pos_status_in_window_fails():
    r = v(pos_in_off=[10.005])
    assert r["pos"] == 1 and r["att"] == 0 and not r["ok"], r
    r = v(pos_in_off=[6.005, 7.005])
    assert r["pos"] == 2 and not r["ok"], r


def test_window_edges():
    # control mode flips to off at exactly 5.00 s and back on at exactly 15.00 s
    assert v(att_in_off=[5.0])["att"] == 1                  # at the first off sample: counted
    assert v(att_in_off=[4.995])["att"] == 0                # just before: still on
    assert v(att_in_off=[14.995])["att"] == 1               # just before the on-edge: counted
    assert v(att_in_off=[15.0])["att"] == 0                 # at the on-edge: on


def test_no_window_is_not_a_pass():
    # flags never all-off (pass-through mode never engaged): 0 samples while off must not be read as a pass
    logs = make()
    for f in ("flag_control_position_enabled", "flag_control_velocity_enabled", "flag_control_altitude_enabled"):
        logs["vehicle_control_mode"][f] = np.ones(2000, bool)
    r = verdict(run(logs))
    assert r["off"] == 0 and not r["ok"], r


def test_any_single_flag_blocks_window():
    for f in ("flag_control_position_enabled", "flag_control_velocity_enabled", "flag_control_altitude_enabled"):
        logs = make(keep_on=f)
        logs["vehicle_attitude_setpoint"]["timestamp"] = us(np.arange(6.005, 9.0, 0.02))   # att_sp flowing in the window
        r = verdict(run(logs))
        assert r["off"] == 0 and r["att"] == 0 and not r["ok"], (f, r)


def test_whole_run_off_counts_everything():
    r = v(always_off=True, att_in_off=[1.0, 2.0], pos_in_off=[3.0])
    assert r["off"] == r["n"] == 2000 and r["att"] == 2 and not r["ok"], r


def test_absent_status_reported():
    out = run(make(drop_pos=True))
    assert "indi_pos_status ABSENT" in out and verdict(out)["pos"] is None, out


CASES = [test_nominal_passes, test_att_sp_in_window_fails, test_pos_status_in_window_fails, test_window_edges,
         test_no_window_is_not_a_pass, test_any_single_flag_blocks_window, test_whole_run_off_counts_everything, test_absent_status_reported]

MUTATIONS = [
    ("off = ~pv -> off = pv (inverted window)", "off = ~pv", "off = pv"),
    ("att_sp window lookup side=right -> left", "idx = np.searchsorted(t, ts, side=\"right\") - 1\n    idx = np.clip(idx, 0, len(t) - 1)\n    print(\"att_sp", "idx = np.searchsorted(t, ts, side=\"left\") - 1\n    idx = np.clip(idx, 0, len(t) - 1)\n    print(\"att_sp"),
    ("pos/vel/alt OR -> only position flag", "pv = (vc[\"flag_control_position_enabled\"] | vc[\"flag_control_velocity_enabled\"] | vc[\"flag_control_altitude_enabled\"])", "pv = (vc[\"flag_control_position_enabled\"])"),
    ("indi_pos_status count uses att_sp mask index shifted +1000", "int(off[idx].sum()), \"of\", len(ts))\n", "int(off[np.clip(idx + 1000, 0, len(t) - 1)].sum()), \"of\", len(ts))\n"),
]


def mutation_detected(old, new):
    src = open(REAL).read()
    assert old in src, "mutation target not found: " + old
    d = tempfile.mkdtemp()
    p = os.path.join(d, "passthrough_check_mut.py")
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
        print("mutation %-62s detected=%s" % (d, det))
        assert det, d
    print("test_passthrough_check OK")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as e:
        print("FAIL", e)
        sys.exit(1)
