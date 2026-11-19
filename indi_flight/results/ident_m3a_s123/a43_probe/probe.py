"""A-43 probe: copy of ident_fit_yaw with variant switches. Does not modify bench/. Usage: probe.py real <ulg> | synth"""
import os, sys
import numpy as np
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "bench")
sys.path.insert(0, B)
import ident_fit as base
import ident_iv as iv
import ident_fit_yaw as fy

def prep(t_gyro, omega, t_u, u, t_z, z, t0, t1, ntaps, fs, interp_match, with_r):
    dt = 1.0 / fs
    tg = np.arange(t0, t1, dt)
    taps = iv.smooth_taps(ntaps)
    t_u = np.asarray(t_u, float); u = np.asarray(u, float)
    chg = np.concatenate([[True], np.diff(u) != 0])
    tc = t_u[chg]
    def sig(t, v):
        if interp_match:  # same operator as u: sample at u's update stamps, linear interp onto grid
            vc = iv.resample_to_grid(t, v, tc)
            ok = np.isfinite(vc)
            g = np.interp(tg, tc[ok], vc[ok]); g[(tg < tc[ok][0]) | (tg > tc[ok][-1])] = np.nan
            return g
        return iv.resample_to_grid(t, v, tg)
    w = sig(t_gyro, omega)
    y = iv.apply_taps(np.gradient(w, dt), taps)
    xg = np.interp(tg, tc, u[chg]); xg[(tg < t_u[0]) | (tg > t_u[-1])] = np.nan
    x1 = iv.apply_taps(iv.apply_taps(xg, base.CENTRAL_DIFF_MATCH), taps)
    x2 = iv.apply_taps(np.gradient(xg, dt), taps)
    zg = sig(t_z, z)
    z1 = iv.apply_taps(iv.apply_taps(zg, base.CENTRAL_DIFF_MATCH), taps)
    z2 = iv.apply_taps(np.gradient(zg, dt), taps)
    cols = [x1, x2]
    if with_r:
        cols.append(iv.apply_taps(iv.apply_taps(w, base.CENTRAL_DIFF_MATCH), taps))
    return y, np.column_stack(cols), z1, z2, np.zeros(len(tg), bool)

def fit(t_gyro, omega, t_u, u, t_z, z, t0, t1, interp_match=False, with_r=False, ntaps=15, fs=800.0, sat=None, t_sat=None):
    _, m = base.update_rate(u, 0.25)
    y, X, z1, z2, excl = prep(t_gyro, omega, t_u, u, t_z, z, t0, t1, ntaps, fs, interp_match, with_r)
    if sat is not None:
        ts = np.asarray(t_sat, float); tg = np.arange(t0, t1, 1 / fs)
        idx = np.clip(np.searchsorted(ts, tg, side="right") - 1, 0, len(ts) - 1)
        excl |= np.convolve(np.asarray(sat, bool)[idx].astype(float), np.ones(ntaps), mode="same") > 0
    sl = slice(None, None, m)
    Zr = fy._build_Z(z1, z2, sl, list(range(0, 33, 2)), list(range(0, 33, 4)), m)
    nr = X.shape[1]
    def run(k, hl, wf):
        Xs = np.column_stack([base._lead(X[:, i], k) if i < 2 else X[:, i] for i in range(nr)])[sl]
        ok = np.isfinite(y[sl]) & np.isfinite(Xs).all(1) & np.isfinite(Zr).all(1) & ~excl[sl]
        return fy._iv2_keep(y[sl], Xs, Zr, ok, hl, wf)
    cand = list(range(base.SHIFT_MIN, base.SHIFT_MAX + 1))
    js = [run(k, max(1, 80 // m), False)["j"] for k in cand]
    k = cand[int(np.argmin(js))]
    r = run(k, max(1, 400 // m), True)
    r["shift"] = k; r["m"] = m
    return r

def row(name, r):
    b, s = r["beta"], 1.96 * r["se"]
    D = ("%.3f +-%.3f" % (-b[2], s[2])) if len(b) > 2 else "-"
    return "| %s | %.1f | +-%.1f | %.2f | +-%.2f | %s | %.1f (df %d, %.1f) | %d | %s |" % (
        name, b[0], s[0], b[1], s[1], D, r["j"], r["j_df"], r["j"] / max(r["j_df"], 1), r["shift"],
        "/".join("%.0f" % f for f in r["f_eff"]))

def synth(seed=1, T=80.0, G1=205.3, G2=27.0, D=1.4, tau=0.0125, K=0.15, amp=0.08):
    rng = np.random.default_rng(seed)
    H = 3200; dt = 1.0 / H; n = int(T * H)
    t = np.arange(n) * dt
    fr = np.linspace(0.3, 50, 120); ph = rng.uniform(0, 2 * np.pi, fr.size)
    dsig = amp * sum(np.sin(2 * np.pi * f * t + p) for f, p in zip(fr, ph)) / np.sqrt(fr.size / 2)
    r = 0.0; um = 0.0; ucmd = 0.0; ur = 0.0
    R = np.zeros(n); U = np.zeros(n)
    for i in range(n):
        if i % (H // 400) == 0:  # controller at 400 Hz, ZOH, acts on measured gyro
            ucmd = -K * r + dsig[i]
        um_old = um
        um += dt / tau * (ucmd - um)
        a = G1 * um + G2 * (um - um_old) / dt - D * r
        r += a * dt
        R[i] = r; U[i] = um
    r400 = H // 400; r800 = H // 800
    ig = np.arange(0, n, r800); iu = np.arange(0, n, r400)
    gyro = R[ig] + 1e-4 * rng.standard_normal(ig.size)
    return t[ig], gyro, t[iu], U[iu], t[ig], dsig[ig]

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "real":
        D = base.load(sys.argv[2], "yaw"); t0l = D.pop("t_log0")
        for k in ("t_gyro", "t_u", "t_z", "t_sat"): D[k] = D[k] - t0l
        for name, im, wr in (("V0", 0, 0), ("V1", 1, 0), ("V2", 0, 1), ("V3", 1, 1)):
            r = fit(D["t_gyro"], D["omega"], D["t_u"], D["u"], D["t_z"], D["z"], 22.1, 76.0, bool(im), bool(wr), sat=D["sat"], t_sat=D["t_sat"])
            print(row(name, r), flush=True)
    else:
        a = synth()
        for name, im, wr in (("S0", 0, 0), ("S1", 1, 0), ("S2", 0, 1), ("S3", 1, 1)):
            r = fit(*a, 8.0, 76.0, bool(im), bool(wr))
            print(row(name, r), flush=True)
