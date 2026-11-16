#!/usr/bin/env python3
"""Second-key check of the motor output map and the allocator roll gain.

Usage: python3 a22_second_key.py <flight.ulg> <out.md>

Reads only the ULog (pyulog) and scipy. Writes a markdown report to <out.md>
and prints the same text. Independent of any other analysis script.
"""
import os
import sys

import numpy as np
from pyulog import ULog
from scipy import signal

SCALE = 2700.0          # nominal rotor speed at control = 1 (rad/s)
WIN_S = (52.0, 82.0)    # multisine injection window, s
BAND_HZ = (2.0, 10.0)   # zero-phase Butterworth band for the regression
FS_GRID = 400.0         # uniform regression grid (Hz)
BIN_CENTERS = [0.05, 0.10, 0.15, 0.20, 0.25]
BIN_HALF = 0.0125
MOTORS = range(4)
AXES = range(3)
COEF_TARGET = 0.23      # reference per-motor roll coefficient
RATIO_TARGET = 0.769    # reference output-map ratio at hover
TOL = 0.10


def topics(ulog, name):
    return [d.data for d in ulog.data_list if d.name == name]


def window_us(mode, t_ref):
    """Absolute timestamp bounds (us) of the injection window.

    mode 'rel': seconds after the ULog start timestamp (primary).
    mode 'abs': seconds on the raw PX4 timestamp axis (sensitivity check).
    """
    base = t_ref if mode == 'rel' else 0.0
    return base + WIN_S[0] * 1e6, base + WIN_S[1] * 1e6


def fit_map(c, y):
    sq = np.sqrt(np.clip(c, 0.0, None))
    k_sqrt = np.sum(y * sq) / np.sum(sq * sq)
    k_lin = np.sum(y * c) / np.sum(c * c)
    A = np.column_stack([sq, np.ones_like(sq)])
    (a_aff, b_aff), *_ = np.linalg.lstsq(A, y, rcond=None)
    preds = {
        'sqrt y=k*sqrt(c)': k_sqrt * sq,
        'linear y=k*c': k_lin * c,
        'affine-sqrt y=a*sqrt(c)+b': a_aff * sq + b_aff,
    }
    sst = np.sum((y - y.mean()) ** 2)
    stats = {}
    for name, yh in preds.items():
        sse = np.sum((y - yh) ** 2)
        stats[name] = (np.sqrt(sse / len(y)), 1.0 - sse / sst)
    pos = (c > 0.01) & (y > 1.0)
    p_exp = np.polyfit(np.log(c[pos]), np.log(y[pos]), 1)[0]
    return dict(k_sqrt=k_sqrt, k_lin=k_lin, a=a_aff, b=b_aff,
                stats=stats, p=p_exp)


