#!/usr/bin/env python3
"""S44 motor-command chatter characterisation on a raw PX4 ULog.

Usage: motor_chatter_s44.py LOG OUT_MD

Times are seconds since boot, from each topic's `timestamp` (us / 1e6).
Analysis window is [52, 82) s since boot.

Motor command   : actuator_motors.control[0]
Measured proxy  : esc_status.esc[0].esc_rpm -> omega = rpm * 2*pi/60 (rad/s),
                  u_meas = (omega / 2700)^2. The unit of esc_rpm (mechanical or
                  electrical) is not in the log; the script prints a heuristic
                  verdict only, which must be treated as UNVERIFIED.
"""
import os
import sys

import numpy as np
from pyulog import ULog

LOG, OUT = sys.argv[1], sys.argv[2]
W0, W1 = 52.0, 82.0
OMEGA_MAX = 2700.0
LAG_MAX_S = 0.05   # cross-correlation search range, +/- seconds
HP_S = 0.10        # high-pass width: residual after subtracting moving average

lines = []
notes = []


def add(s=''):
    lines.append(s)


def tsec(d):
    return d['timestamp'].astype(np.float64) * 1e-6


def win(t):
    return (t >= W0) & (t < W1)


def fmt(x, nd=4):
    x = float(x)
    return 'n/a' if not np.isfinite(x) else f'{x:.{nd}g}'


def welch(y, fs, nperseg=4096):
    nseg = min(nperseg, len(y))
    step = nseg // 2
    w = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(nseg) / nseg)
    acc = []
    for s in range(0, len(y) - nseg + 1, step):
        seg = y[s:s + nseg]
        acc.append(np.abs(np.fft.rfft((seg - seg.mean()) * w)) ** 2)
    P = np.mean(acc, axis=0) / (fs * np.sum(w ** 2))
    P[1:-1] *= 2.0
    f = np.fft.rfftfreq(nseg, 1.0 / fs)
    return f, P, len(acc)


def uniform(t, y, fs):
    g = np.arange(t[0], t[-1], 1.0 / fs)
    return g, np.interp(g, t, y)


def detrend(y):
    tt = np.arange(len(y))
    return y - np.polyval(np.polyfit(tt, y, 1), tt)


def highpass(y, n):
    n = max(3, int(n))
    return y - np.convolve(y, np.ones(n) / n, mode='same')


def runs(mask):
    if not mask.any():
        return np.array([], dtype=int)
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return np.flatnonzero(d == -1) - np.flatnonzero(d == 1)


def xcorr_lag(a, b, max_lag):
    """Lag k (samples) maximising mean(a[t] * b[t + k]) on standardised signals.
    Positive k: measured b lags command a."""
    a = (a - a.mean()) / a.std()
    b = (b - b.mean()) / b.std()
    n = len(a)
    best_r, best_k = -np.inf, 0
    for k in range(-max_lag, max_lag + 1):
        if k >= 0:
            x, y = a[:n - k], b[k:]
        else:
            x, y = a[-k:], b[:n + k]
        r = float(np.mean(x * y))
        if r > best_r:
            best_r, best_k = r, k
    return best_k, best_r


ul = ULog(LOG)


def get(name):
    try:
        return ul.get_dataset(name).data
    except Exception as e:
        sys.exit(f'required topic {name} unavailable: {e}')


am = get('actuator_motors')
es = get('esc_status')
ir = get('indi_rate_status')

t_am = tsec(am)
t_es = tsec(es)
t_ir = tsec(ir)

# ---- logged rates in window ----
rate_rows = []
for name, t in [('actuator_motors', t_am), ('esc_status', t_es), ('indi_rate_status', t_ir)]:
    tw = t[win(t)]
    dt = np.diff(tw)
    rate_rows.append((name, len(tw), len(tw) / (W1 - W0), 1.0 / np.median(dt),
                      np.median(dt) * 1e3, dt.max() * 1e3))

add('# S44 motor-command chatter: a23_test / indi_g1derived')
add()
add(f'- Log: `{LOG}`')
add('- Time base: seconds since boot (topic `timestamp` / 1e6).')
add(f'- Window: [{W0:.1f}, {W1:.1f}) s since boot.')
add('- Motor command: `actuator_motors.control[0]`.')
add('- Measured proxy: `esc_status.esc[0].esc_rpm`, omega = rpm * 2*pi/60, '
    'u_meas = (omega / 2700)^2 (2700 rad/s taken from the task, not verified).')
add()
add('## Logged rates (window)')
add()
add('| topic | samples in window | mean rate Hz (n/30 s) | median-dt rate Hz | median dt ms | max gap ms |')
add('|---|---|---|---|---|---|')
for name, n, r_mean, r_med, dt_med, gap in rate_rows:
    add(f'| {name} | {n} | {r_mean:.2f} | {r_med:.2f} | {dt_med:.4f} | {gap:.3f} |')
