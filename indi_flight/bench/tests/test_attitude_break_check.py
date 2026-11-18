#!/usr/bin/env python3
"""Synthetic self-test of bench/attitude_break_check.py (arrays only, no ulog).

  python3 -I indi_flight/bench/tests/test_attitude_break_check.py      (numpy only; exit 0 = pass, 1 = failure)

Known-good log: a closed rate loop whose law is fed x = y + d, rate_sp_dot = filtered derivative of x as the library
does. Bad log: same loop and same logged x, but the law got the un-injected y (the call-site bug), or d was applied
after the law. Both must FAIL.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import attitude_break_check as ab  # noqa: E402

DT = 0.0025
TP = 10.0
NP = 3


def multisine(t, fmin=0.2, fmax=20.0, amp=0.05):
    ks = np.unique(np.round(np.logspace(np.log10(fmin), np.log10(fmax), 21) * TP)).astype(int)
    ph = -2 * np.pi * np.array([sum((k - l) / len(ks) for l in range(k)) for k in range(len(ks))])
    return sum(amp * np.cos(2 * np.pi * (k / TP) * t + p) for k, p in zip(ks, ph))


def make(law_gets):
    """law_gets: 'x' (good), 'y' (law never saw d)."""
    n = int((NP * TP + 4) / DT)
    t = np.arange(n) * DT
    rng = np.random.default_rng(1)
    d = np.where((t >= 2) & (t < 2 + NP * TP), multisine(t - 2), 0.0)
    y = 0.3 * np.sin(2 * np.pi * 0.05 * t)         # attitude loop output, slow
    y = y[0::1]
    x = y + d
    fed = x if law_gets == "x" else y
    r = np.zeros(n)
    c = np.zeros(n)
    rdot = np.zeros(n)
    a = DT / (ab.K_TC + DT)
    for k in range(1, n):
        rdot[k] = np.clip(rdot[k - 1] + a * ((fed[k] - fed[k - 1]) / DT - rdot[k - 1]), -ab.K_MAX_DOT, ab.K_MAX_DOT)
        c[k] = 0.6 * (fed[k] - r[k - 1]) + 0.01 * rdot[k] + 1e-4 * rng.standard_normal()
        r[k] = r[k - 1] + DT * (-5.0 * r[k - 1] + 30.0 * c[k])
    f32 = lambda v: v.astype(np.float32).astype(float)  # noqa: E731
    return dict(t_us=np.round(t * 1e6).astype(np.int64) + 5_000_000, d=f32(d), x=f32(x), y=f32(y), rdot=f32(rdot),
                c=f32(c), fault=np.zeros(n, bool), stale=np.zeros(n, bool))


def run(S, axis=1):
    return {name: v for name, v, _ in ab.analyse(S, axis, TP, 0.2, 20.0)}


def main():
    bad = 0

    def expect(label, cond):
        nonlocal bad
        print(("ok   " if cond else "FAIL ") + label)
        bad += 0 if cond else 1

    good = run(make("x"))
    expect("good log: all PASS", all(v == "PASS" for v in good.values()))
    ys = run(make("y"))
    expect("law fed y: rate_sp_dot check FAILS", ys["law fed x: rate_sp_dot"] == "FAIL")
    expect("law fed y: response check FAILS", ys["law fed x: c responds at excited bins"] == "FAIL")
    expect("law fed y: the circular check still passes (that is why it is not enough)",
           ys["consistency x-y-d (circular, informative)"] == "PASS")
    S = make("x")
    S["fault"][5000] = True
    expect("fault inside the window FAILS", run(S)["window"] == "FAIL")
    expect("yaw: lead check SKIP", run(make("x"), axis=2)["law fed x: rate_sp_dot"] == "SKIP")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
