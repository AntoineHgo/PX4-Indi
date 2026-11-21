#!/usr/bin/env python3
"""Self-test for indi_flight/bench/g3_checks.py on synthetic truth with known answers.

  python3 indi_flight/bench/tests/test_g3_checks.py [--break-check]
--break-check (lesson 20): blinds each detector once (threshold patched) and requires the matching case to FAIL.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g3_checks as G  # noqa: E402

FS, T = 800.0, 90.0
T0, T1 = 40.0, 50.0


def make(osc_hz=None, osc_dps=0.0, alt_off=0.0, tilt_deg=0.0, line_hz=None, pos_lc=0.0, land_at=None, seed=0, osc_from=0.0, land_rate=1.0):
    rng = np.random.default_rng(seed)
    t = np.arange(0, T, 1 / FS)
    n = len(t)
    h = np.minimum(t / 5.0, 1.0) * 5.0 + alt_off * (t > 30)          # climb 1 m/s to 5 m then hold
    pos = np.stack([rng.normal(0, 0.02, n), rng.normal(0, 0.02, n), -h], axis=1)
    pos[:, 2][t < 0.5] = 0.0
    pos[:, 0] += pos_lc * np.sin(2 * np.pi * 0.5 * t) * (t > 10)
    if land_at:
        h = np.where(t > land_at, np.maximum(5.0 - land_rate * (t - land_at), 0.0), h)
        pos[:, 2] = -h
    th = np.zeros(n)
    if tilt_deg:
        th[(t > 20) & (t < 20.5)] = np.radians(tilt_deg)               # 0.5 s tilt about the body x axis
    q = np.stack([np.cos(th / 2), np.sin(th / 2), np.zeros(n), np.zeros(n)], axis=1)
    w = np.radians(1.0) * rng.normal(size=(n, 3))
    if osc_hz:
        w[:, 0] += np.radians(osc_dps) * np.sqrt(2) * np.sin(2 * np.pi * osc_hz * t) * (t > osc_from)   # osc_dps = RMS
    cmd = 0.5 + 0.002 * rng.normal(size=(n, 4))
    if line_hz:
        cmd += 0.02 * np.sin(2 * np.pi * line_hz * t)[:, None]
    ref = np.array([0.0, 0.0, -5.0])
    return G.evaluate(t, pos, q, w, t, cmd, ref, T0, T1, t_land=land_at)


def main():
    brk = "--break-check" in sys.argv
    cases = {
        "clean": (dict(), dict(p=True)),
        "osc30": (dict(osc_hz=30.0, osc_dps=8.0), dict(item2=False)),
        "osc30_4dps": (dict(osc_hz=30.0, osc_dps=4.0), dict(item2=True)),
        "chatter60": (dict(line_hz=60.0), dict(item2=False)),
        "poslc": (dict(pos_lc=0.2), dict(item2=False)),
        "landing": (dict(land_at=70.0), dict(p=True)),
        "osc_in_land": (dict(land_at=70.0, land_rate=0.5, osc_hz=30.0, osc_dps=8.0, osc_from=70.0), dict(item2=False)),  # D-G3-SPAN
        "alt_off": (dict(alt_off=0.2), dict(item3=False)),
        "loc": (dict(tilt_deg=80.0), dict(item1=False)),
    }
    patches = {"osc30": ("RMS_DEG_S", 1e9), "osc_in_land": ("RMS_DEG_S", 1e9), "chatter60": None, "poslc": ("POS_P2P_M", 9.0),
               "alt_off": ("ALT_MEAN", (9.0, 9.0)), "loc": ("TILT_DEG", 179.0)}
    out, bad = {}, 0
    for name, (kw, exp) in cases.items():
        r = None
        if brk:
            if name not in patches:
                continue
            saved = {}
            if name == "chatter60":
                saved["CMD_BAND"] = G.CMD_BAND
                G.CMD_BAND = (100.0, 150.0)       # detector looks at the wrong band: blind to the 60 Hz line
            else:
                k, v = patches[name]
                saved[k] = getattr(G, k)
                setattr(G, k, v)
            r = make(**kw)
            for k, v in saved.items():
                setattr(G, k, v)
        else:
            r = make(**kw)
        got = {"item1": r["item1_loc"]["pass"], "item2": r["item2_oscillation"]["pass"], "item3": r["item3_steady_state"]["pass"], "p": r["pass"]}
        ok = all(got[k] == v for k, v in exp.items())
        if name == "osc30_4dps":
            ok = ok and not r["item2_oscillation"]["q"]["sustained"]
        if name == "chatter60":
            ok = ok and r["item2_oscillation"]["command_chatter"]["sustained"]
        if name == "poslc":
            ok = ok and r["item2_oscillation"]["position"]["sustained"]
        if brk:
            print(f"break-check {name}: case {'STILL FAILS DETECTION (BAD)' if ok else 'passes expectation-miss (break caught)'}")
            bad += ok
        else:
            print(f"selftest {name}: {got} {'OK' if ok else 'FAIL'}")
            bad += not ok
    print(("break-check " if brk else "selftest ") + ("PASS" if not bad else "FAIL"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