def main(log_path, out_path):
    u = ULog(log_path)
    t_ref = float(u.start_timestamp)
    L = []

    def emit(s=''):
        L.append(s)
        print(s)

    # Airborne span from vehicle_land_detected.
    land = topics(u, 'vehicle_land_detected')[0]
    tl = land['timestamp'].astype(float)
    air_t = tl[land['landed'] == 0]
    a0, a1 = air_t[0], air_t[-1]

    # Commanded motor controls.
    mot = topics(u, 'actuator_motors')[0]
    tm = mot['timestamp'].astype(float)
    ctrl = np.column_stack([mot['control[%d]' % i] for i in MOTORS]).astype(float)

    # Rotor-speed instance of actuator_outputs (output[0..3] in rad/s).
    outs = [d for d in topics(u, 'actuator_outputs')
            if np.max(np.column_stack([d['output[%d]' % i] for i in MOTORS])) > 500.0]
    if not outs:
        raise SystemExit('no actuator_outputs instance with rotor speeds')
    out = outs[0]
    to = out['timestamp'].astype(float)
    Os = np.column_stack([out['output[%d]' % i] for i in MOTORS]).astype(float)
    n_all = len(to)
    n_invalid = [int((Os[:, i] <= 300.0).sum()) for i in MOTORS]

    # Nearest-timestamp pairing over the airborne part.
    air = (tm >= a0) & (tm <= a1)
    ta = tm[air]
    C = ctrl[air]
    O = np.zeros((len(ta), 4))
    dt_pair_ms = np.zeros(len(ta))
    for i in MOTORS:
        vi = Os[:, i] > 300.0
        ti = to[vi]
        oi = Os[vi, i]
        k = np.clip(np.searchsorted(ti, ta), 1, len(ti) - 1)
        j = np.where(ta - ti[k - 1] < ti[k] - ta, k - 1, k)
        O[:, i] = oi[j]
        if i == 0:
            dt_pair_ms = np.abs(ti[j] - ta) * 1e-3

    emit('# A-22 second-key check (independent, from the ULog only)')
    emit('')
    emit('Log: %s' % log_path)
    emit('Log start timestamp: %.3f s (primary time axis = seconds after this).' % (t_ref * 1e-6))
    emit('Airborne (vehicle_land_detected.landed == 0): %.2f s to %.2f s after log start, %d motor samples.'
         % ((a0 - t_ref) * 1e-6, (a1 - t_ref) * 1e-6, air.sum()))
    emit('actuator_outputs instance: %d samples, median rate %.1f Hz; pairing |dt| for motor 0: median %.1f ms, max %.1f ms.'
         % (len(to), 1e6 / np.median(np.diff(to)), np.median(dt_pair_ms), dt_pair_ms.max()))
    emit('Zero-filled output rows (output[i] < 300 rad/s) excluded per motor, out of %d rows: %s.'
         % (n_all, ', '.join(str(v) for v in n_invalid)))
    emit('Airborne output max per motor (rad/s): %s' % ', '.join('%.1f' % v for v in O.max(axis=0)))
    emit('')

    # ---------------- Section 1: static output map ----------------
    emit('## 1. Static output map (airborne, all samples)')
    for i in MOTORS:
        c = C[:, i]
        y = O[:, i]
        f = fit_map(c, y)
        emit('Motor %d: k_sqrt = %.1f rad/s (k/2700 = %.3f), k_lin = %.1f, affine a = %.1f b = %.1f, power exponent p = %.3f'
             % (i, f['k_sqrt'], f['k_sqrt'] / SCALE, f['k_lin'], f['a'], f['b'], f['p']))
        parts = ['%s rmse %.1f R2 %.4f' % (n, s[0], s[1]) for n, s in f['stats'].items()]
        emit('  fit quality: ' + '; '.join(parts))
        best = min(f['stats'], key=lambda n: f['stats'][n][0])
        emit('  best simple map (lowest rmse): %s' % best)
        for ctr in BIN_CENTERS:
            m = np.abs(c - ctr) < BIN_HALF
            if m.sum() == 0:
                emit('  bin %.2f: no samples' % ctr)
                continue
            mc = c[m].mean()
            my = y[m].mean()
            emit('  bin %.2f n=%6d mean_c=%.4f mean_out=%8.1f ratio=out/(sqrt(c)*2700)=%.4f'
                 % (ctr, m.sum(), mc, my, my / (np.sqrt(mc) * SCALE)))
    emit('')

    emit('## 1b. Hover window means and output ratio')
    hover_ratio_rel = None
    for mode in ('rel', 'abs'):
        lo, hi = window_us(mode, t_ref)
        w = (ta >= lo) & (ta <= hi)
        if w.sum() == 0:
            emit('mode %s: no airborne samples in window' % mode)
            continue
        Cw, Ow = C[w], O[w]
        mc = Cw.mean(axis=0)
        mo = Ow.mean(axis=0)
        ratio_i = mo / (np.sqrt(mc) * SCALE)
        pooled = Ow.mean() / (np.sqrt(Cw.mean()) * SCALE)
        persample = Ow.mean() / (np.sqrt(Cw).mean() * SCALE)
        if mode == 'rel':
            hover_ratio_rel = ratio_i.mean()
        emit('mode %s: window %.2f s to %.2f s on airborne samples, n=%d (span %.2f to %.2f s)'
             % (mode, lo * 1e-6 - (t_ref * 1e-6 if mode == 'rel' else 0.0),
                hi * 1e-6 - (t_ref * 1e-6 if mode == 'rel' else 0.0), w.sum(),
                (ta[w][0] - t_ref) * 1e-6, (ta[w][-1] - t_ref) * 1e-6))
        for i in MOTORS:
            emit('  motor %d: mean control %.4f, mean output %.1f rad/s, ratio %.4f'
                 % (i, mc[i], mo[i], ratio_i[i]))
        emit('  mean of per-motor ratios %.4f; pooled ratio of means %.4f; per-sample mean-of-sqrt ratio %.4f'
             % (ratio_i.mean(), pooled, persample))
    emit('')

    # ---------------- Section 1c: quasi-static map ----------------
    def tavg(t, x, centers, half=0.25e6):
        cs = np.concatenate([[0.0], np.cumsum(x)])
        lo = np.searchsorted(t, centers - half)
        hi = np.searchsorted(t, centers + half)
        n = hi - lo
        return np.where(n > 0, (cs[hi] - cs[lo]) / np.maximum(n, 1), np.nan)

    emit('## 1c. Quasi-static map: control averaged over 0.5 s, evaluated at output timestamps')
    for i in MOTORS:
        oa = (to >= a0) & (to <= a1) & (Os[:, i] > 300.0)
        tq_out = to[oa]
        cs_i = tavg(tm, ctrl[:, i], tq_out)
        yv = Os[oa, i]
        ok = np.isfinite(cs_i)
        f = fit_map(cs_i[ok], yv[ok])
        emit('Motor %d (n=%d): k_sqrt/2700 = %.3f, k_lin/2700 = %.3f, affine a = %.1f b = %.1f, best rmse map: %s'
             % (i, ok.sum(), f['k_sqrt'] / SCALE, f['k_lin'] / SCALE, f['a'], f['b'],
                min(f['stats'], key=lambda q: f['stats'][q][0])))
        emit('  fit quality: ' + '; '.join('%s rmse %.1f R2 %.4f' % (q, sv[0], sv[1]) for q, sv in f['stats'].items()))
        row = []
        for ctr in BIN_CENTERS:
            m = ok & (np.abs(cs_i - ctr) < BIN_HALF)
            if m.sum() > 0:
                mc = cs_i[m].mean()
                my = yv[m].mean()
                row.append('bin %.2f n=%d ratio=%.3f' % (ctr, m.sum(), my / (np.sqrt(mc) * SCALE)))
        emit('  ' + '; '.join(row))
    emit('')

    # ---------------- Section 2: allocator roll gain ----------------
    tq = topics(u, 'vehicle_torque_setpoint')[0]
    tt = tq['timestamp'].astype(float)
    XYZ = [tq['xyz[%d]' % ax].astype(float) for ax in AXES]
    sos = signal.butter(4, BAND_HZ, btype='bandpass', fs=FS_GRID, output='sos')

    def prep(x):
        return signal.sosfiltfilt(sos, x - x.mean())

    def roll_fit(t_lo, t_hi):
        grid = np.arange(t_lo, t_hi, 1e6 / FS_GRID)
        cg = [np.interp(grid, tm, ctrl[:, i]) for i in MOTORS]
        xg = [np.interp(grid, tt, XYZ[ax]) for ax in AXES]
        X = np.column_stack([prep(x) for x in xg])
        rows = []
        for i in MOTORS:
            y = prep(cg[i])
            coef, *_ = np.linalg.lstsq(X, y, rcond=None)
            r2 = 1.0 - np.sum((y - X @ coef) ** 2) / np.sum(y ** 2)
            x0 = X[:, 0]
            single = np.dot(x0, y) / np.dot(x0, x0)
            rows.append(dict(coef=coef, r2=r2, single=single))
        return rows

    emit('## 2. Allocator roll gain (least squares, 2-10 Hz zero-phase Butterworth order 4)')
    emit('Joint fit: control_i ~ b0*xyz[0] + b1*xyz[1] + b2*xyz[2]; single fit: control_i ~ s*xyz[0].')
    rows_rel = None
    for mode in ('rel', 'abs'):
        lo, hi = window_us(mode, t_ref)
        rows = roll_fit(lo, hi)
        if mode == 'rel':
            rows_rel = rows
        emit('mode %s:' % mode)
        for i, r in enumerate(rows):
            b = r['coef']
            emit('  motor %d: b_roll(xyz0) = %+.4f | b_pitch(xyz1) = %+.4f | b_yaw(xyz2) = %+.4f | joint R2 %.4f | single-axis roll %+.4f'
                 % (i, b[0], b[1], b[2], r['r2'], r['single']))
    emit('')

    # ---------------- Section 3: summary and comparison ----------------
    emit('## 3. Summary and comparison (primary convention: seconds after log start)')
    mags = np.array([abs(r['coef'][0]) for r in rows_rel])
    coef_ok = np.abs(mags / COEF_TARGET - 1.0) <= TOL
    ratio_ok = abs(hover_ratio_rel / RATIO_TARGET - 1.0) <= TOL
    emit('Per-motor roll coefficient magnitudes: %s' % ', '.join('%.4f' % m for m in mags))
    emit('Per-motor roll coefficient signs: %s' % ', '.join('%+d' % np.sign(r['coef'][0]) for r in rows_rel))
    emit('Coefficient vs 0.23: relative diffs %s; all within 10 %%: %s'
         % (', '.join('%+.1f%%' % (100 * (m / COEF_TARGET - 1)) for m in mags), bool(coef_ok.all())))
    emit('Output-map ratio at hover (mean of per-motor ratios of means): %.4f vs 0.769, relative diff %+.1f %%; within 10 %%: %s'
         % (hover_ratio_rel, 100 * (hover_ratio_rel / RATIO_TARGET - 1), bool(ratio_ok)))
    verdict = 'AGREE' if (coef_ok.all() and ratio_ok) else 'DISAGREE'
    emit('VERDICT: %s' % verdict)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, 'w') as fh:
        fh.write('\n'.join(L) + '\n')


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise SystemExit('usage: a22_second_key.py <flight.ulg> <out.md>')
    main(sys.argv[1], sys.argv[2])
