#!/usr/bin/env python3
"""G2 outer-loop margins, independent second key (S164). Own FRF + margin code.
Usage: python3 indi_flight/bench/g2_key2_outer_s164.py [--selftest-only]
Writes indi_flight/results/g2_outer_freeze_s163/key2.md (method, self-test, own table; THEN primary comparison).
Convention: L = -G_yd/G_xd, d injected, x = c + d, y = c.
"""
import sys, os, glob, json
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, '..', 'results', 'g2_outer_freeze_s163')
FMIN, FMAX, COH_MIN, NP = 0.2, 8.0, 0.8, 5


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


def dft(t, v, f, w):
    """weighted non-uniform DFT of v(t) at frequencies f (trapezoid-like weights w)."""
    return (v * w)[None, :] @ np.exp(-2j * np.pi * np.outer(t, f))


def frf(t, d, x, y, Tp):
    """periods 2..NP; returns f, L, coh_x, coh_y (bins excited in d)."""
    t0 = t[0]
    P = []
    for p in range(1, NP):
        m = (t >= t0 + p * Tp) & (t < t0 + (p + 1) * Tp)
        P.append(m)
    nb = np.arange(int(np.floor(0.15 * Tp)), int(np.ceil(8.5 * Tp)) + 1)
    f = nb / Tp
    D = np.zeros((len(P), len(f)), complex); X = D.copy(); Y = D.copy()
    for i, m in enumerate(P):
        tt = t[m]
        w = np.gradient(tt)
        D[i] = dft(tt, d[m], f, w)[0]; X[i] = dft(tt, x[m], f, w)[0]; Y[i] = dft(tt, y[m], f, w)[0]
    Dm = np.abs(D.mean(0))
    ex = (Dm > 0.1 * Dm.max()) & (f >= FMIN - 1e-9) & (f <= FMAX + 1e-9)
    f, D, X, Y = f[ex], D[:, ex], X[:, ex], Y[:, ex]
    # period-averaged cross-spectral FRFs; coherence across the periods (d is periodic, noise is not)
    Gxd = (X * D.conj()).sum(0) / (np.abs(D) ** 2).sum(0)
    Gyd = (Y * D.conj()).sum(0) / (np.abs(D) ** 2).sum(0)
    def coh(Z):
        return np.abs((Z * D.conj()).sum(0)) ** 2 / ((np.abs(Z) ** 2).sum(0) * (np.abs(D) ** 2).sum(0))
    return f, -Gyd / Gxd, coh(X), coh(Y)


def margins(f, L):
    """f ascending, L complex at kept bins. Log-f linear interpolation of log|L| and unwrapped phase."""
    out = dict(pm=np.nan, gm=np.nan, dm=np.nan, ms=np.nan, pgm=np.nan, n=len(f), wc=[], wpi=[])
    if len(f) < 2:
        return out
    lf = np.log(f); lm = np.log(np.abs(L)); ph = np.degrees(np.unwrap(np.angle(L)))
    # fine grid for Ms
    g = np.linspace(lf[0], lf[-1], 4000)
    Lg = np.exp(np.interp(g, lf, lm) + 1j * np.radians(np.interp(g, lf, ph)))
    out['ms'] = float(np.max(1 / np.abs(1 + Lg)))
    # gain crossovers
    pms, dms, gms = [], [], []
    for i in range(len(f) - 1):
        a, b = lm[i], lm[i + 1]
        if a == 0 or (a < 0) != (b < 0) or b == 0:
            s = (0 - a) / (b - a) if b != a else 0.0
            if 0 <= s <= 1:
                phc = ph[i] + s * (ph[i + 1] - ph[i]); wc = 2 * np.pi * np.exp(lf[i] + s * (lf[i + 1] - lf[i]))
                pm = wrap180(phc + 180.0)
                pms.append(pm); dms.append(np.radians(pm) / wc); out['wc'].append(wc / 2 / np.pi)
        # phase crossings of -180 mod 360
        k0 = (ph[i] + 180) / 360.0; k1 = (ph[i + 1] + 180) / 360.0
        lo, hi = sorted((k0, k1))
        for k in range(int(np.ceil(lo)), int(np.floor(hi)) + 1):
            if k1 == k0:
                continue
            s = (k - k0) / (k1 - k0)
            if 0 <= s <= 1:
                gms.append(-20 * np.log10(np.exp(lm[i] + s * (lm[i + 1] - lm[i])))); out['wpi'].append(np.exp(lf[i] + s * (lf[i + 1] - lf[i])))
    if pms:
        out['pm'] = float(min(pms)); out['dm'] = float(min(dms))
    if gms:
        out['gm'] = float(min(gms))
    pl = np.abs(wrap180(ph + 180.0)) <= 10.0
    if pl.any():
        out['pgm'] = float(np.min(-20 * np.log10(np.abs(L[pl]))))
    return out


