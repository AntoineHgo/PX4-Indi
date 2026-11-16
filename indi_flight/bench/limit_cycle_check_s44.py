#!/usr/bin/env python3
"""S44 limit-cycle check on a raw PX4 ULog.

Usage: limit_cycle_check_s44.py LOG OUT_MD [LABEL] [search]

Times are seconds since boot, taken from each topic's `timestamp` (us / 1e6).
Bins are 1 s, starting at the first vehicle_status sample with arming_state == 2.
Analysis window is [52, 82) s since boot. With the optional `search` argument the
30 s window (1 s steps over the armed period) with the most vehicle_angular_velocity
samples is used instead; the fixed 52-82 s window wins ties.
"""
import os
import sys

import numpy as np
from pyulog import ULog

args = [a for a in sys.argv[1:] if a != 'search']
SEARCH = len(args) != len(sys.argv) - 1
LOG, OUT = args[0], args[1]
LABEL = args[2] if len(args) > 2 else os.path.basename(os.path.dirname(LOG))
W_LEN = 30.0
W0 = 52.0
notes = []
lines = []


def add(s=''):
    lines.append(s)


def tsec(d):
    return d['timestamp'].astype(np.float64) * 1e-6


def frac(c, cond):
    v = np.isfinite(c)
    return np.sum(cond & v, axis=0) / np.maximum(v.sum(axis=0), 1)


def mat(d, base, n):
    return np.column_stack([d[f'{base}[{i}]'].astype(np.float64) for i in range(n)])


def fmt(x, nd=4):
    x = float(x) if x is not None else float('nan')
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
    P[1:-1] *= 2.0  # one-sided; DC and Nyquist bins not doubled
    f = np.fft.rfftfreq(nseg, 1.0 / fs)
    return f, P, len(acc)


ul = ULog(LOG)
T_LAST = ul.last_timestamp * 1e-6


def get(name):
    try:
        return ul.get_dataset(name).data
    except Exception as e:  # topic absent from this log
        notes.append(f'NOT COMPUTED: topic `{name}` unavailable ({e})')
        return None


vs = get('vehicle_status')
am = get('actuator_motors')
av = get('vehicle_angular_velocity')
lp = get('vehicle_local_position')
ca = get('control_allocator_status')
ld = get('vehicle_land_detected')
if vs is None or am is None or av is None:
    sys.exit('required topic missing')

t_vs = tsec(vs)
armed = np.flatnonzero(vs['arming_state'] == 2)
if armed.size == 0:
    sys.exit(f'{LOG}: never armed')
T_ARM = float(t_vs[armed[0]])
t_am = tsec(am)
t_av = tsec(av)
T_END = float(max(T_LAST, t_am.max(), t_av.max()))
NB = int(np.floor(T_END - T_ARM)) + 1

ctrl = mat(am, 'control', 4)
xyz = mat(av, 'xyz', 3)
k_am = np.floor(t_am - T_ARM).astype(np.int64)
k_av = np.floor(t_av - T_ARM).astype(np.int64)
RATE = 1.0 / float(np.median(np.diff(t_av[t_av >= T_ARM])))

# ---- 1 s bins over the armed period ----
motor_rows = []
gyro_rows = []
bin_pitch = np.full(NB, np.nan)
for k in range(NB):
    t_k = T_ARM + k
    m = k_am == k
    n = int(m.sum())
    if n:
        c = ctrl[m]
        row = np.concatenate([np.nanmean(c, axis=0), frac(c, c < 0.005), frac(c, c > 0.995)])
    else:
        row = np.full(12, np.nan)
    motor_rows.append((t_k, n, row))
    mg = k_av == k
    ng = int(mg.sum())
    if ng:
        x = xyz[mg]
        x = x - x.mean(axis=0)
        rms = np.sqrt(np.mean(x ** 2, axis=0))
    else:
        rms = np.full(3, np.nan)
    gyro_rows.append((t_k, ng, rms))
    bin_pitch[k] = rms[1]


# ---- analysis window ----
def count_av(t0, t1):
    return int(np.sum((t_av >= t0) & (t_av < t1)))


W_T0 = W0
if SEARCH:
    best_n = count_av(W0, W0 + W_LEN)
    for s in np.arange(T_ARM, T_END - W_LEN, 1.0):
        n_s = count_av(s, s + W_LEN)
        if n_s > best_n:
            best_n, W_T0 = n_s, float(s)
W_T1 = W_T0 + W_LEN
N_WIN = count_av(W_T0, W_T1)
WIN_NOTE = ('max-sample-count search over 1 s steps' if SEARCH else 'fixed 52-82 s')

