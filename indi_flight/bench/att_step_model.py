#!/usr/bin/env python3
"""Linear prediction of the 15 deg attitude step under the INDI rate loop (S61, N1 item B).

  python3 att_step_model.py      -> calibration of the inner actuator model, then overshoot / 2 % settle for
                                    variants (P_att, K_R, rate-setpoint-derivative feedforward with filter tau_ff).
Inner: omega_dot = H nu, H = e^{-d s}/(tau_a s + 1); nu = K_R (r - omega) [+ r_dot filtered]. Outer: r = P (theta_sp - theta).
tau_a, d are fitted so that the K_R = 20 closed rate loop matches the flight fit (first order 80 ms + 22 ms delay,
bench/rate_fit.py on results/indi_vs_pid/step_roll_indi).
"""
import numpy as np

DT = 1 / 800.0


def sim(P, KR, tau_a, d, ff=False, tau_ff=0.01, mode="att", T=2.0, amp=np.radians(15), tau_c=0.0, kff=None):
    n = int(T / DT); nd = int(round(d / DT))
    th = om = a = 0.0; buf = [0.0] * (nd + 1); r_prev = 0.0; rdf = 0.0
    out = np.zeros(n)
    for i in range(n):
        r = P * (amp - th) if mode == "att" else amp
        rd = (r - r_prev) / DT if i > 0 else 0.0
        r_prev = r
        rdf += DT / tau_ff * (rd - rdf)
        # lead (D-RATE-LEAD): - K tau_c a (a = achieved accel); ff: kff * filtered r_dot (default 1, i.e. full r_dot)
        nu = KR * (r - om) - KR * tau_c * a + ((1.0 if kff is None else kff) * rdf if ff else 0.0)
        buf.append(nu); nu_d = buf.pop(0)
        a += DT / tau_a * (nu_d - a)
        om += DT * a; th += DT * om
        out[i] = th if mode == "att" else om
    return out


def metrics(y, amp):
    t = np.arange(len(y)) * DT
    os_ = max(0.0, (y.max() - amp) / amp * 100)
    outside = np.where(np.abs(y - amp) > 0.02 * amp)[0]
    settle = t[outside[-1] + 1] * 1e3 if len(outside) else 0.0
    return os_, settle


def fit_fopdt(y, amp):
    t = np.arange(len(y)) * DT; best = None
    for tau in np.arange(0.02, 0.2, 0.002):
        for dd in np.arange(0.0, 0.05, 0.001):
            m = np.where(t > dd, amp * (1 - np.exp(-(t - dd) / tau)), 0.0)
            e = np.mean((m - y) ** 2)
            if best is None or e < best[0]:
                best = (e, tau, dd)
    return best[1], best[2]


def lead_table():
    """S61: plant tau 33 ms, lead tau_c 50 ms (defaults), pure delay d; overshoot/settle for the ff variants."""
    amp = np.radians(15)
    for d in (0.010, 0.020):
        for name, ff, kff in [("no ff (as flown)", False, 0), ("setpoint lead kff=K tau_c", True, 20 * 0.05),
                              ("full r_dot kff=1+K tau_c", True, 1 + 20 * 0.05)]:
            y = sim(8, 20, 0.033, d, ff, 0.01, T=3.0, tau_c=0.05, kff=kff)
            o, st = metrics(y, amp)
            print(f"d {d*1e3:.0f} ms {name:27}: overshoot {o:5.1f} %, settle {st:5.0f} ms")
        yr = sim(0, 20, 0.033, d, mode="rate", T=0.6, amp=1.0, tau_c=0.05)
        print(f"   closed rate loop no ff fits {[round(v*1e3) for v in fit_fopdt(yr, 1.0)]} ms (tau, delay)")


if __name__ == "__main__" and len(__import__("sys").argv) > 1:
    lead_table()
elif __name__ == "__main__":
    best = None
    for tau_a in np.arange(0.01, 0.06, 0.005):
        for d in np.arange(0.0, 0.03, 0.0025):
            y = sim(0, 20, tau_a, d, mode="rate", T=0.6, amp=1.0)
            ft, fd = fit_fopdt(y, 1.0)
            e = (ft - 0.080) ** 2 + (fd - 0.022) ** 2
            if best is None or e < best[0]:
                best = (e, tau_a, d, ft, fd)
    _, TA, D, ft, fd = best
    print(f"calibrated inner: tau_a {TA*1e3:.0f} ms, d {D*1e3:.1f} ms -> closed rate loop fits {ft*1e3:.0f} ms + {fd*1e3:.0f} ms")
    amp = np.radians(15)
    for P, KR, ff, tff in [(8, 20, False, 0.01), (8, 20, True, 0.005), (8, 20, True, 0.02), (8, 20, True, 0.05),
                           (8, 30, False, 0.01), (8, 40, False, 0.01), (8, 30, True, 0.02), (5, 20, False, 0.01)]:
        o, s = metrics(sim(P, KR, TA, D, ff, tff, T=3.0), amp)
        print(f"P {P} K_R {KR} ff {ff!s:5} tau_ff {tff*1e3:3.0f} ms: overshoot {o:5.1f} %, settle {s:5.0f} ms")
