"""S180 reconcile key1 (88.5 Hz) vs key2 (33.5 Hz) on cruise_typ_s1, same window. Docker, repo root:
 indi_project/docker/run.sh -n s180rec -t 900 -- python3 indi_flight/results/g55_gain_probe_s179/reconcile_s180.py"""
import sys, numpy as np
sys.path.insert(0, "indi_flight/bench"); sys.path.insert(0, "indi_flight/results/g4_gate_s169")
import g3_checks as k1, g3_checks_key2 as k2
import chatter_s175 as c
from scipy.signal import periodogram
D = "indi_flight/results/f2_probe_s180/cruise_typ_s1"
tt, pos, q, w, tm, cmd, ref, src, t_land, navc = k1.load(f"{D}/flight.ulg", 0, 1)
cm = cmd[:, :4]
print("motor samples", len(tm), "median dt %.5f s" % np.median(np.diff(tm)), "t range %.2f-%.2f" % (tm[0], tm[-1]))
T0, T1 = 36.0, 53.5
m = (tm >= T0) & (tm <= T1)
_, cg1, fs1 = k1.uniform(tm[m], cm[m], T0, T1)
tg2, g2 = k2.grid(tm[m], cm[m])
print("key1 grid fs", fs1, "samples", cg1.shape[1], "| key2 grid fs", k2.FS, "samples", g2.shape[0], "| bin width 1/4s = 0.25 Hz both")
def win1(x, fs, t0):
    n = int(round(4*fs)); st = int(round(1*fs)); out = []
    for s in range(0, len(x)-n+1, st):
        f, P = periodogram(x[s:s+n], fs, window="hann", detrend="constant", scaling="density"); b = (f >= 20) & (f <= 100)
        k = int(np.argmax(P[b])); kk = np.flatnonzero(b)[k]; df = f[1]-f[0]
        out.append((t0+s/fs, float(f[kk]), float(P[b][k]/np.median(P[b])), float(np.sqrt(P[kk-8:kk+9].sum()*df)), float(np.sqrt(P[kk-2:kk+3].sum()*df)), float(np.sqrt(P[kk]*df))))
    return out
print("\n== per window, window start t0+s, hop 1 s, [peak Hz, ratio, rms+-2Hz, rms+-2bins, rms peak bin only]; * = ratio>20 and rms2Hz>=5e-4")
for i in range(4):
    A = win1(cg1[i], fs1, T0)
    B = k2.psd_windows(g2[:, i], k2.FS, 20, 100, rms_hz=2.0, t_off=tg2[0])
    print(f"-- motor m{i}")
    for a, (t0, f, r, r2, rb, rp) in enumerate(A):
        b = B[a]
        fa = "*" if r > 20 and r2 >= 5e-4 else " "; fb = "*" if b[2] > 20 and b[3] >= 5e-4 else " "
        print(f" {t0:5.1f} key1{fa} {f:6.2f} Hz ratio {r:7.1f} rms2Hz {r2:.2e} rms2bin {rb:.2e} pk {rp:.2e} | key2{fb} {b[1]:6.2f} Hz ratio {b[2]:7.1f} rms2Hz {b[3]:.2e}")
print("\n== key1 line_detector (fixed +-2Hz) on slice, per motor:")
for i in range(4):
    r = k1.line_detector(cg1[i], fs1, k1.CMD_BAND, k1.CMD_LINE_RMS, T0, [], rms_hz=2.0); print(f" m{i}", r["sustained"], r["lines"], "flagged", r["flagged_windows"], "of", r["windows"])
print("== key2 sustained on slice, per motor:")
for i in range(4):
    wi = k2.psd_windows(g2[:, i], k2.FS, 20, 100, rms_hz=2.0, t_off=tg2[0]); print(f" m{i}", k2.sustained(wi, rms_min=5e-4))
print("\n== key2 chatter() whole flight, report line per motor (as score_key2 / rescore_key2):")
for kx, v in k2.chatter(tm, cm).items(): print(kx, {a: (round(b, 6) if isinstance(b, float) else b) for a, b in v.items()})
print("\n== chatter_cruise track() hop 0.5 s, strongest-RMS motor per window, whole flight, windows in 36-53.5:")
for hz in (2.0, None):
    Tk = c.band_track(tm, cm) if hz is None else None
import chatter_cruise_s176 as cc
for hz in (2.0, None):
    Tk = cc.track(tm, cm, hz)
    sel = [x for x in Tk if x[0] >= 35.9 and x[1] <= 53.6]
    print("hz", hz, [(round(x[0], 1), round(x[3], 1), f"{x[4]:.1e}", int(x[2])) for x in sel])
    print(" runs_of:", c.runs_of(Tk))
    fl = [x for x in sel if x[2]]; print(" median of peak Hz over flagged in 36-53.5:", np.median([x[3] for x in fl]) if fl else None, "max rms", max([x[4] for x in fl], default=0))
