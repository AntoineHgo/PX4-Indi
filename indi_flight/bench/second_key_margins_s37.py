import os
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from margins_est import margins  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else 'second_key_margins.md'
W0 = 2 * np.pi * 15.0
TOL_GM, TOL_PM, TOL_DM_MS = 1.0, 3.0, 0.3
NAN = float('nan')


def make_case(name, T=None):
    if name == 'A':
        tau = 0.008 + 1.5 * T
        return lambda s: 20 * np.exp(-s * tau) / (s * (1 + 0.01 * s))
    if name == 'B':
        return lambda s: (20 * np.exp(-0.004 * s) / (s * (1 + 0.02 * s))
                          * (1 + 2.5 * W0 ** 2 / (s ** 2 + 2 * 0.1 * W0 * s + W0 ** 2)))
    return lambda s: 8 * (1 + 2 / s) * np.exp(-0.003 * s) / (s * (1 + 0.03 * s))


def bisect(fn, a, b, iters=100):
    """Log-domain bisection on an analytic real function with a sign change in [a, b]."""
    fa = fn(a)
    for _ in range(iters):
        m = np.sqrt(a * b)
        fm = fn(m)
        if np.sign(fm) == np.sign(fa):
            a, fa = m, fm
        else:
            b = m
    return np.sqrt(a * b)


def reference(L):
    """Analytic crossings on 0.05-200 Hz, 200000 log points, roots refined analytically."""
    f = np.logspace(np.log10(0.05), np.log10(200.0), 200000)
    w = 2 * np.pi * f
    Lg = L(1j * w)
    Lf = lambda x: L(1j * x)

    # gain crossovers: |L| = 1
    g = np.abs(Lg) - 1.0
    gc = []
    for i in np.where(np.sign(g[:-1]) != np.sign(g[1:]))[0]:
        wc = bisect(lambda x: abs(Lf(x)) - 1.0, w[i], w[i + 1])
        pm = np.mod(np.degrees(np.angle(Lf(wc))) + 180.0, 360.0)
        if pm > 180.0:
            pm -= 360.0
        gc.append((wc / (2 * np.pi), pm, np.radians(pm) / wc))

    # phase crossovers: Im(L) = 0 with Re(L) < 0  <=>  angle(L) = -180 + k*360
    im = Lg.imag
    pc = []
    for i in np.where(np.sign(im[:-1]) != np.sign(im[1:]))[0]:
        wp = bisect(lambda x: Lf(x).imag, w[i], w[i + 1])
        if Lf(wp).real < 0:
            pc.append((wp / (2 * np.pi), -20 * np.log10(abs(Lf(wp)))))
    return gc, pc


def summarise(gc, pc, lo=None, hi=None):
    inb = (lambda f: True) if lo is None else (lambda f: lo <= f <= hi)
    G = [c for c in gc if inb(c[0])]
    P = [p for p in pc if inb(p[0])]
    return dict(
        gm=min(p[1] for p in P) if P else np.inf,
        pm=min(c[1] for c in G) if G else NAN,
        dm=min(c[2] for c in G) * 1e3 if G else NAN,
        n=len(G), np=len(P),
        fg=[c[0] for c in G], fp=[p[0] for p in P],
    )


def repo(L, w):
    r = margins(w, L(1j * w))
    cross = r['crossings']
    gm = NAN if r['gm_db'] is None else float(r['gm_db'])
    gm = np.inf if np.isnan(gm) else gm
    pm = NAN if r['pm_deg'] is None else float(r['pm_deg'])
    dm = NAN if r['dm_s'] is None else float(r['dm_s']) * 1e3
    list_pm = min(c['pm_deg'] for c in cross) if cross else NAN
    list_dm = min(c['dm_s'] for c in cross) * 1e3 if cross else NAN
    if not (np.isnan(list_pm) and np.isnan(pm)) and abs(list_pm - pm) > 1e-9:
        print('WARNING repo top-level pm != min over crossings list', pm, list_pm)
    return dict(gm=gm, pm=pm, dm=dm, n=len(cross),
                np=len(r['phase_crossings']),
                fg=[c['f_c'] for c in cross],
                fp=[p['f'] for p in r['phase_crossings']])


def compare(ref, rep):
    bad = []
    if np.isinf(ref['gm']) or np.isinf(rep['gm']):
        if not (np.isinf(ref['gm']) and np.isinf(rep['gm'])):
            bad.append('GM')
    elif abs(ref['gm'] - rep['gm']) > TOL_GM:
        bad.append('GM')
    for key, tol in (('pm', TOL_PM), ('dm', TOL_DM_MS)):
        a, b = ref[key], rep[key]
        if np.isnan(a) or np.isnan(b):
            if not (np.isnan(a) and np.isnan(b)):
                bad.append(key.upper())
        elif abs(a - b) > tol:
            bad.append(key.upper())
    if ref['n'] != rep['n']:
        bad.append('N_gc')
    return bad