def analyse(t, d, x, y, Tp):
    f, L, cx, cy = frf(t, d, x, y, Tp)
    keep = (cx >= COH_MIN) & (cy >= COH_MIN)
    r = margins(f[keep], L[keep])
    r['nex'] = len(f)
    return r


# ---------------------------------------------------------------- self-test
def schroeder(Tp, nbins=30, amp=0.08):
    m = np.unique(np.round(np.geomspace(FMIN * Tp, FMAX * Tp, nbins)).astype(int))
    fk = m / Tp
    ph = -np.pi * np.arange(1, len(m) + 1) * np.arange(len(m)) / len(m)  # Schroeder
    a = amp / np.sqrt(len(m) / 2)
    return fk, ph, a


def run_loop(num, den, mdelay, Tp, seed, fs=88.9, noise=0.003, procnoise=0.01):
    rng = np.random.default_rng(seed)
    Ts = 1 / fs; N = int(round(NP * Tp * fs)); tk = np.arange(N) * Ts + 50.0
    fk, ph, a = schroeder(Tp)
    d = sum(a * np.cos(2 * np.pi * fi * (tk - tk[0]) + p_) for fi, p_ in zip(fk, ph))
    w = procnoise * rng.standard_normal(N)
    x = np.zeros(N); Lout = np.zeros(N)  # Lout = L(z) x ; c = -Lout
    c = np.zeros(N)
    for k in range(N):
        s = 0.0
        for i, b in enumerate(num):
            j = k - i - mdelay
            if j >= 0: s += b * x[j]
        for j in range(1, len(den)):
            if k - j >= 0: s -= den[j] * Lout[k - j]
        Lout[k] = s; c[k] = -s
        x[k] = c[k] + d[k] + w[k]
    y = c + noise * rng.standard_normal(N); xm = x + noise * rng.standard_normal(N)
    tq = np.floor(tk * 400 + 1e-9) / 400  # mimic the 400 Hz timestamp grid of the real logs
    return tq, d, xm, y


def analytic(num, den, mdelay, fs, f):
    z = np.exp(2j * np.pi * f / fs)
    zi = 1 / z
    n = sum(b * zi ** i for i, b in enumerate(num)); dd = sum(b * zi ** i for i, b in enumerate(den))
    return n * zi ** mdelay / dd