mw = (t_am >= W_T0) & (t_am < W_T1)
cw = ctrl[mw]
win_motor = np.concatenate([np.nanmean(cw, axis=0), frac(cw, cw < 0.005), frac(cw, cw > 0.995)])

mgw = (t_av >= W_T0) & (t_av < W_T1)
xw = xyz[mgw] - xyz[mgw].mean(axis=0)
win_rms = np.sqrt(np.mean(xw ** 2, axis=0))

# Welch PSD of pitch rate on a uniform grid at the window's median rate.
tw = t_av[mgw]
yw = xyz[mgw, 1]
FS = 1.0 / float(np.median(np.diff(tw)))
g = np.arange(tw[0], tw[-1], 1.0 / FS)
yg = np.interp(g, tw, yw)
tt = np.arange(len(yg)) / FS
yg = yg - np.polyval(np.polyfit(tt, yg, 1), tt)
f, P, NSEG = welch(yg, FS)
keep = (f >= 0.5) & (f < FS / 2)
Pk = P[keep]
ip = int(np.argmax(Pk))
FPK = float(f[keep][ip])
RATIO = float(Pk[ip] / np.median(Pk))
df = float(f[1] - f[0])
sel = keep & (np.abs(f - FPK) <= 0.5)
AMP = float(np.sqrt(2.0 * np.sum(P[sel]) * df))

# control allocator
CA = None
if ca is not None:
    tca = tsec(ca)
    mc = (tca >= W_T0) & (tca < W_T1)
    nc = int(mc.sum())
    if nc:
        ach = float(np.mean(ca['torque_setpoint_achieved'][mc].astype(bool)))
        ut = mat(ca, 'unallocated_torque', 3)[mc]
        CA = (nc, ach, np.nanmean(np.abs(ut), axis=0))
    else:
        notes.append('NOT COMPUTED: control_allocator_status has no samples in window')

# land detected
LD = []
if ld is not None:
    tld = tsec(ld)
    for name, m in [('armed period', tld >= T_ARM), ('window', (tld >= W_T0) & (tld < W_T1))]:
        n = int(m.sum())
        if n:
            LD.append((name, n,
                       float(ld['landed'][m].astype(bool).mean()),
                       float(ld['maybe_landed'][m].astype(bool).mean())))
        else:
            LD.append((name, 0, float('nan'), float('nan')))

# pitch-rate threshold crossing
hit = np.flatnonzero(bin_pitch > 1.0)
CROSS = None
if hit.size:
    k = int(hit[0])
    t_k = T_ARM + k
    z_val, z_src = float('nan'), 'none'
    if lp is not None:
        tlp = tsec(lp)
        ml = (tlp >= t_k) & (tlp < t_k + 1)
        if ml.any():
            z_val, z_src = float(np.mean(lp['z'][ml])), 'mean over bin'
        else:
            j = int(np.argmin(np.abs(tlp - t_k)))
            z_val, z_src = float(lp['z'][j]), f'nearest sample, t={tlp[j]:.3f} s'
    CROSS = (t_k, float(bin_pitch[k]), z_val, z_src)
kmax = int(np.nanargmax(bin_pitch)) if np.isfinite(bin_pitch).any() else None

# ---- markdown ----
add(f'# S44 limit-cycle check: {LABEL}')
add()
add(f'- Log: `{LOG}`')
add(f'- Time base: seconds since boot (topic `timestamp` / 1e6).')
add(f'- First armed sample (vehicle_status.arming_state == 2): t = {T_ARM:.3f} s. '
    f'End of log: t = {T_END:.3f} s. {NB} one-second bins from the armed sample.')
add(f'- vehicle_angular_velocity median logged rate (armed period): {RATE:.2f} Hz, Nyquist {RATE / 2:.1f} Hz.')
add(f'- Analysis window: [{W_T0:.3f}, {W_T1:.3f}) s since boot ({WIN_NOTE}); '
    f'vehicle_angular_velocity samples in window: {N_WIN}.')
add()
add('## 1 and 2. Per-bin motors and body-rate RMS')
add()
add('Motors: mean, lo = fraction < 0.005, hi = fraction > 0.995, for control[0..3].')
add()
add('| t_start s | n | mean0 | mean1 | mean2 | mean3 | lo0 | lo1 | lo2 | lo3 | hi0 | hi1 | hi2 | hi3 |')
add('|' + '---|' * 14)
for t_k, n, row in motor_rows:
    add(f'| {t_k:.3f} | {n} | ' + ' | '.join(fmt(x) for x in row) + ' |')