def fmt(x, nd=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return 'n/a'
    if np.isinf(x):
        return 'inf'
    return f'{x:.{nd}f}'


def fl(xs, nd=1):
    return '[' + ', '.join(f'{x:.{nd}f}' for x in xs) + ']' if xs else '[]'


cases = [('A', 1 / 800), ('A', 1 / 400), ('A', 1 / 266.67), ('B', None), ('C', None)]
f_bins = np.logspace(np.log10(0.2), np.log10(60.0), int(round(40 * np.log10(300.0))) + 1)
w_bins = 2 * np.pi * f_bins

rows1, rows2, detail = [], [], []
for name, T in cases:
    L = make_case(name, T)
    label = f'{name}'
    Tstr = 'n/a' if T is None else f'{T:.6f}'
    gc, pc = reference(L)
    full = summarise(gc, pc)
    inb = summarise(gc, pc, 0.2, 60.0)
    rep = repo(L, w_bins)
    bad = compare(inb, rep)
    verdict = 'AGREE' if not bad else 'DISAGREE (' + ','.join(bad) + ')'
    oob = (full['n'] != inb['n']) or (full['np'] != inb['np'])
    if oob:
        verdict += ' [out-of-band crossings exist in full range]'
    print(label, Tstr, 'full', full['gm'], full['pm'], full['dm'], full['n'], full['np'],
          '| inband', inb['gm'], inb['pm'], inb['dm'], inb['n'], inb['np'],
          '| repo', rep['gm'], rep['pm'], rep['dm'], rep['n'], rep['np'], '|', verdict)

    rows1.append(f"| {label} | {Tstr} | {fmt(full['gm'])} | {fmt(full['pm'])} | {fmt(full['dm'])} | "
                 f"{full['n']} | {full['np']} | {fmt(inb['gm'])} | {fmt(inb['pm'])} | {fmt(inb['dm'])} | "
                 f"{inb['n']} | {inb['np']} |")
    rows2.append(f"| {label} | {Tstr} | {fmt(inb['gm'])} / {fmt(rep['gm'])} | "
                 f"{fmt(inb['pm'])} / {fmt(rep['pm'])} | {fmt(inb['dm'])} / {fmt(rep['dm'])} | "
                 f"{inb['n']} / {rep['n']} | {verdict} |")
    detail.append(f"- Case {label}, T={Tstr}: ref gain-xover Hz (in-band) {fl(inb['fg'])}; "
                  f"repo {fl(rep['fg'])}. Ref full-range gain-xover Hz {fl(full['fg'])}. "
                  f"Ref phase-xover Hz (in-band) {fl(inb['fp'])}; repo {fl(rep['fp'])}. "
                  f"Ref phase-xover Hz (full) {fl(full['fp'])}.")

md = []
md.append('# Second-key stability margin check (stage 2, S37)')
md.append('')
md.append('Independent re-implementation of the margin definitions (`margins_est.margins` was only '
          'introspected for signature and return keys; its source was not used).')
md.append('')
md.append('Reference: analytic L on 200000 log points, 0.05-200 Hz; sign changes of |L|-1 (gain '
          'crossovers) and of Im(L) with Re(L)<0 (phase crossovers, equivalent to angle = -180 + k*360); '
          'roots refined by log-domain bisection on the analytic expression. PM wrapped into (-180, 180]; '
          'DM = PM[rad]/w_c; GM = -20 log10|L| at phase crossovers; min over crossings.')
md.append('Repo: `margins(w, L)` with defaults, fed 100 samples at 40 bins/decade over 0.2-60 Hz.')
md.append('Tolerances: GM 1 dB, PM 3 deg, DM 0.3 ms, identical gain-crossover count inside 0.2-60 Hz.')
md.append('')
md.append('## Reference values')
md.append('')
md.append('| Case | T [s] | GM full [dB] | PM full [deg] | DM full [ms] | N_gc full | N_pc full | '
          'GM in-band | PM in-band | DM in-band [ms] | N_gc in-band | N_pc in-band |')
md.append('|---|---|---|---|---|---|---|---|---|---|---|---|')
md += rows1
md.append('')
md.append('## Reference (in-band) vs repo')
md.append('')
md.append('| Case | T [s] | GM ref / repo [dB] | PM ref / repo [deg] | DM ref / repo [ms] | '
          'N_gc ref / repo | Verdict |')
md.append('|---|---|---|---|---|---|---|')
md += rows2
md.append('')
md.append('## Crossing detail')
md.append('')
md += detail
md.append('')
text = '\n'.join(md) + '\n'
with open(OUT, 'w') as fh:
    fh.write(text)
print('wrote', OUT)