def selftest(log):
    fs = 88.9; Ts = 1 / fs
    cases = []
    def lagint(K, pHz, mdel):
        a = np.exp(-2 * np.pi * pHz * Ts)
        # L = K Ts/(1-z^-1) * (1-a)/(1-a z^-1)  [integrator * unity-DC-gain lag at pHz]; K in rad/s
        num = [K * Ts * (1 - a)]; den = np.convolve([1, -1], [1, -a])
        return num, den, mdel
    cases.append(('A finite GM/PM (delay)', lagint(6.0, 6.0, 4), 20.0))
    cases.append(('B no -180 crossing in band', lagint(3.0, 30.0, 1), 20.0))
    cases.append(('C phase plateau near -180', lagint(10.0, 0.25, 1), 10.0))
    cases.append(('D z-axis Tp=10', lagint(8.0, 5.0, 3), 10.0))
    allok = True
    for name, (num, den, md), Tp in cases:
        # analytic margins on a dense in-band grid (continuous interp of the exact L(e^jwTs))
        fg = np.geomspace(FMIN, FMAX, 20000)
        La = analytic(num, den, md, fs, fg)
        ra = margins(fg, La)
        # plateau analytic on the excited bins
        fk, _, _ = schroeder(Tp)
        ra_bins = margins(fk, analytic(num, den, md, fs, fk))
        res = []
        for seed in (1, 2, 3):
            t, d, x, y = run_loop(num, den, md, Tp, seed)
            res.append(analyse(t, d, x, y, Tp))
        r = res[0]
        def cmp(k, tol, rel=False):
            e = r[k]; a_ = ra[k]
            if np.isnan(a_) and np.isnan(e): return True, 'none/none'
            if np.isnan(a_) != np.isnan(e): return False, f'est {e} vs ana {a_}'
            err = abs(e - a_) / abs(a_) if rel else abs(e - a_)
            return err <= tol, f'est {e:.3f} ana {a_:.3f} err {err:.3f}'
        okp, sp = cmp('pm', 1.0); okg, sg = cmp('gm', 0.5); okd, sd = cmp('dm', 0.05, True)
        if np.isnan(ra['gm']) and not np.isnan(r['gm']):
            # phase asymptotes to -180 without crossing: noise can create a spurious crossing at tiny |L|; tolerated only if far from gate-relevant
            okg = r['gm'] >= 20.0; sg += ' (spurious noise crossing at tiny |L|, accepted if >= 20 dB; gate value is min(GM, plateau GM) below)'
        if np.isnan(ra_bins['pgm']) and np.isnan(r['pgm']): okq, sq = True, 'none/none'
        elif np.isnan(ra_bins['pgm']) != np.isnan(r['pgm']): okq, sq = False, f"est {r['pgm']} ana {ra_bins['pgm']}"
        else: okq = abs(r['pgm'] - ra_bins['pgm']) <= 0.5; sq = f"est {r['pgm']:.3f} ana {ra_bins['pgm']:.3f}"
        mn = lambda a_, b_: np.nanmin([a_, b_]) if not (np.isnan(a_) and np.isnan(b_)) else np.nan
        e_, a2 = mn(r['gm'], r['pgm']), mn(ra['gm'], ra_bins['pgm'])
        okm = (np.isnan(e_) and np.isnan(a2)) or (not np.isnan(e_) and not np.isnan(a2) and abs(e_ - a2) <= 0.5)
        sq += f"; min(GM,pl) est {e_:.3f} ana {a2:.3f}"
        ok = okp and okg and okd and okq and okm
        allok &= ok
        log.append(f"- {name}: {'PASS' if ok else 'FAIL'} (kept {r['n']}/{r['nex']} bins)\n    PM {sp} deg; GM {sg} dB; DM {sd}; plateauGM {sq}")
        print(log[-1])
    return allok


# ---------------------------------------------------------------- real cells
def primary(base):
    p = os.path.join(RES, base + '_margins.json')
    try:
        j = json.load(open(p))
    except Exception:
        return None
    m = j.get('margins', j)
    def g(k):
        v = m.get(k)
        if isinstance(v, (list, tuple)):
            v = [q for q in v if q is not None]
            v = min(v) if v else None
        return np.nan if v is None else float(v)
    return dict(pm=g('pm_deg'), gm=g('gm_db'), dm=g('dm_s'), ms=g('Ms'))


