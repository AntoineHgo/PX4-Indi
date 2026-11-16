#!/usr/bin/env python3
"""A-22: per-link small-signal gains of the roll chain in the M3a log (S43).
Usage: a22_chain.py LOG.ulg [t0=52] [t1=82]
IV estimator: H = S_dy/S_dx with d = indi_rate_status.inject[0] (the injected multisine) as instrument, plus plain S_xy/S_xx."""
import sys
import numpy as np
from pyulog import ULog

path = sys.argv[1]
t0 = float(sys.argv[2]) if len(sys.argv) > 2 else 52.0
t1 = float(sys.argv[3]) if len(sys.argv) > 3 else 82.0
ul = ULog(path)
WMAX = 2700.0
FS = 800.0


def ds(name):
    return ul.get_dataset(name).data


def ts(d):
    s = d.get('timestamp_sample')
    if s is not None and s.max() > 0 and (s > 0).all():
        return s * 1e-6
    return d['timestamp'] * 1e-6


ir = ds('indi_rate_status')
t_ir = ts(ir)
t_boot0 = 0.0
tg = np.arange(t0, t1, 1 / FS)


def grid(t, y):
    return np.interp(tg, t, y)


u = grid(t_ir, ir['torque_sp[0]'])
dinj = grid(t_ir, ir['inject[0]'])
alpha_f = grid(t_ir, ir['angular_accel_filtered[0]'])
am = ds('actuator_motors')
tam = ts(am)
print('actuator_motors ts_sample==ts? median diff (us):', np.median(am['timestamp'] - am['timestamp_sample']) if 'timestamp_sample' in am else 'n/a')
mot = [grid(tam, am['control[%d]' % i]) for i in range(4)]
es = ds('esc_status')
tes = es['timestamp'] * 1e-6
rpm = [grid(tes, es['esc[%d].esc_rpm' % i].astype(float)) for i in range(4)]
w = [r * 2 * np.pi / 60 for r in rpm]
x = [(wi / WMAX) ** 2 for wi in w]
va = ds('vehicle_angular_velocity')
va_t = ts(va)
alpha_gyro = grid(va_t, va['xyz_derivative[0]'])
vg = ds('vehicle_angular_velocity_groundtruth')
p_gt = grid(ts(vg), vg['xyz[0]'])
vgp = ds('vehicle_angular_velocity')
p_gyro = grid(va_t, va['xyz[0]'])
tq = ds('vehicle_torque_setpoint')
u_pub = grid(ts(tq), tq['xyz[0]'])
print('mean motors', [round(float(m.mean()), 4) for m in mot], 'mean w', [round(float(a.mean()), 1) for a in w])
print('max |u-u_pub|', float(np.abs(u - u_pub).max()), 'rms inject', float(dinj.std()), 'rms u', float(u.std()))

SEG = int(10 * FS)
win = np.hanning(SEG)
freqs = np.fft.rfftfreq(SEG, 1 / FS)


def segs(s):
    out = []
    for k in range(0, len(s) - SEG + 1, SEG // 2):
        z = s[k:k + SEG]
        out.append(np.fft.rfft((z - z.mean()) * win))
    return np.array(out)


def spec(a, b):
    A, B = segs(a), segs(b)
    return (np.conj(A) * B).mean(0)


def Hiv(inp, out, instr=dinj):
    return spec(instr, out) / spec(instr, inp)


def Hls(inp, out):
    return spec(inp, out) / spec(inp, inp)


sdd = spec(dinj, dinj).real
band = (freqs >= 2) & (freqs <= 10)
lines = np.where(band & (sdd > 0.01 * sdd[band].max()))[0]
print('injection lines 2-10 Hz (Hz):', np.round(freqs[lines], 2).tolist())
targets = []
for f0 in (3.0, 5.0, 8.0):
    cand = lines[np.abs(freqs[lines] - f0) < 0.8]
    targets.append(int(cand[np.argmax(sdd[cand])]) if len(cand) else int(np.argmin(np.abs(freqs - f0))))


def fmt(h):
    return '%.4g @ %+.1f deg' % (abs(h), np.degrees(np.angle(h)))


def report(name, inp, out):
    hi, hl = Hiv(inp, out), Hls(inp, out)
    pooled = lambda H: (spec(dinj, out)[lines].sum() / spec(dinj, inp)[lines].sum())
    print('%-34s' % name, ' | '.join('%.1fHz IV %s' % (freqs[k], fmt(hi[k])) for k in targets),
          '| pooled IV %s | LS %s' % (fmt(pooled(0)), fmt(sum(spec(inp, out)[lines]) / sum(spec(inp, inp)[lines].real))))
    return hi


sgn = np.array([-1, 1, 1, -1.0])  # roll sign = -sign(py): rotor0 py+, rotor1 py-, rotor2 py-, rotor3 py+
print('--- (a) u -> motor_i (per-motor column)')
cols = [report('u -> motor[%d]' % i, u, mot[i]) for i in range(4)]
rdiff_m = sum(sgn[i] * mot[i] for i in range(4))
ra = report('u -> sum s_i motor_i (roll diff)', u, rdiff_m)
print('--- (b) motor_i -> x_i=(w/wmax)^2')
for i in range(4):
    report('motor[%d] -> x[%d]' % (i, i), mot[i], x[i])
rdiff_x = sum(sgn[i] * x[i] for i in range(4))
report('rdiff_m -> rdiff_x', rdiff_m, rdiff_x)
print('--- (c) rdiff_x -> alpha  (units rad/s^2 per unit sum s_i x_i; analytic static 621)')
report('rdiff_x -> alpha_filtered', rdiff_x, alpha_f)
report('rdiff_x -> alpha_gyro_deriv(vav)', rdiff_x, alpha_gyro)
Wt = np.fft.rfft  # alpha_true = j 2 pi f * p_gt, applied per segment
# spectral derivative via segs
def diff_spec(p):
    return segs(p) * (1j * 2 * np.pi * freqs)[None, :]
def specd(a, Bs):
    A = segs(a)
    return (np.conj(A) * Bs).mean(0)
for lab, p in (('gt', p_gt), ('gyro', p_gyro)):
    Bs = diff_spec(p)
    h = specd(dinj, Bs) / spec(dinj, rdiff_x)
    print('%-34s' % ('rdiff_x -> d/dt p_' + lab), ' | '.join('%.1fHz IV %s' % (freqs[k], fmt(h[k])) for k in targets))
print('--- end-to-end u -> alpha')
report('u -> alpha_filtered', u, alpha_f)
report('u -> alpha_gyro_deriv', u, alpha_gyro)
for lab, p in (('gt', p_gt), ('gyro', p_gyro)):
    Bs = diff_spec(p)
    h = specd(dinj, Bs) / spec(dinj, u)
    print('%-34s' % ('u -> d/dt p_' + lab), ' | '.join('%.1fHz IV %s' % (freqs[k], fmt(h[k])) for k in targets))
print('--- alpha_f vs d/dt p_gt  (filter gain)')
Bs = diff_spec(p_gt)
h = specd(dinj, segs(alpha_f)) / specd(dinj, Bs)
print(' | '.join('%.1fHz %s' % (freqs[k], fmt(h[k])) for k in targets))
