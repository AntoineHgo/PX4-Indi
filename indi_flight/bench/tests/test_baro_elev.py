#!/usr/bin/env python3
"""A-14 check: mirrors GZBridge::airPressureCallback re-expression of gz pressure at world elevation."""
import math

P0, T0, L = 101325.0, 288.15, 0.0065
K = 9.80665 * 0.0289644 / (8.31432 * 0.0065)  # same constant as ISA_EXPONENT in GZBridge.cpp


def isa_p(h):
    return P0 * (1.0 - L * h / T0) ** K


def isa_h(p):
    return (T0 / L) * (1.0 - (p / P0) ** (1.0 / K))


def remap(p_gz, elev):
    return isa_p(isa_h(p_gz) + elev)


def main():
    assert abs(K - 5.2559) < 1e-3, K
    # ground at local 0 m, world elevation 488 m
    p = remap(P0, 488.0)
    assert abs(p - 95599.0) < 5.0, p
    # zero elevation is the identity
    for h in (-50, 0, 5, 100, 1000):
        assert abs(remap(isa_p(h), 0.0) - isa_p(h)) < 1e-6
    # round trip: remap then inverse gives local + elev, and local altitude is recovered
    for elev in (0.0, 100.0, 488.0, 2000.0):
        for h in (0.0, 1.0, 5.0, 50.0, 300.0):
            p_out = remap(isa_p(h), elev)
            assert abs(p_out - isa_p(h + elev)) < 1e-6
            assert abs(isa_h(p_out) - (h + elev)) < 1e-6
            assert abs((isa_h(p_out) - elev) - h) < 1e-6
    # derivative near 488 m
    d = (remap(isa_p(1.0), 488.0) - remap(isa_p(-1.0), 488.0)) / 2.0
    assert abs(d - (-11.3)) < 0.3, d
    # noise: a 1 Pa perturbation maps to ~(dP/dh at 488)/(dP/dh at 0) Pa
    n = remap(P0 - 1.0, 488.0) - remap(P0, 488.0)
    assert -1.0 < n < 0.0 and abs(n - (-0.944)) < 0.01, n
    print("ok: P(0m,488m)=%.1f Pa dP/dz=%.2f Pa/m noise gain=%.3f" % (p, d, -n))


if __name__ == "__main__":
    main()
