#!/usr/bin/env python3
"""Independent (key 2) attitude-loop margin estimator from raw ULogs.
Break MC_INDI_INJ_PT=1 (indi_rate_status): y=rates_sp_pre_inject (loop signal entering the
break, attitude output), d=rates_sp_inject, x=rates_sp_applied=y+d (leaving, fed to rate law).
Return signal Y, break output X=Y+d  ->  L = -Y/X  (H1 over periods: -sum(Y X*)/sum|X|^2).
Window: samples with d!=0, complete periods, first period discarded.
Consistency (coherence-like) per bin: |sum_p Y_p X_p*|^2 / (sum_p|X_p|^2 * sum_p|Y_p|^2)
(multi-period coherence); bin kept if >= COH_MIN and finite."""
import sys, os, numpy as np
COH_MIN = 0.9
TP = 10.0

def nudft(t, x, f):
    return np.exp(-2j*np.pi*np.outer(f, t)) @ x

def estimate(t, d, y, x, tp=TP, discard=1, coh_min=COH_MIN):
    nz = np.nonzero(d)[0]
    t0 = t[nz[0]]; t1 = t[nz[-1]]
    nper = int(round((t1 - t0) / tp + 1e-9)) if (t1 - t0) > tp * 0.5 else 0
    nper = int(np.floor((t1 - t0) / tp + 0.02))  # complete periods (last sample ~ T - dt)
    nper = max(nper, 1)
    # excited bins from the d spectrum over the last complete period
    fb = np.arange(1, int(40*tp)+1) / tp
    m = (t >= t0) & (t < t0 + tp)
    D = nudft(t[m]-t0, d[m], fb)
    ex = fb[np.abs(D) > 0.05*np.abs(D).max()]
    Sxy = 0; Sxx = 0; Syy = 0; Lp = []
    for p in range(discard, nper):
        m = (t >= t0 + p*tp) & (t < t0 + (p+1)*tp)
        tt = t[m] - (t0 + p*tp)
        X = nudft(tt, x[m], ex); Y = nudft(tt, y[m], ex)
        Sxy = Sxy + Y*np.conj(X); Sxx = Sxx + np.abs(X)**2; Syy = Syy + np.abs(Y)**2
        Lp.append(-Y/X)
    L = -Sxy/Sxx
    coh = np.abs(Sxy)**2/(Sxx*Syy)
    keep = np.isfinite(coh) & (coh >= coh_min)
    return ex, L, coh, keep, nper-discard

def margins(f, L):
    """f ascending, L complex. Returns dict."""
    lf = np.log10(f); mag = 20*np.log10(np.abs(L)); ph = np.degrees(np.unwrap(np.angle(L)))
    # shift phase so that the low-frequency value is in (-360, 0]... keep unwrapped
    while ph[0] > 0: ph -= 360
    while ph[0] <= -360: ph += 360
    out = dict(fc=np.nan, pm=np.nan, gm=np.nan, gm_note='', dm=np.nan)
    s = np.nonzero((mag[:-1] > 0) & (mag[1:] <= 0))[0]
    if len(s):
        i = s[-1]; a = mag[i]/(mag[i]-mag[i+1])  # last downward crossing
        fc = 10**(lf[i] + a*(lf[i+1]-lf[i])); phc = ph[i] + a*(ph[i+1]-ph[i])
        out['fc'] = fc; out['pm'] = 180 + phc
        out['dm'] = np.radians(out['pm'])/(2*np.pi*fc)*1e3
    gms = []
    for k in range(-4, 2):
        tgt = -180 + 360*k
        c = np.nonzero((ph[:-1]-tgt)*(ph[1:]-tgt) < 0)[0]
        for i in c:
            a = (tgt-ph[i])/(ph[i+1]-ph[i])
            gms.append(-(mag[i] + a*(mag[i+1]-mag[i])))
    if gms:
        out['gm'] = min(gms)
    else:
        w = np.abs(((ph + 180 + 180) % 360) - 180) <= 10
        out['gm_note'] = 'none in band'
        if w.any(): out['gm_note'] += ' (min 1/|L| within 10deg of -180: %.1f dB)' % (-mag[w].max())
        else: out['gm_note'] += ' (no bin within 10deg of -180)'
    return out

