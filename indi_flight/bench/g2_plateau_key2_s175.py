#!/usr/bin/env python3
"""G2 phase-plateau gain margin, second key (S175). Independent implementation.

Rule (GATES.md G2 + owner Q13 A), per run, L(f) = |L| dB, arg L deg per accepted bin:
  classic GM  = -20log10|L| at arg L = -180 (phase crossing, linear interpolation in log f)
  plateau GM  = min over bins with |L| < 1 and |arg L + 180| <= 10 deg of -20log10|L|
  reduction   = +20log10|L| for bins (and crossings) with |L| > 1 and arg within 10 deg of -180
  cell pass   = min(classic, plateau) >= 6 and all reductions >= 6; cell value = worst seed.
Data: rate cells results/g2_freeze_s160/<cell>/margins.txt (lines 'f', '|L| dB', 'arg deg', 0.1 resolution);
      attitude cells results/g2_att_freeze_s162/ax?_r???_s?_att.csv (f_hz, L_db, arg_L_deg, accepted).
"""
import ast, csv, glob, math, os, sys
import numpy as np

BAND = 10.0
LIM = 6.0


def analyse(f, ldb, arg):
    f = np.asarray(f, float); ldb = np.asarray(ldb, float); arg = np.asarray(arg, float)
    o = np.argsort(f); f, ldb, arg = f[o], ldb[o], arg[o]
    dev = (arg + 180.0 + 180.0) % 360.0 - 180.0          # arg L + 180 wrapped to (-180, 180]
    near = np.abs(dev) <= BAND
    plateau_bins = [(float(f[i]), float(-ldb[i])) for i in range(len(f)) if near[i] and ldb[i] < 0]
    red_bins = [(float(f[i]), float(ldb[i])) for i in range(len(f)) if near[i] and ldb[i] >= 0]
    # classic crossings: unwrapped phase passes through -180 mod 360
    ph = np.degrees(np.unwrap(np.radians(arg)))
    cross = []
    for i in range(len(f) - 1):
        a, b = ph[i] + 180.0, ph[i + 1] + 180.0
        k0, k1 = math.floor(a / 360.0), math.floor(b / 360.0)
        if k0 == k1 and a != 0 and not (a % 360 == 0):
            continue
        # a crossing exists if a multiple of 360 lies in (a, b] (or [b, a))
        lo, hi = min(a, b), max(a, b)
        m = math.ceil(lo / 360.0)
        while m * 360.0 <= hi:
            tgt = m * 360.0
            if lo <= tgt <= hi and a != b:
                t = (tgt - a) / (b - a)
                lf = math.log(f[i]) + t * (math.log(f[i + 1]) - math.log(f[i]))
                cross.append((math.exp(lf), float(ldb[i] + t * (ldb[i + 1] - ldb[i]))))
            m += 1
    cross = sorted(set((round(x, 9), y) for x, y in cross))
    classic = min([-y for _, y in cross if y < 0], default=None)
    red = [y for _, y in cross if y >= 0] + [y for _, y in red_bins]
    plateau = min([g for _, g in plateau_bins], default=None)
    red_min = min(red, default=None)
    vals = [v for v in (classic, plateau, red_min) if v is not None]
    return dict(classic=classic, plateau=plateau, red=red_min, cross=cross,
                npl=len(plateau_bins), nred=len(red), ok=(min(vals) >= LIM if vals else None),
                worst=min(vals) if vals else None)


def load_rate(path):
    L = open(path).read().splitlines()
    f = ast.literal_eval(L[1][2:].strip())
    l = ast.literal_eval(L[2].split(' dB', 1)[1].strip())
    a = ast.literal_eval(L[3].split('deg', 1)[1].strip())
    assert len(f) == len(l) == len(a), path
    return f, l, a


def load_att(path):
    f, l, a = [], [], []
    for r in csv.DictReader(open(path)):
        if int(float(r['accepted'])):
            f.append(float(r['f_hz'])); l.append(float(r['L_db'])); a.append(float(r['arg_L_deg']))
    return f, l, a


def fmt(x):
    return '-' if x is None else f'{x:.2f}'


def main():
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
    rows = []  # (cell, kind, runs)
    cells = {}
    for p in sorted(glob.glob(os.path.join(base, 'g2_freeze_s160', '*_s[0-9]', 'margins.txt'))):
        d = os.path.basename(os.path.dirname(p))
        cell, seed = d.rsplit('_s', 1)
        cells.setdefault(('rate', cell), {})[seed] = (p, load_rate(p))
    for p in sorted(glob.glob(os.path.join(base, 'g2_att_freeze_s162', 'ax?_r???_s?_att.csv'))):
        b = os.path.basename(p)[:-8]
        cell, seed = b.rsplit('_s', 1)
        cells.setdefault(('att', cell), {})[seed] = (p, load_att(p))
    out = []
    npass = 0
    for (kind, cell), runs in sorted(cells.items()):
        res = {s: analyse(*v[1]) for s, v in sorted(runs.items())}
        cg = min([r['classic'] for r in res.values() if r['classic'] is not None], default=None)
        pg = min([r['plateau'] for r in res.values() if r['plateau'] is not None], default=None)
        rd = min([r['red'] for r in res.values() if r['red'] is not None], default=None)
        vals = [v for v in (cg, pg, rd) if v is not None]
        ok = min(vals) >= LIM
        npass += ok
        src = os.path.relpath(next(iter(runs.values()))[0], base)
        out.append((kind, cell, ','.join(sorted(runs)), cg, pg, rd, ok, src,
                    sum(r['npl'] for r in res.values()), sum(r['nred'] for r in res.values()),
                    {s: (r['classic'], r['plateau']) for s, r in res.items()}))
    print('| kind | cell | seeds | classic GM | plateau GM | reduction | pass | plateau bins (all seeds) | per-seed classic/plateau | source |')
    print('|---|---|---|---|---|---|---|---|---|---|')
    for k, c, s, cg, pg, rd, ok, src, npl, nrd, ps in out:
        per = ' '.join(f'{sd}:{fmt(a)}/{fmt(b)}' for sd, (a, b) in ps.items())
        print(f'| {k} | {c} | {s} | {fmt(cg)} | {fmt(pg)} | {fmt(rd)} | {"PASS" if ok else "FAIL"} | {npl} | {per} | {src} |')
    print(f'\n{len(out)} cells, {npass} pass', file=sys.stderr)


if __name__ == '__main__':
    main()
