#!/usr/bin/env python3
"""T124: independent second-key simulation of the single-axis INDI attitude-step model.

Model (continuous time, simulated with fixed-step explicit Euler, dt = 1/800 s):
  tau_a * da/dt = nu(t - d) - a            (actuator with pure delay d)
  d(omega)/dt = a,  d(theta)/dt = omega    (body)
  nu = K*(r - omega) - K*tau_c*a + kff*rdot_f
  rdot_f = (r - rf)/tau_f, with rf the first-order low-pass of r (tau_f = 0.01 s)
  r = P*(theta_sp - theta), P = 8, theta_sp = 15 deg step at t = 0
"""
import numpy as np

TAU_A = 0.033
TAU_C = 0.05
K = 20.0
TAU_F = 0.01
P = 8.0
THSP = np.deg2rad(15.0)


def run(kff, d, dt=1.0 / 800.0, T=3.0, tau_c=TAU_C, P=P, r_fixed=None):
    """Simulate; returns t [s], theta [deg], omega [rad/s], a [rad/s^2]."""
    n = int(round(T / dt))
    nd = int(round(d / dt))
    nu_hist = np.zeros(n)
    th = np.zeros(n + 1)
    om = np.zeros(n + 1)
    a = np.zeros(n + 1)
    rf = 0.0
    for k in range(n):
        r = r_fixed if r_fixed is not None else P * (THSP - th[k])
        rdot = (r - rf) / TAU_F
        nu = K * (r - om[k]) - K * tau_c * a[k] + kff * rdot
        nu_hist[k] = nu
        u = nu_hist[k - nd] if k >= nd else 0.0
        a[k + 1] = a[k] + dt * (u - a[k]) / TAU_A
        om[k + 1] = om[k] + dt * a[k]
        th[k + 1] = th[k] + dt * om[k]
        rf += dt * rdot
    t = np.arange(n + 1) * dt
    return t, np.rad2deg(th), om, a


def metrics(t, thd):
    peak = thd.max()
    overshoot = (peak - 15.0) / 15.0 * 100.0
    out = np.nonzero(np.abs(thd - 15.0) > 0.3)[0]
    ts = t[out[-1]] if out.size else 0.0
    unsettled = out.size > 0 and out[-1] == len(t) - 1
    return overshoot, ts, t[np.argmax(thd)], peak, unsettled


if __name__ == "__main__":
    print("== Rate-loop poles, kff=0, P=0, d=0 (tau_a s^2 + (1+K tau_c) s + K = 0) ==")
    A = np.array([[0.0, 1.0], [-K / TAU_A, -(1.0 + K * TAU_C) / TAU_A]])
    print("monic char poly coeffs [1, (1+K tau_c)/tau_a, K/tau_a]:", np.poly(A))
    rts = np.linalg.eigvals(A)
    print("roots [1/s]:", rts)
    print("dominant time constant 1/|Re| = %.4f s" % (1.0 / min(abs(rts.real))))
    print()

    cases = [(0.0, "kff=0"), (K * TAU_C, "kff=1"), (1.0 + K * TAU_C, "kff=2")]
    print("== Attitude step, P=8, 15 deg ==")
    print("%-6s %-6s %-10s %-10s %-10s %-10s %-8s" % ("d[s]", "case", "OS[%]", "ts2%[s]", "t_peak[s]", "peak[deg]", "unsett"))
    for d in (0.010, 0.020):
        for kff, name in cases:
            t, thd, _, _ = run(kff, d)
            os_pct, ts, tp, peak, uns = metrics(t, thd)
            print("%-6.3f %-6s %-10.2f %-10.3f %-10.3f %-10.2f %-8s" % (d, name, os_pct, ts, tp, peak, uns))
    print()

    print("== Convergence check: dt = 1/3200 vs 1/800 (OS and ts) ==")
    for d in (0.010, 0.020):
        for kff, name in cases:
            t, thd, _, _ = run(kff, d, dt=1.0 / 3200.0)
            os_pct, ts, _, _, _ = metrics(t, thd)
            print("d=%.3f %-6s OS=%.2f%%  ts=%.3f s" % (d, name, os_pct, ts))
    print()

    print("== Analytic rate-loop check: d=0, tau_c=tau_a, kff=K*tau_a ==")
    Ta = TAU_A
    num = K * np.array([Ta + TAU_F, 1.0])  # K((Ta+Tf) s + 1)
    den = np.polymul(np.polymul([TAU_F, 1.0], [Ta, 1.0]), [1.0, K])  # (Tf s+1)(Ta s+1)(s+K)
    print("zeros:", np.roots(num), " poles:", np.roots(den))
    print("DC gain:", num[-1] / den[-1])
    print("no-filter quadratic Ta s^2+(1+K Ta)s+K roots:", np.roots([Ta, 1.0 + K * Ta, K]))

    # Independent check: RK4 on the canonical realization of the analytic TF vs the Euler sim
    c3 = den[0]
    a2, a1, a0 = den[1] / c3, den[2] / c3, den[3] / c3
    b1, b0 = num[0] / c3, num[1] / c3
    Am = np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [-a0, -a1, -a2]])
    Bm = np.array([0.0, 0.0, 1.0])
    Cm = np.array([b0, b1, 0.0])
    t, _, om_sim, _ = run(K * Ta, 0.0, tau_c=Ta, r_fixed=1.0)
    h = t[1] - t[0]
    x = np.zeros(3)
    y = [0.0]
    f = lambda x: Am @ x + Bm  # unit step input
    for _ in range(len(t) - 1):
        k1 = f(x)
        k2 = f(x + 0.5 * h * k1)
        k3 = f(x + 0.5 * h * k2)
        k4 = f(x + h * k3)
        x = x + h / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)
        y.append(Cm @ x)
    y = np.array(y)
    print("omega step response (r=1 rad/s): max |sim - analytic| = %.2e rad/s" % np.max(np.abs(om_sim - y)))
    for tq in (0.02, 0.05, 0.2, 1.0):
        i = int(round(tq / h))
        print("  t=%.2f  sim=%.5f  analytic=%.5f" % (t[i], om_sim[i], y[i]))
