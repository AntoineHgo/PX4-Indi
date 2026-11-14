#!/usr/bin/env python3
"""Identify the simulated motor dynamics (gz-sim MulticopterMotorModel) from ULog files.

Plant: first-order lag on rotor speed with timeConstantUp / timeConstantDown (SDF values
0.0125 / 0.025 s for x500), fed by a rotor-speed reference.

Reference mapping (read from the code, not fitted). PX4 MixingOutput scales the normalised
motor command c = actuator_motors.control[i] in [0, 1] linearly to the SIM_GZ_EC_MIN/MAX
range of the output function (x500: MIN = 150, MAX = 1000, FUNCn = 100 + n), and
GZMixingInterfaceESC publishes that value unchanged as the gz Actuators velocity [rad/s]:
    omega_ref = SIM_GZ_EC_MIN + c * (SIM_GZ_EC_MAX - SIM_GZ_EC_MIN)      [rad/s]
    rpm_ref   = omega_ref * 60 / (2 pi)
MIN/MAX are read from the log's initial parameters (fallback 150/1000). Check: hover
c = 0.728 -> 769 rad/s = 7344 rpm, matching the logged median esc_rpm (7342-7357). The
rotorVelocitySlowdownSim = 10 factor is already included in esc_status.esc_rpm
(= rotor joint speed * 10 * 60 / 2 pi), so no further scaling is needed.

Measurement: esc_status.esc[i].esc_rpm. esc_status is logged at an irregular 1-12 ms spacing
and most samples are stale (the same value as the previous one: gz feedback / eRPM telemetry
arrives slower than the log rate, or a frame was dropped), so the fit never uses a fixed-dt
recursion on the log samples. Instead each block is simulated on a 1 ms grid:
    x[j+1] = x[j] + (1 - exp(-h / tau)) * (u(t_j - d) - x[j]),  h = 1 ms,
    tau = tau_up if u(t_j - d) > x[j] else tau_down,
with u(t) the held (previous-sample) actuator_motors reference (gz applies the last command),
d a pure delay searched on a 1 ms grid (-4..16 ms; negative = esc sample stamped before the
command it reflects), x re-initialised from a fresh (non-stale) esc sample at the start of each
block (default 0.1 s), and the residual taken only at fresh samples. (tau_up, tau_down) come
from a log-spaced 2-D grid plus two local refinements, per delay. Only airborne samples
(vehicle_land_detected.landed false) with the reference above --min-ref (default 30 % of
the 1000 rad/s model maximum) over the whole block are used; --excite keeps only blocks
where |ref - rpm| exceeds a threshold somewhere. The "SDF" residual uses tau 12.5/25 ms
with the delay re-optimised on the same grid. Pure numpy + pyulog (scipy is not needed).
"""
import argparse
import os
import sys

import numpy as np
from pyulog import ULog

RPM = 60.0 / (2.0 * np.pi)
SDF_UP, SDF_DOWN = 0.0125, 0.025
H = 1e-3
DELAYS = np.arange(-4, 16.1, 1.0) * 1e-3


def get(ulog, name):
    return [d for d in ulog.data_list if d.name == name and d.multi_id == 0][0].data