def main():
    log = []
    ok = selftest(log)
    md = ["# G2 outer-loop margins: independent second key (S164)\n",
          "## Method\n",
          "- Window: periods 2..5 (first period discarded), time-based non-uniform DFT at m/Tp (trapezoid weights) per period; Tp=10 s (ax3), 20 s (ax1/2).",
          "- Excited bins: |D| > 0.1 max over m/Tp in [0.2, 8] Hz, found from the period-averaged DFT of d.",
          "- FRF: cross-spectral G_xd, G_yd over the 4 periods; L = -G_yd/G_xd. Coherence per bin of x and y vs periodic d across the 4 periods; keep bins with both >= 0.8.",
          "- Margins: linear interpolation of log|L| and unwrapped phase vs log f between consecutive KEPT bins. Crossovers |L|=1 -> PM = 180+arg L (wrapped), DM = PM/wc (min over crossovers). GM = min over -180 (mod 360) crossings of -20log10|L|. Plateau GM = min over kept bins with |arg L + 180| <= 10 deg of -20log10|L|. Ms = max 1/|1+L| on the interpolated fine grid (kept-bin span).",
          "- 'GM' = NaN means no -180 crossing between kept bins in band.\n",
          f"## Self-test: {'PASS' if ok else 'FAIL'}\n",
          "Synthetic discrete loop L(z)=K Ts(1-a)z^-m/((1-z^-1)(1-a z^-1)) at 88.9 Hz, d injected at summing point, process + measurement noise, 400 Hz timestamp quantisation as in the logs; tolerances 1 deg / 0.5 dB / 5 %. Analytic reference = dense-grid margins of exact L(e^jwTs).\n"] + log
    if len(sys.argv) > 1 and sys.argv[1] == '--selftest-only':
        print('\n'.join(md)); return 0 if ok else 1
    rows = []
    for fn in sorted(glob.glob(os.path.join(RES, 'pt*_pinj.csv'))):
        base = os.path.basename(fn)[:-len('_pinj.csv')]
        a = np.loadtxt(fn, delimiter=',', skiprows=1)
        Tp = 10.0 if '_ax3_' in base else 20.0
        r = analyse(a[:, 0], a[:, 1], a[:, 2], a[:, 3], Tp)
        rows.append((base, r))
    md += ["\n## Own results (written before the primary values are read)\n",
           "| cell | kept/exc | PM deg | GM dB | plateau GM dB | min(GM,pl) dB | DM ms | Ms |", "|---|---|---|---|---|---|---|---|"]
    fm = lambda v, s=1.0, p=2: 'NaN' if v is None or np.isnan(v) else f'{v * s:.{p}f}'
    for base, r in rows:
        mg = np.nanmin([r['gm'], r['pgm']]) if not (np.isnan(r['gm']) and np.isnan(r['pgm'])) else np.nan
        md.append(f"| {base} | {r['n']}/{r['nex']} | {fm(r['pm'])} | {fm(r['gm'])} | {fm(r['pgm'])} | {fm(mg)} | {fm(r['dm'], 1e3, 1)} | {fm(r['ms'], 1, 3)} |")
    os.makedirs(RES, exist_ok=True)
    out = os.path.join(RES, 'key2.md')
    open(out, 'w').write('\n'.join(md) + '\n')
    # ---- stage 2: primary comparison (own table is already on disk)
    md += ["\n## Comparison with primary (*_margins.json)\n",
           "| cell | PM own/prim/d | GM own/prim/d | DM ms own/prim | Ms own/prim | status |", "|---|---|---|---|---|---|"]
    blocked = []
    for base, r in rows:
        p = primary(base)
        if p is None:
            md.append(f"| {base} | primary missing/empty | | | | n/a |"); continue
        dpm = r['pm'] - p['pm']; dgm = r['gm'] - p['gm']
        bad = (not np.isnan(dpm) and abs(dpm) > 3) or (not np.isnan(dgm) and abs(dgm) > 1) \
            or (np.isnan(dpm) != (np.isnan(p['pm']) or np.isnan(r['pm']) and False) and (np.isnan(r['pm']) != np.isnan(p['pm']))) \
            or (np.isnan(r['gm']) != np.isnan(p['gm']))
        if bad: blocked.append(base)
        md.append(f"| {base} | {fm(r['pm'])}/{fm(p['pm'])}/{fm(dpm)} | {fm(r['gm'])}/{fm(p['gm'])}/{fm(dgm)} | "
                  f"{fm(r['dm'],1e3,1)}/{fm(p['dm'],1e3,1)} | {fm(r['ms'],1,3)}/{fm(p['ms'],1,3)} | {'BLOCKED' if bad else 'agree'} |")
    md += [f"\nBLOCKED cells ({len(blocked)}): " + (', '.join(blocked) if blocked else 'none')]
    open(out, 'w').write('\n'.join(md) + '\n')
    print('\n'.join(md))
    return 0


if __name__ == '__main__':
    sys.exit(main())
