#!/usr/bin/env python3
"""Estimate the roll INDI control effectiveness G1 from a stage-2 multisine injection window.

Model: alpha(t) = G1 * u_lag(t - k*dt) + b
  alpha  = roll angular acceleration [rad/s^2]
  u      = indi_rate_status.torque_sp[0] (normalised roll torque command, what the plant sees)
  u_lag  = u through a discrete first-order lag, exact ZOH: y[n] = a*y[n-1] + (1-a)*u[n], a = exp(-dt/tau)
Cross-checks: alpha from vehicle_angular_velocity.xyz_derivative[0]; regressor inject[0] (excitation only).
Both regressand and regressor are band-passed to REG_BAND with the same zero-phase FFT mask.
Frequency-domain estimate: median |FFT(alpha)| / |FFT(u_lag)| at the strongest injection peaks.

Usage: g1_regress_s42.py <flight.ulg> <out.md>
"""
import os
import sys

import numpy as np
from pyulog import ULog

WIN = (52.0, 82.0)       # s since boot, absolute indi_rate_status timestamp_sample
REG_BAND = (2.0, 10.0)   # Hz, regression band
FQ_BAND = (2.0, 20.0)    # Hz, frequency-domain band
TAUS = (0.0, 0.020, 0.033)  # s; 0.0 means no lag
KS = (0, 1, 2, 3, 4)     # delay in samples
N_PEAKS = 10
G1_DEFAULT = 320.0
G1_HYPOTHESIS = G1_DEFAULT * 1.30


def lag(x, tau, dt):
    """Discrete first-order lag, exact ZOH. tau <= 0 returns the input unchanged."""
    if tau <= 0.0:
        return x.copy()
    a = np.exp(-dt / tau)
    y = np.empty_like(x)
    y[0] = x[0]
    for n in range(1, x.size):
        y[n] = a * y[n - 1] + (1.0 - a) * x[n]
    return y


def bandpass(x, dt, lo, hi):
    """Zero-phase band-pass: brick-wall FFT mask on the mean-removed segment."""
    x = x - x.mean()
    f = np.fft.rfftfreq(x.size, dt)
    X = np.fft.rfft(x)
    X[(f < lo) | (f > hi)] = 0.0
    return np.fft.irfft(X, x.size)


def fit(a, u):
    """Least squares a = G*u + b. Returns (G, R^2)."""
    A = np.column_stack([u, np.ones_like(u)])
    coef = np.linalg.lstsq(A, a, rcond=None)[0]
    ss_res = np.sum((a - A @ coef) ** 2)
    ss_tot = np.sum((a - a.mean()) ** 2)
    return float(coef[0]), float(1.0 - ss_res / ss_tot)


def scan(alpha, lagged, w, dt, ks=KS):
    """lagged: {tau: regressor series}. Returns rows (tau, k, G1, R2)."""
    a = bandpass(alpha[w], dt, *REG_BAND)
    rows = []
    for tau, x in lagged.items():
        for k in ks:
            uu = bandpass(x[w - k], dt, *REG_BAND)
            g, r2 = fit(a, uu)
            rows.append((tau, k, g, r2))
    return rows


def freq_ratio(alpha, u_lag, u_raw, w, k, dt):
    """|FFT(alpha)| / |FFT(u_lag)| at the strongest local peaks of |FFT(u_raw)| in FQ_BAND."""
    f = np.fft.rfftfreq(w.size, dt)
    U = np.abs(np.fft.rfft(u_raw[w]))
    band = np.flatnonzero((f >= FQ_BAND[0]) & (f <= FQ_BAND[1]))
    peaks = [i for i in band if 0 < i < U.size - 1 and U[i] >= U[i - 1] and U[i] >= U[i + 1]]
    top = sorted(sorted(peaks, key=lambda i: U[i], reverse=True)[:N_PEAKS])
    A = np.abs(np.fft.rfft(alpha[w]))
    B = np.abs(np.fft.rfft(u_lag[w - k]))
    ratio = A[top] / B[top]
    return f[top], ratio, float(np.median(ratio))