def load_blocks(path, block_s, min_ref, excite=0.0):
    """Per motor: block data on the 1 ms grid. x0 (nb,), xm (nb, ns+1) with NaN where no fresh sample, tf (nb, ns)."""
    ul = ULog(path)
    am, es, ld = get(ul, 'actuator_motors'), get(ul, 'esc_status'), get(ul, 'vehicle_land_detected')
    p = ul.initial_parameters
    t = es['timestamp'] * 1e-6
    airborne = np.interp(t, ld['timestamp'] * 1e-6, 1.0 - ld['landed'].astype(float), left=0, right=0) > 0.999
    ns = int(round(block_s / H))
    tref = am['timestamp'] * 1e-6
    out = {}
    for m in range(4):
        pmin, pmax = p.get('SIM_GZ_EC_MIN%d' % (m + 1), 150), p.get('SIM_GZ_EC_MAX%d' % (m + 1), 1000)
        c = np.clip(np.nan_to_num(am['control[%d]' % m], nan=0.0), 0, 1)
        ref = (pmin + c * (pmax - pmin)) * RPM  # rpm
        x = es['esc[%d].esc_rpm' % m].astype(float)
        fresh = np.r_[True, x[1:] != x[:-1]]
        ok = airborne & (np.interp(t, tref, ref) > min_ref * 1000 * RPM)
        x0, xm, t0s = [], [], []
        k = 0
        while k < len(t):
            if not (fresh[k] and ok[k]):
                k += 1
                continue
            e = np.searchsorted(t, t[k] + block_s, side='right')
            if e >= len(t):
                break
            if ok[k:e].all():
                sel = np.arange(k + 1, e)
                sel = sel[fresh[sel]]
                row = np.full(ns + 1, np.nan)
                row[np.round((t[sel] - t[k]) / H).astype(int)] = x[sel]
                rr = np.interp(t[k:e], tref, ref)
                if np.abs(rr - x[k:e]).max() >= excite and len(sel) > 0:
                    x0.append(x[k]); xm.append(row); t0s.append(t[k])
            k = e
        t0s = np.array(t0s)
        out[m] = dict(x0=np.array(x0), xm=np.array(xm), tf=t0s[:, None] + H * np.arange(ns)[None, :], tref=tref, ref=ref)
    return out


def merge(blks):
    return dict(x0=np.concatenate([b['x0'] for b in blks]), xm=np.vstack([b['xm'] for b in blks]),
                tf=np.vstack([b['tf'] for b in blks]), parts=blks)


def delayed_ref(b, d):
    """Held reference u(t - d) on each block's fine grid; blocks merged from several logs use their own reference."""
    if 'parts' not in b:
        i = np.searchsorted(b['tref'], b['tf'] - d, side='right') - 1
        return b['ref'][np.clip(i, 0, None)]
    return np.vstack([delayed_ref(q, d) for q in b['parts']])


def rms_grid(b, u, tu, td):
    """RMS residual [rpm] for each (tu[i], td[i]); b: block data, u: delayed reference (nb, ns)."""
    au, ad = (1 - np.exp(-H / np.asarray(tu)))[:, None], (1 - np.exp(-H / np.asarray(td)))[:, None]
    xs = np.repeat(b['x0'][None, :], len(au), axis=0)
    sse, cnt = np.zeros(len(au)), 0
    for j in range(u.shape[1]):
        e = u[None, :, j] - xs
        xs = xs + np.where(e > 0, au, ad) * e
        w = ~np.isnan(b['xm'][:, j + 1])
        sse += (np.where(w, xs - np.nan_to_num(b['xm'][:, j + 1]), 0.0) ** 2).sum(axis=1)
        cnt += w.sum()
    return np.sqrt(sse / cnt)


PERTURB = [('tu x0.8', .8, 1), ('tu x1.2', 1.2, 1), ('td x0.8', 1, .8), ('td x1.2', 1, 1.2),
           ('both x0.8', .8, .8), ('both x1.2', 1.2, 1.2), ('swap up/down', None, None)]


