#!/usr/bin/env python3
"""Self-test (pure python, no gz) of the airframe-based profile sizing in bench/disturbance.py (N1 C2, T132).

  python3 indi_flight/bench/tests/test_disturbance_sizing.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import disturbance as D  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
X500_SDF = os.path.join(HERE, "..", "..", "..", "Tools", "simulation", "gz", "models", "x500_base", "model.sdf")
Q5_SDF = os.path.join(HERE, "..", "..", "sim", "models", "quad5in_base", "model.sdf")
Q5_TOP = os.path.join(HERE, "..", "..", "sim", "models", "quad5in", "model.sdf")


def peak(fn, af, dur, idx):
    return max(abs(fn(i / 100.0, af)[idx]) for i in range(int(dur * 100)))


def main():
    # both SDFs must be readable here, otherwise load_airframe would silently use the fallback constants
    for p in (X500_SDF, Q5_SDF, Q5_TOP):
        assert os.path.exists(p), p
    x5 = D.load_airframe("x500")
    q5 = D.load_airframe("quad5in")
    assert x5.source.endswith("x500_base/model.sdf") and q5.source.endswith("quad5in_base/model.sdf"), (x5.source, q5.source)
    print(f"x500 mass {x5.mass:.4f} kg, quad5in mass {q5.mass:.4f} kg")
    assert abs(x5.mass - D.X500_MASS_KG) < 1e-9
    assert 0.5 <= q5.mass <= 0.7
    # quad5in/model.sdf must be the include of quad5in_base with no mass of its own
    top = open(Q5_TOP).read()
    assert "model://quad5in_base" in top and "<mass>" not in top
    # fallback constants == SDF
    for n, af in (("x500", x5), ("quad5in", q5)):
        fm, fi = D.AIRFRAMES[n]["fallback"]
        assert abs(fm - af.mass) < 1e-9 and all(abs(a - b) < 1e-12 for a, b in zip(fi, af.inertia)), n
    assert D.airframe_from_model("x500_0") == "x500" and D.airframe_from_model("quad5in_0") == "quad5in"

    # x500 reproduces the old numbers
    old_cdrag = 0.5 * 1.225 * 0.06
    assert abs(x5.c_drag - old_cdrag) < 1e-12 and x5.cop_z == 0.05
    assert abs(D.payload_add(1.0, x5)[2] + 0.25 * D.X500_MASS_KG * 9.8) < 1e-9
    assert abs(D.com_shift(1.0, x5)[2] + 0.15 * D.X500_MASS_KG * 9.8) < 1e-9
    assert abs(D.gust_x(2.0 + 10.0 + 0.5, x5)[0] - old_cdrag * 9.0 * 9.0) < 1e-9  # gust peak 9 m/s

    # payload / com_shift: same fraction of weight on both airframes
    for name, fn, frac in (("payload_add", D.payload_add, 0.25), ("com_shift", D.com_shift, 0.15)):
        for af in (x5, q5):
            r = peak(fn, af, 5.0, 2) / (af.mass * D.GRAVITY)
            assert abs(r - frac) < 1e-9, (name, af.name, r)
            print(f"{name:12s} {af.name:8s} peak Fz/weight = {r:.3f}")
    assert abs(D.com_shift(1.0, q5)[3] - D.SHIFT_Y * D.com_shift(1.0, q5)[2]) < 1e-12

    # gusts: drag/weight is airframe-specific by design (CdA follows frame area, not mass)
    for name, fn, dur in (("gust_x", D.gust_x, D.GUST_DURATION), ("gust_diag", D.gust_diag, D.DIAG_DURATION)):
        rs = {}
        for af in (x5, q5):
            f = max(math.hypot(*fn(i / 100.0, af)[:2]) for i in range(int(dur * 100)))
            rs[af.name] = f / (af.mass * D.GRAVITY)
            print(f"{name:12s} {af.name:8s} peak |Fxy| = {f:.3f} N = {rs[af.name]:.3f} weight")
        assert 0.05 <= rs["quad5in"] <= 0.25, rs
    assert peak(D.gust_x, q5, D.GUST_DURATION, 0) < 0.3 * peak(D.gust_x, x5, D.GUST_DURATION, 0)

    # torque steps: same angular-acceleration step on both airframes, quad5in numbers unchanged
    for k, ref in enumerate((0.10, 0.10, 0.03)):
        t_mid = (0.0, 4.0, 8.0)[k] + 1.0
        tq_q5 = D.torque_steps(t_mid, q5)[3 + k]
        tq_x5 = D.torque_steps(t_mid, x5)[3 + k]
        assert abs(tq_q5 - ref) < 1e-12, (k, tq_q5)
        assert abs(tq_x5 / x5.inertia[k] - tq_q5 / q5.inertia[k]) < 1e-9
        print(f"torque_steps axis {k}: quad5in {tq_q5:.4f} N m ({tq_q5 / q5.inertia[k]:.1f} rad/s2), x500 {tq_x5:.4f} N m")
    print("OK")


if __name__ == "__main__":
    main()