add()
add('Body rate: RMS of each axis (rad/s) after removing the bin mean.')
add()
add('| t_start s | n | rms x (roll) | rms y (pitch) | rms z (yaw) |')
add('|---|---|---|---|---|')
for t_k, n, rms in gyro_rows:
    add(f'| {t_k:.3f} | {n} | ' + ' | '.join(fmt(x) for x in rms) + ' |')
add()
add(f'## Window [{W_T0:.3f}, {W_T1:.3f}) s since boot')
add()
add('Motors over window (mean / lo / hi):')
add()
add('| motor | mean | lo (<0.005) | hi (>0.995) |')
add('|---|---|---|---|')
for i in range(4):
    add(f'| control[{i}] | {fmt(win_motor[i])} | {fmt(win_motor[4 + i])} | {fmt(win_motor[8 + i])} |')
add()
add(f'Body-rate RMS over window (mean removed): x {fmt(win_rms[0])}, y {fmt(win_rms[1])}, z {fmt(win_rms[2])} rad/s.')
add()
add(f'3. Pitch-rate PSD (Welch, Hann, 4096-sample segments, 50% overlap, {NSEG} segments, '
    f'linear detrend), logged rate {FS:.2f} Hz, Nyquist {FS / 2:.1f} Hz. Search band [0.5, Nyquist).')
add(f'- Dominant frequency: {FPK:.3f} Hz')
add(f'- PSD peak / median over band: {RATIO:.4g}')
add(f'- Sinusoid amplitude estimate, sqrt(2 * band power within +/-0.5 Hz of peak): {AMP:.4g} rad/s')
add()
add('4. control_allocator_status over window:')
if CA:
    add(f'- samples: {CA[0]}; fraction torque_setpoint_achieved true: {CA[1]:.4g}')
    add(f'- mean abs unallocated_torque[0..2]: {fmt(CA[2][0])}, {fmt(CA[2][1])}, {fmt(CA[2][2])}')
else:
    add('- NOT COMPUTED (no samples in window)')
add()
add('5. vehicle_land_detected (sample fractions):')
add()
add('| range | samples | landed | maybe_landed |')
add('|---|---|---|---|')
for name, n, la, ma in LD:
    add(f'| {name} | {n} | {fmt(la)} | {fmt(ma)} |')
add()
add('## Pitch-rate bin RMS > 1 rad/s (whole armed period)')
add()
if CROSS:
    t_k, rms_v, z_val, z_src = CROSS
    add(f'- First exceedance: bin starting t = {t_k:.3f} s (bin RMS {rms_v:.4g} rad/s).')
    add(f'- vehicle_local_position.z = {z_val:.4g} m ({z_src}); altitude = -z = {-z_val:.4g} m (NED).')
else:
    add('- Never exceeded.')
if kmax is not None:
    add(f'- Largest pitch-rate bin RMS: {bin_pitch[kmax]:.4g} rad/s at t = {T_ARM + kmax:.3f} s.')
add()
add('## Notes')
add()
add('- All statistics are sample-based over the logged topics; nothing was interpolated except the '
    'uniform grid for the Welch PSD.')
for nt in notes:
    add(f'- {nt}')
if not notes:
    add('- Everything requested was computed.')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as fh:
    fh.write('\n'.join(lines) + '\n')

# compact stdout
print(f'[{LABEL}] armed t={T_ARM:.3f} end={T_END:.3f} bins={NB} rate={RATE:.2f} Hz')
print(f'[{LABEL}] window [{W_T0:.3f},{W_T1:.3f}) ({WIN_NOTE}) samples={N_WIN}')
print(f'[{LABEL}] window motor mean {np.round(win_motor[:4], 4)} lo {np.round(win_motor[4:8], 4)} hi {np.round(win_motor[8:], 4)}')
print(f'[{LABEL}] window rms xyz {np.round(win_rms, 4)}')
print(f'[{LABEL}] PSD pitch: fpk={FPK:.3f} Hz ratio={RATIO:.4g} amp={AMP:.4g} rad/s fs={FS:.2f} nseg={NSEG}')
print(f'[{LABEL}] control_alloc: {CA}')
print(f'[{LABEL}] land: {LD}')
print(f'[{LABEL}] pitch>1 first: {CROSS}; max bin pitch rms {bin_pitch[kmax] if kmax is not None else "n/a"} at {T_ARM + kmax if kmax is not None else "n/a"}')
print(f'[{LABEL}] first bins (t,n,rms_pitch): ' + '; '.join(f'{t:.1f},{n},{r[1]:.3g}' for (t, n, r) in gyro_rows[:3]))
print(f'[{LABEL}] notes: {notes}')