def fit(b, delays=DELAYS):
    """Fit (tau_up, tau_down, delay); returns dict with RMS, SDF-tau RMS and the +-20 % / swap cost increases."""
    lg = np.geomspace(3e-3, 0.12, 14)
    TU, TD = [a.ravel() for a in np.meshgrid(lg, lg)]
    best = (np.inf,)
    for d in delays:
        u = delayed_ref(b, d)
        c = rms_grid(b, u, TU, TD)
        i = c.argmin()
        tu, td, step, cb = TU[i], TD[i], lg[1] / lg[0], c[i]
        for _ in range(2):  # local refinement: 9 x 9 grid spanning +-1 step
            f = np.geomspace(1 / step, step, 9)
            A, B = [a.ravel() for a in np.meshgrid(tu * f, td * f)]
            c2 = rms_grid(b, u, A, B)
            j = c2.argmin()
            tu, td, step, cb = A[j], B[j], step ** 0.25, c2[j]
        if cb < best[0]:
            best = (cb, tu, td, d)
    rms, tu, td, d = best
    u = delayed_ref(b, d)
    pert = {}
    for name, fu, fd in PERTURB:
        a_, b_ = (td, tu) if fu is None else (tu * fu, td * fd)
        pert[name] = 100 * (rms_grid(b, u, [a_], [b_])[0] / rms - 1)
    sdf = min((rms_grid(b, delayed_ref(b, dd), [SDF_UP], [SDF_DOWN])[0], dd) for dd in delays)
    return dict(tu=tu, td=td, d=d, rms=rms, sdf_rms=sdf[0], sdf_d=sdf[1], pert=pert)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('logs', nargs='+')
    ap.add_argument('--md', help='append the Markdown output to this file')
    ap.add_argument('--block', type=float, default=0.1, help='block length [s], re-initialised from a fresh esc sample')
    ap.add_argument('--min-ref', type=float, default=0.30, help='min reference as a fraction of 1000 rad/s')
    ap.add_argument('--excite', type=float, default=0.0, help='only blocks where |ref - rpm| exceeds this [rpm] somewhere')
    ap.add_argument('--label', default='')
    a = ap.parse_args()

    rows, res, allb = [], [], []
    for path in a.logs:
        name = os.path.relpath(path).replace('/flight.ulg', '').replace('indi_project/results/', '')
        bl = load_blocks(path, a.block, a.min_ref, a.excite)
        for m in range(4):
            r = fit(merge([bl[m]]))
            res.append(r)
            allb.append(bl[m])
            rows.append('| %s | %d | %d | %.1f | %.1f | %.0f | %.1f | %.1f (d=%.0f) |' % (
                name, m, len(bl[m]['x0']), r['tu'] * 1e3, r['td'] * 1e3, r['d'] * 1e3, r['rms'], r['sdf_rms'], r['sdf_d'] * 1e3))
            print(rows[-1], file=sys.stderr)
    out = ['| log | motor | blocks | tau_up [ms] | tau_down [ms] | delay [ms] | RMS [rpm] | RMS SDF taus [rpm] (best d) |',
           '|---|---|---|---|---|---|---|---|'] + rows
    med = {k: np.median([r[k] for r in res]) for k in ('tu', 'td', 'd', 'rms', 'sdf_rms')}
    out.append('\nMedian over motors/logs: tau_up %.1f ms, tau_down %.1f ms, delay %.1f ms, RMS %.1f rpm, RMS with SDF taus %.1f rpm.'
               % (med['tu'] * 1e3, med['td'] * 1e3, med['d'] * 1e3, med['rms'], med['sdf_rms']))
    dd = [med['d'] + k * 1e-3 for k in (-2, -1, 0, 1, 2)]
    pooled = merge(allb)
    r = fit(pooled, dd)  # pooled over every motor and log, delay searched +-2 ms around the median
    out.append('\nPooled over all motors/logs (%d blocks of %.2f s): tau_up %.2f ms, tau_down %.2f ms, delay %.0f ms, RMS %.2f rpm; '
               'SDF taus RMS %.2f rpm (best delay %.0f ms).' % (len(pooled['x0']), a.block, r['tu'] * 1e3, r['td'] * 1e3,
                                                                  r['d'] * 1e3, r['rms'], r['sdf_rms'], r['sdf_d'] * 1e3))
    out.append('\nCost increase of the pooled fit when the taus are perturbed (delay kept): ' +
               ', '.join('%s %+.0f%%' % kv for kv in r['pert'].items()) + '.')
    sens = np.median([list(q['pert'].values()) for q in res], axis=0)
    out.append('Median of the per-motor fits: ' + ', '.join('%s %+.0f%%' % (k, v) for k, v in zip(r['pert'], sens)) + '.')
    text = '\n'.join(out)
    print(text)
    if a.md:
        with open(a.md, 'a') as f:
            f.write('\n### %s\n\n%s\n' % (a.label or 'identification run', text))


if __name__ == '__main__':
    main()