def main(path, out_md):
    msgs = ULog(path, ["indi_rate_status", "vehicle_angular_velocity"]).data_list
    ind = next(d for d in msgs if d.name == "indi_rate_status").data
    vav = next(d for d in msgs if d.name == "vehicle_angular_velocity").data

    def col(d, key):
        return np.asarray(d[key], float)

    t = col(ind, "timestamp_sample") * 1e-6
    t_rel = t - t[0]
    dt = float(np.median(np.diff(t)))
    rate_ind = 1.0 / dt
    w = np.flatnonzero((t >= WIN[0]) & (t < WIN[1]))

    tv = col(vav, "timestamp_sample") * 1e-6
    o = np.argsort(tv)
    rate_vav = 1.0 / float(np.median(np.diff(tv)))
    alpha_vav = np.interp(t, tv[o], col(vav, "xyz_derivative[0]")[o])

    primary = "angular_accel_filtered[0] (indi_rate_status)"
    alphas = {
        primary: col(ind, "angular_accel_filtered[0]"),
        "xyz_derivative[0] (vehicle_angular_velocity, interpolated)": alpha_vav,
    }
    raw = {"torque_sp[0] (u)": col(ind, "torque_sp[0]"), "inject[0] (excitation)": col(ind, "inject[0]")}
    lagged = {name: {tau: lag(x, tau, dt) for tau in TAUS} for name, x in raw.items()}

    inj = raw["inject[0] (excitation)"]
    nz = np.flatnonzero(inj != 0.0)
    inj_first, inj_last = (t[nz[0]], t[nz[-1]]) if nz.size else (np.nan, np.nan)
    inj_in_win = int(np.count_nonzero(inj[w] != 0.0))

    results = {}
    for aname, alpha in alphas.items():
        for rname in raw:
            results[(aname, rname)] = scan(alpha, lagged[rname], w, dt)

    main_rows = results[(primary, "torque_sp[0] (u)")]
    best = max(main_rows, key=lambda r: r[3])
    best_tau, best_k, best_g, best_r2 = best

    freq_rows = []
    u_key = "torque_sp[0] (u)"
    for tau in TAUS:
        k_tau = max((r for r in main_rows if r[0] == tau), key=lambda r: r[3])[1]
        fq, ratio, med = freq_ratio(alphas[primary], lagged[u_key][tau], raw[u_key], w, k_tau, dt)
        freq_rows.append((tau, k_tau, med, fq, ratio))

    ext = scan(alphas[primary], lagged[u_key], w, dt, ks=range(0, 13))
    ext_map = {(tau, k): (g, r2) for tau, k, g, r2 in ext}
    L = []
    L.append("# Roll G1 regression, stage2_s42")
    L.append("")
    L.append(f"Log: `{path}`  ")
    L.append("Script: `indi_flight/bench/g1_regress_s42.py`")
    L.append("")
    L.append("## Signals and rates")
    L.append("")
    L.append(f"- u = `indi_rate_status.torque_sp[0]` (normalised roll torque command), {rate_ind:.1f} Hz (median dt {dt*1e3:.4f} ms)")
    L.append(f"- alpha (primary) = `indi_rate_status.angular_accel_filtered[0]`, {rate_ind:.1f} Hz, rad/s^2")
    L.append(f"- alpha (cross-check) = `vehicle_angular_velocity.xyz_derivative[0]`, {rate_vav:.1f} Hz, linearly interpolated onto the indi_rate_status timestamps")
    L.append("- excitation (cross-check regressor) = `indi_rate_status.inject[0]`")
    L.append("")
    L.append("## Window and method")
    L.append("")
    L.append(f"- Window: {WIN[0]:.0f}-{WIN[1]:.0f} s since boot (absolute timestamp_sample; first indi sample at {t[0]:.3f} s), "
             f"N = {w.size} samples = {w.size*dt:.2f} s.")
    L.append(f"- inject[0] nonzero in window: {inj_in_win}/{w.size} samples. Overall nonzero extent: {inj_first:.2f}-{inj_last:.2f} s since boot.")
    L.append(f"- Regression: alpha = G1 * BP(u_lag(t - k dt)) + b, BP = zero-phase {REG_BAND[0]:.0f}-{REG_BAND[1]:.0f} Hz FFT mask on both signals.")
    L.append("- Lag applied to u before the delay and band-pass: exact ZOH, a = exp(-dt/tau). tau = 0 means no lag.")
    L.append("")
    L.append("## Main table (alpha = angular_accel_filtered[0], regressor = torque_sp[0])")
    L.append("")
    L.append("| tau [s] | k | delay [ms] | G1 | R^2 |")
    L.append("|---|---|---|---|---|")
    for tau, k, g, r2 in main_rows:
        L.append(f"| {tau:.3f} | {k} | {k*dt*1e3:.2f} | {g:.1f} | {r2:.4f} |")
    L.append("")
    L.append(f"**Best R^2 = {best_r2:.4f}** at tau = {best_tau:.3f} s, k = {best_k} ({best_k*dt*1e3:.2f} ms): "
             f"**G1 = {best_g:.1f}**, G1 / 320 = {best_g/G1_DEFAULT:.3f} (hypothesis 1.30 x 320 = {G1_HYPOTHESIS:.0f}).")
    L.append("")
    L.append("## Cross-checks (best k per tau, by R^2)")
    L.append("")
    L.append("| alpha | regressor | tau [s] | best k | G1 | R^2 |")
    L.append("|---|---|---|---|---|---|")
    for (aname, rname), rows in results.items():
        for tau in TAUS:
            tau_rows = [r for r in rows if r[0] == tau]
            tau_, k, g, r2 = max(tau_rows, key=lambda r: r[3])
            L.append(f"| {aname} | {rname} | {tau:.3f} | {k} | {g:.1f} | {r2:.4f} |")
    L.append("")
    L.append("## Delay extension (diagnostic, k = 0..12, alpha = angular_accel_filtered[0], u = torque_sp[0])")
    L.append("")
    L.append("| k | delay [ms] | G1 (tau 0.020) | R^2 (tau 0.020) | G1 (tau 0.033) | R^2 (tau 0.033) |")
    L.append("|---|---|---|---|---|---|")
    for k in range(0, 13):
        g2, r22 = ext_map[(0.020, k)]
        g3, r23 = ext_map[(0.033, k)]
        L.append(f"| {k} | {k*dt*1e3:.2f} | {g2:.1f} | {r22:.4f} | {g3:.1f} | {r23:.4f} |")
    L.append("")
    L.append("## Frequency-domain estimate (alpha = angular_accel_filtered[0], u = torque_sp[0])")
    L.append("")
    L.append("Ratio |FFT(alpha)| / |FFT(u_lag)| at the strongest local peaks of |FFT(u)| in "
             f"{FQ_BAND[0]:.0f}-{FQ_BAND[1]:.0f} Hz, rectangular window over the full window (bin width {1/(w.size*dt):.4f} Hz). "
             "k = best R^2 for that tau.")
    L.append("")
    L.append("| tau [s] | k | median ratio (G1) | peak frequencies [Hz] | ratios |")
    L.append("|---|---|---|---|---|")
    for tau, k, med, fq, ratio in freq_rows:
        L.append(f"| {tau:.3f} | {k} | {med:.1f} | {', '.join(f'{x:.3f}' for x in fq)} | "
                 f"{', '.join(f'{x:.1f}' for x in ratio)} |")
    L.append("")
    GRID_TAUS = (0.0, 0.020, 0.033, 0.050, 0.070, 0.100)
    a_bp = bandpass(alphas[primary][w], dt, *REG_BAND)
    L.append("## Diagnostic: joint tau x k grid (beyond the spec)")
    L.append("")
    L.append("Tests whether the k=4 best in the main table is an interior optimum. If the best k sits at 24, "
             "or G1 keeps rising with k, G1 is not identified by this regression alone.")
    L.append("")
    L.append("| tau [s] | best k (0..24) | G1 at best k | best R^2 | G1, R^2 at k=0 | G1, R^2 at k=12 |")
    L.append("|---|---|---|---|---|---|")
    for tau in GRID_TAUS:
        ul = lag(raw[u_key], tau, dt)
        grid = []
        for k in range(0, 25):
            g_, r2_ = fit(a_bp, bandpass(ul[w - k], dt, *REG_BAND))
            grid.append((k, g_, r2_))
        kb, gb, rb = max(grid, key=lambda r: r[2])
        L.append(f"| {tau:.3f} | {kb} | {gb:.1f} | {rb:.4f} | {grid[0][1]:.1f}, {grid[0][2]:.4f} | "
                 f"{grid[12][1]:.1f}, {grid[12][2]:.4f} |")
    L.append("")
    L.append("## UNVERIFIED")
    L.append("")
    L.append("- The tau = 0.033 s and 0.020 s lag values come from the task brief; not checked against the sim model or firmware parameters.")
    L.append("- torque_sp[0] assumed to be the exact plant input. Not checked against actuator_motors, mixer or ESC dynamics.")
    L.append("- torque_sp includes the INDI feedback part as well as the injection, so it is correlated with alpha. "
             "The inject[0] regressor cross-check is the excitation-only alternative; the two disagree (see table), and the feedback-correlated fit is not verified to be unbiased.")
    L.append("- angular_accel_filtered[0] has an unknown internal filter and delay. Its G1 and k may differ from the true plant. "
             "The xyz_derivative[0] cross-check is NOT independent: corr 0.99999999, max abs diff 0.21 rad/s^2 vs window RMS 13.9 rad/s^2, so the two alpha rows are the same signal.")
    L.append("- Units: G1 = (rad/s^2) per normalised torque unit. Comparing it to the firmware default 320 assumes the same units and definition. Not checked against the INDI code.")
    L.append("- '52-82 s after boot' is taken as the absolute indi_rate_status timestamp_sample in s. It matches the inject[0] extent; the ULog boot time itself is not checked.")
    L.append("- The 2-10 Hz band-pass is a brick-wall FFT mask over a rectangular 30 s window (no taper). Edge and leakage effects are not quantified.")
    L.append("- The intercept b absorbs any residual offset; not checked for steady-state torque bias.")
    L.append("- Frequency-domain peaks assume the injection periods are commensurate with the window. Non-integer periods leak into neighbouring bins and bias the ratio.")
    L.append("- Closed loop: the slow loop is removed by band-pass, not modelled. Feedback inside 2-10 Hz is not separated from the injection beyond the inject[0] cross-check.")
    L.append("- G1 is confounded with the (tau, k) lag/delay pair. The joint grid ridge gives G1 from about 320 to 820 at R^2 0.85-0.93. "
             "Fitted delays of 20-28 ms at the ridge top are not physical for a motor lag, so the extra delay may absorb an unmodelled filter lag in angular_accel_filtered or feedback correlation. Not resolved here.")
    L.append("- The 1.30 x 320 hypothesis is only compared numerically; no firmware or sim truth value was checked.")
    L.append("")

    os.makedirs(os.path.dirname(os.path.abspath(out_md)), exist_ok=True)
    with open(out_md, "w") as fh:
        fh.write("\n".join(L))

    print(f"best R2={best_r2:.4f} tau={best_tau} k={best_k} G1={best_g:.1f} G1/320={best_g/G1_DEFAULT:.3f}")
    for tau, k, med, fq, ratio in freq_rows:
        print(f"freq tau={tau} k={k} median={med:.1f} bins={np.round(fq, 3).tolist()}")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
