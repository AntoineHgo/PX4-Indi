#!/usr/bin/env python3
"""S50 second key: INDI roll-rate loop with rate lead, own frequency-domain model.

Loop (G1 normalised to 1, matched):
  plant      w = Pl(s) u,  Pl = ZOH(s) * exp(-s d) / (tau s + 1) / s        (u = torque setpoint)
  attitude   rate_sp = -P w/s                                              (att_sp = 0)
  controller u_c = Fm u_p - X w,  X = K (P/s + Hg) + (1 + c) D,  c = K tau_c (0 if no lead)
     Hg = LPF2p(fg)                   gyro filter on the rate error path
     D  = alpha(fd) * (1 - z^-1)/T * LPF2p(fg)       filtered angular acceleration a_f
     Fm = alpha(fd) * LPF2p(fg) * Mz * z^-1          filtered torque model t_f (same H as a_f)
     Mz = discrete first order lag of tau_c (exact ZOH step-invariant), one sample delay z^-1
  Break at the torque setpoint: closing u_p = u_c gives 1 + L, L = X Pl - Fm.
"""
import numpy as np

FG, FD, TAU = 40.0, 30.0, 0.033


def lpf2p(f, fc, T):
    # 2nd order Butterworth, bilinear (same form as PX4 LowPassFilter2p)
    k = np.tan(np.pi * fc * T)
    q = np.sqrt(2.0)
    n = 1 + q * k + k * k
    b0 = k * k / n
    a1 = 2 * (k * k - 1) / n
    a2 = (1 - q * k + k * k) / n
    zi = np.exp(-2j * np.pi * f * T)
    return b0 * (1 + 2 * zi + zi * zi) / (1 + a1 * zi + a2 * zi * zi)


def loop(f, fs, K, P, tau_c, lead, d, tau=TAU):
    T = 1.0 / fs
    s = 2j * np.pi * f
    zi = np.exp(-s * T)
    al = T / (T + 1 / (2 * np.pi * FD))
    Ha = al / (1 - (1 - al) * zi)
    Hg = lpf2p(f, FG, T)
    D = Ha * (1 - zi) / T * Hg
    m = 1 - np.exp(-T / tau_c)
    Fm = Ha * Hg * (m * zi / (1 - (1 - m) * zi)) * zi
    c = K * tau_c if lead else 0.0
    X = K * (P / s + Hg) + (1 + c) * D
    zoh = (1 - zi) / (s * T)
    Pl = zoh * np.exp(-s * d) / (tau * s + 1) / s
    return X * Pl - Fm


def margins(fs, K, P, tau_c, lead, d):
    f = np.linspace(0.2, 0.45 * fs, 400000)
    L = loop(f, fs, K, P, tau_c, lead, d)
    mag = np.abs(L)
    ph = np.degrees(np.unwrap(np.angle(L)))
    ph -= 360 * np.ceil(ph[0] / 360)
    idx = np.where((mag[:-1] >= 1) & (mag[1:] < 1))[0]
    if len(idx) == 0:
        return (np.nan,) * 4
    i = idx[0]
    r = (1 - mag[i]) / (mag[i + 1] - mag[i]) if False else (np.log(mag[i]) / (np.log(mag[i]) - np.log(mag[i + 1])))
    fc = f[i] + r * (f[i + 1] - f[i])
    phc = ph[i] + r * (ph[i + 1] - ph[i])
    pm = 180 + phc
    dm = pm / (360 * fc) * 1000
    jj = np.where((ph[:-1] > -180) & (ph[1:] <= -180) & (np.arange(len(f) - 1) > i))[0]
    if len(jj):
        j = jj[0]
        gm = -20 * np.log10(mag[j])
    else:
        gm = np.inf
    return pm, fc, gm, dm


if __name__ == "__main__":
    rows = []
    for d in (0, 2.5, 5):
        rows.append(("no lead", 800, 20, d, margins(800, 20, 8, TAU, False, d * 1e-3)))
    for fs in (400, 800):
        for K in (20, 30, 40):
            for d in (2.5, 5):
                rows.append(("lead", fs, K, d, margins(fs, K, 8, TAU, True, d * 1e-3)))
    out = ["| case | rate Hz | K_R | d ms | PM deg | f_c Hz | GM dB | DM ms |", "|---|---|---|---|---|---|---|---|"]
    for n, fs, K, d, (pm, fc, gm, dm) in rows:
        out.append(f"| {n} | {fs} | {K} | {d} | {pm:.1f} | {fc:.2f} | {gm:.1f} | {dm:.1f} |")
    print("\n".join(out))
