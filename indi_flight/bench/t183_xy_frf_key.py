"""T183 second key: x-axis pinj loop FRF from the two pinj CSVs.

Columns: d = excitation r (only periodic channel, lag-Tp corr = 1.000),
x = loop input e (entering the break), y = loop output (returning signal).
Harmonic coefficients at k/Tp from a per-period least-squares fit on the
true timestamps (no resampling); whole periods, first period dropped.
Sign: the data obey x = r + y (checked), so x/r = 1/(1-Y/X) and the
loop gain with sensitivity 1/(1+L) is L = -Y/X.
"""
from pathlib import Path

import numpy as np

TP = 10.0
KMAX = 80                       # bins 1..80 -> 0.1..8.0 Hz
EXC = [2, 3, 4, 5, 6, 8, 10, 13, 16, 20, 25, 32, 40, 50, 63, 80]  # excited bins
CHECK_HZ = [0.2, 0.4, 0.5, 1.0, 2.0]
DATA = Path("indi_flight/results/stage5_s86_g2outer")
FILES = ["pt0_ax1_r400_s1_pinj.csv", "pt1_ax1_r400_s1_pinj.csv"]


def load(name):
    D = np.genfromtxt(DATA / name, delimiter=",", names=True)
    return D["t"], {c: D[c] for c in ("d", "x", "y")}


def period_coeffs(t, sig, t0, nper):
    """Complex coefficients a - i b per whole period, bins 1..KMAX, periods 0..nper-1."""
    ks = np.arange(1, KMAX + 1)
    out = []
    for p in range(nper):
        m = (t >= t0 + p * TP) & (t < t0 + (p + 1) * TP)
        tau = t[m] - (t0 + p * TP)
        th = 2 * np.pi * np.outer(tau, ks) / TP
        A = np.column_stack([np.ones(m.sum()), np.cos(th), np.sin(th)])
        coef, *_ = np.linalg.lstsq(A, sig[m], rcond=None)
        out.append(coef[1:KMAX + 1] - 1j * coef[KMAX + 1:])
    return np.array(out)


def analyse(name):
    t, s = load(name)
    fs = 1 / np.median(np.diff(t))
    nper = int(np.floor((t[-1] - t[0]) / TP + 1e-9)) + 1   # 5 (last one 99.98 % complete)
    C = {c: period_coeffs(t, s[c], t[0], nper)[1:] for c in "dxy"}   # drop period 0
    n = C["d"].shape[0]
    f = np.arange(1, KMAX + 1) / TP
    Srr = np.mean(np.abs(C["d"]) ** 2, axis=0)
    Sxx = np.mean(np.abs(C["x"]) ** 2, axis=0)
    Syy = np.mean(np.abs(C["y"]) ** 2, axis=0)
    Srx = np.mean(np.conj(C["d"]) * C["x"], axis=0)
    Sry = np.mean(np.conj(C["d"]) * C["y"], axis=0)
    Sxy = np.mean(np.conj(C["x"]) * C["y"], axis=0)
    # Sign: x = r + y exactly (identity below) => G = Y/X = 1 - R/X and x/r = 1/(1-G) = 1/(1+L), L = -G.
    # Primary estimate is r-referenced (r is the clean reference; y carries the non-periodic noise):
    #   L = 1/S - 1 with S = Srx/Srr.  H1 (-Sxy/Sxx) is kept for comparison only.
    L = Srr / Srx - 1
    L_h1 = -Sxy / Sxx
    ident = np.abs((C["x"] - C["d"]) - C["y"]).sum() / np.abs(C["y"]).sum()
    chk = np.abs(L_h1) / np.abs(L)      # H1 / r-referenced magnitude ratio
    coh_rx = np.abs(Srx) ** 2 / (Srr * Sxx)
    coh_ry = np.abs(Sry) ** 2 / (Srr * Syy)
    coh_xy = np.abs(Sxy) ** 2 / (Sxx * Syy)

    print(f"== {name}: N={len(t)} fs~{fs:.2f} Hz span={t[-1]-t[0]:.3f} s periods used={n}")
    print(f"   identity x=r+y residual (rel, sum over bins) = {ident:.3e}")
    print("   H1 vs r-referenced |L| ratio over excited bins: min %.3f max %.3f" %
          (chk[np.array(EXC)-1].min(), chk[np.array(EXC)-1].max()))
    print("   bin   f[Hz]  |L|    arg(L)[deg]  coh(r,x) coh(r,y) coh(x,y)  |L_H1| arg_H1")
    rows = []
    for b in EXC:
        i = b - 1
        rows.append((f[i], np.abs(L[i]), np.degrees(np.angle(L[i])), coh_rx[i], coh_ry[i], coh_xy[i]))
        print(f"   {b:3d}  {f[i]:5.2f}  {np.abs(L[i]):6.3f}  {np.degrees(np.angle(L[i])):9.1f}"
              f"   {coh_rx[i]:6.3f}   {coh_ry[i]:6.3f}   {coh_xy[i]:6.3f}   {np.abs(L_h1[i]):6.3f} {np.degrees(np.angle(L_h1[i])):7.1f}")
    # Interpolate at requested frequencies (on excited-bin grid, log-f linear)
    fe = np.array([r[0] for r in rows]); Le = np.array([r[1] for r in rows])
    ph = np.unwrap(np.radians([r[2] for r in rows]))
    print("   check Hz -> |L|  arg(L) (log-f interp on excited bins; nearest bin shown)")
    for fc in CHECK_HZ:
        i = np.argmin(np.abs(fe - fc))
        print(f"   {fc:4.1f}: nearest bin {fe[i]:.2f} Hz |L|={Le[i]:.3f} arg={np.degrees(ph[i]):.1f}")
    # Crossover |L| = 1 by log-log interpolation, phase by linear-in-log-f interpolation
    lf = np.log10(fe); lm = np.log10(Le)
    idx = np.where((lm[:-1]) * (lm[1:]) <= 0)[0]
    if len(idx) == 0:
        print("   no crossover on excited bins")
        return
    j = idx[0]
    w = lm[j] / (lm[j] - lm[j + 1])
    fc = 10 ** (lf[j] + w * (lf[j + 1] - lf[j]))
    phc = ph[j] + w * (ph[j + 1] - ph[j])
    pm = 180 + np.degrees(phc)
    print(f"   crossover fc = {fc:.3f} Hz (bins {fe[j]:.2f}-{fe[j+1]:.2f}), arg(L)={np.degrees(phc):.1f} deg, PM = {pm:.1f} deg")


if __name__ == "__main__":
    for name in FILES:
        analyse(name)
        print()