def selftest():
    fs = 800.; dt = 1/fs; k = 2*np.pi*3.0; m = 16  # tau = 0.02 s
    rng = np.random.default_rng(1)
    bins = np.unique(np.round(np.geomspace(0.2, 20, 60)*10)/10)
    n = len(bins); ph = -np.pi*np.arange(n)*(np.arange(n)+1)/n  # Schroeder
    N = int(6*TP*fs); t = np.arange(N)*dt
    d = sum(0.06*np.cos(2*np.pi*f*t + p) for f, p in zip(bins, ph))
    d[t < TP/10] = 0  # start offset; window starts at first nonzero
    d[d == 0] = 1e-12
    I = 0.; yb = np.zeros(m+1); x = np.zeros(N); y = np.zeros(N)
    for i in range(N):
        y[i] = -yb[0] + 0.003*rng.standard_normal()*0  # return signal
        x[i] = y[i] + d[i]
        I += k*dt*x[i]
        yb = np.roll(yb, -1); yb[-1] = I  # delay m steps: y_i = I_{i-m}
    y = y + 0.002*rng.standard_normal(N)  # measurement noise on logged y
    ex, L, coh, keep, nu = estimate(t, d, y, x)
    est = margins(ex[keep], L[keep])
    fd = np.geomspace(0.2, 20, 4000); z = np.exp(2j*np.pi*fd/fs)
    tru = margins(fd, k*dt*z**(-m)/(z-1) * 1.0)
    # note L_true = -Y/X = z^-m * k dt/(z-1)
    ok = abs(est['pm']-tru['pm']) < 1 and abs(est['gm']-tru['gm']) < 0.5
    return est, tru, ok, nu, int(keep.sum())

def load(path):
    from pyulog import ULog
    u = ULog(path, message_name_filter_list=['indi_rate_status'])
    d = u.get_dataset('indi_rate_status')
    return d.data

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    lines = []
    est, tru, ok, nu, nk = selftest()
    lines.append('SELFTEST k/s*exp(-s*0.02) (3 Hz crossover, discrete 800 Hz, noise): est fc=%.3f PM=%.2f GM=%.2f | true fc=%.3f PM=%.2f GM=%.2f | bins=%d periods=%d -> %s'
                 % (est['fc'], est['pm'], est['gm'], tru['fc'], tru['pm'], tru['gm'], nk, nu, 'PASS' if ok else 'FAIL'))
    lines.append('Break PT1: L=-Y/X, Y=rates_sp_pre_inject, X=rates_sp_applied=Y+d, d=rates_sp_inject; coherence threshold %.2f' % COH_MIN)
    lines.append('%-12s %7s %7s %7s %7s %9s %6s %6s' % ('cell', 'fc_Hz', 'PM_deg', 'GM_dB', 'DM_ms', 'bins', 'cohmed', 'rate'))
    for ax in (1, 2, 3):
        for r in (400, 800):
            for s in (1, 2):
                name = 'ax%d_r%d_s%d' % (ax, r, s)
                try:
                    D = load(os.path.join(here, name, 'flight.ulg'))
                    a = ax-1
                    t = D['timestamp_sample'].astype(float)/1e6
                    d = D['rates_sp_inject[%d]' % a].astype(float)
                    y = D['rates_sp_pre_inject[%d]' % a].astype(float)
                    x = D['rates_sp_applied[%d]' % a].astype(float)
                    ex, L, coh, keep, nu = estimate(t, d, y, x)
                    mg = margins(ex[keep], L[keep])
                    gm = ('%7.2f' % mg['gm']) if np.isfinite(mg['gm']) else mg['gm_note']
                    lines.append('%-12s %7.3f %7.1f %7s %7.1f %4d/%-4d %6.3f %5.0f  periods=%d' % (
                        name, mg['fc'], mg['pm'], gm, mg['dm'], keep.sum(), len(ex), np.median(coh), 1/np.median(np.diff(t)), nu))
                except Exception as e:
                    lines.append('%-12s ERROR %r' % (name, e))
    txt = '\n'.join(lines)
    open(os.path.join(here, 'key2_att_margins.txt'), 'w').write(txt + '\n')
    print(txt)

if __name__ == '__main__':
    main()