add()

# ---- 1. motor command ----
mm = win(t_am)
tm = t_am[mm]
cm = am['control[0]'][mm].astype(np.float64)
if not np.all(np.isfinite(cm)):
    notes.append('actuator_motors control[0] has non-finite samples in window (dropped).')
    ok = np.isfinite(cm)
    tm, cm = tm[ok], cm[ok]

hist, _ = np.histogram(cm, bins=10, range=(0.0, 1.0))
n_oob = int(np.sum((cm < 0.0) | (cm > 1.0)))
fs_m = 1.0 / np.median(np.diff(tm))
g_m, cg = uniform(tm, cm, fs_m)
cg = detrend(cg)
f, P, nseg_m = welch(cg, fs_m)
pos = f > 0
tot = P[pos].sum()
frac50 = P[f > 50.0].sum() / tot
frac_nyq = P[f >= 0.9 * fs_m / 2].sum() / tot
band = f >= 0.5
ipk = int(np.argmax(np.where(band, P, -np.inf)))
fpk = float(f[ipk])
pk_ratio = float(P[ipk] / np.median(P[band]))

dcm = np.diff(cm)
nz = dcm != 0
sgn = np.sign(dcm)
both = nz[1:] & nz[:-1]
flip_frac = float(np.mean((sgn[1:] * sgn[:-1])[both] < 0)) if both.any() else float('nan')
zero_frac = float(np.mean(~nz))
x0 = cm - cm.mean()
r1 = float(np.mean(x0[:-1] * x0[1:]) / np.mean(x0 ** 2))

low = cm < 0.005
rl = runs(low)
run_mean = float(rl.mean()) if rl.size else float('nan')
run_med = float(np.median(rl)) if rl.size else float('nan')
run_len1 = float(np.mean(rl == 1)) if rl.size else float('nan')

add('## 1. actuator_motors control[0]')
add()
add(f'- Samples in window: {cm.size}; fs (median dt) {fs_m:.2f} Hz, Nyquist {fs_m / 2:.1f} Hz.')
add(f'- mean {cm.mean():.4g}, std {cm.std():.4g}, min {cm.min():.4g}, max {cm.max():.4g}.')
add(f'- Samples outside [0, 1]: {n_oob}.')
add()
add('Histogram, 10 bins over [0, 1]:')
add()
add('| bin | count | fraction |')
add('|---|---|---|')
for i, h in enumerate(hist):
    add(f'| [{i / 10:.1f}, {(i + 1) / 10:.1f}) | {h} | {h / cm.size:.4g} |')
add()
add(f'Welch PSD (Hann, 4096-sample segments, 50% overlap, {nseg_m} segments, linear detrend, '
    f'uniform grid at {fs_m:.2f} Hz):')
add(f'- Dominant frequency (search f >= 0.5 Hz): {fpk:.3f} Hz; peak / median over band: {pk_ratio:.4g}.')
add(f'- Fraction of power above 50 Hz (of f > 0): {frac50:.4g}.')
add(f'- Fraction of power in top 10% of band (f >= 0.9 * Nyquist = {0.9 * fs_m / 2:.1f} Hz): {frac_nyq:.4g}.')
add()
add('Sample-to-sample behaviour:')
add(f'- Fraction of consecutive sample pairs where the difference reverses sign: {flip_frac:.4g} '
    f'(1.0 = strict alternation every sample).')
add(f'- Fraction of zero first differences: {zero_frac:.4g}.')
add(f'- Lag-1 autocorrelation of control[0]: {r1:.4g}.')
add()
add(f'Run length of consecutive samples with control[0] < 0.005: runs = {rl.size}, '
    f'mean length = {run_mean:.4g} samples, median = {run_med:.4g}, '
    f'fraction of runs of length 1 = {run_len1:.4g}.')
add(f'- Fraction of window samples with control[0] < 0.005: {low.mean():.4g}.')
add()

# ---- 2. ESC rpm vs command ----
me = win(t_es)
te = t_es[me]
rpm = es['esc[0].esc_rpm'][me].astype(np.float64)
ok = np.isfinite(rpm)
te, rpm = te[ok], rpm[ok]
omega = rpm * 2.0 * np.pi / 60.0
um = (omega / OMEGA_MAX) ** 2
fs_e = 1.0 / np.median(np.diff(te))
ratio_max = float(np.max(omega) / OMEGA_MAX)
if ratio_max > 1.5:
    verdict = (f'SUSPECT eRPM: max rpm * 2pi/60 / 2700 = {ratio_max:.3g} (> 1.5), '
               'so esc_rpm may carry a pole-pair multiple. UNVERIFIED.')
else:
    verdict = (f'Consistent with mechanical rpm: max omega / 2700 = {ratio_max:.3g}. '
               'Not proven (pole count not in log). UNVERIFIED.')

lo = max(te[0], tm[0])
hi = min(te[-1], tm[-1])
g = np.arange(lo, hi, 1.0 / fs_e)
cmg = np.interp(g, tm, cm)
umg = np.interp(g, te, um)
L = int(round(LAG_MAX_S * fs_e))
lag_f, r_f = xcorr_lag(detrend(cmg), detrend(umg), L)
n_hp = HP_S * fs_e
lag_h, r_h = xcorr_lag(highpass(detrend(cmg), n_hp), highpass(detrend(umg), n_hp), L)

add('## 2. esc_status esc[0] vs command')
add()
add(f'- esc_status rate: samples in window {te.size}, median-dt rate {fs_e:.2f} Hz.')
add(f'- esc[0].esc_rpm raw: min {rpm.min():.6g}, max {rpm.max():.6g}, '
    f'mean {rpm.mean():.6g}, std {rpm.std():.4g}; fraction zero {np.mean(rpm == 0):.4g}.')
add(f'- Unit check: {verdict}')
add(f'- omega (rad/s) mean {omega.mean():.4g}, std {omega.std():.4g}.')
add()
add('| quantity | mean | std |  samples |')
add('|---|---|---|---|')
add(f'| control[0] (raw samples, actuator_motors) | {cm.mean():.4g} | {cm.std():.4g} | {cm.size} |')
add(f'| u_meas = (omega/2700)^2 (raw samples, esc_status) | {um.mean():.4g} | {um.std():.4g} | {um.size} |')
add(f'| control[0] (resampled to esc grid, {fs_e:.1f} Hz) | {cmg.mean():.4g} | {cmg.std():.4g} | {cmg.size} |')
add(f'| u_meas (resampled, same grid) | {umg.mean():.4g} | {umg.std():.4g} | {umg.size} |')
add()
add(f'- mean(u_meas) - mean(control[0]) on the resampled grid: {umg.mean() - cmg.mean():.4g}.')
add(f'- Cross-correlation (detrended, search +/- {LAG_MAX_S * 1e3:.0f} ms): max r = {r_f:.4g} at lag '
    f'{lag_f / fs_e * 1e3:.2f} ms ({lag_f} samples). Positive lag = u_meas lags command.')
add(f'- Cross-correlation (high-pass residual, moving-average width {HP_S * 1e3:.0f} ms): '
    f'max r = {r_h:.4g} at lag {lag_h / fs_e * 1e3:.2f} ms ({lag_h} samples).')
add()

# ---- 3. indi_rate_status ----
mi = win(t_ir)
fields = sorted(k for k in ir.keys() if k not in ('timestamp', 'timestamp_sample'))
motor_like = [k for k in fields if 'motor' in k.lower() or 'actuator' in k.lower()]

add('## 3. indi_rate_status')
add()
add(f'- Fields ({len(fields)}): ' + ', '.join(fields))
add(f'- Fields naming motors/actuators: {motor_like if motor_like else "none"}. '
    'No rotor-speed or motor-domain measured-u / delta-u field is logged; '
    'the fields below are in torque or angular-acceleration units.')
add()
add('| field | mean | std | min | max |')
add('|---|---|---|---|---|')
for k in fields:
    v = ir[k][mi].astype(np.float64)
    if v.size == 0:
        add(f'| {k} | n/a | n/a | n/a | n/a |')
        continue
    add(f'| {k} | {v.mean():.4g} | {v.std():.4g} | {v.min():.4g} | {v.max():.4g} |')
add()

add('## Notes')
add()
add('- No topic in the log carries true rotor speed; esc_status is the only speed source.')
add('- esc_rpm unit (mechanical vs electrical) and the 2700 rad/s scale are UNVERIFIED.')
add('- Resolution of the lag estimate is one sample (about 1.3 ms at the esc rate).')
for nt in notes:
    add(f'- {nt}')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as fh:
    fh.write('\n'.join(lines) + '\n')

print(f'rates: ' + '; '.join(f'{n} n={c} mean={r:.2f}Hz med={m:.2f}Hz' for n, c, r, m, _, _ in rate_rows))
print(f'1 control[0]: fpk={fpk:.3f} Hz ratio={pk_ratio:.4g} frac>50Hz={frac50:.4g} '
      f'flip={flip_frac:.4g} r1={r1:.4g} runs={rl.size} meanrun={run_mean:.4g}')
print(f'2 esc: {verdict}')
print(f'2 means cmd={cmg.mean():.4g} umeas={umg.mean():.4g} std cmd={cmg.std():.4g} umeas={umg.std():.4g}')
print(f'2 xcorr full lag={lag_f / fs_e * 1e3:.2f} ms r={r_f:.4g}; hp lag={lag_h / fs_e * 1e3:.2f} ms r={r_h:.4g}')
print(f'wrote {OUT}')
