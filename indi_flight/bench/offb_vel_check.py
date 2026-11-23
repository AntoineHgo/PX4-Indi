"""S133 T7: velocity-only offboard check. usage: offb_vel_check.py run_dir
S215 (G7): verdict + exit code (0 PASS, 1 FAIL, 2 INVALID), LOC check, "never reached 90 %" reported, final |vx| = mean over the
last 1 s of the hold, empty / absent topics reported INVALID instead of IndexError. GATES.md G5.5 limits unchanged."""
import sys, json, numpy as np
from pyulog import ULog
LIM_RMS, LIM_VEND, LIM_DZ = 0.2, 0.1, 0.3          # GATES.md G5.5 offb_vel_step
LOC_TILT_DEG, LOC_TILT_S, LOC_DROP_M = 60.0, 0.2, 2.0   # GATES.md LOC (same as g3_checks.py TILT_DEG, TILT_S, DROP_M)
END_WIN_S = 1.0                                     # final |vx| = mean |vx| over the last END_WIN_S of the hold


def longest_run_s(t, mask):
    """as g3_checks.longest_run_s (not imported: g3_checks needs scipy)."""
    best, i, n = 0.0, 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j + 1 < n and mask[j + 1]:
                j += 1
            best = max(best, t[j] - t[i]); i = j + 1
        else:
            i += 1
    return best


def tilt_deg(q):
    """as g3_checks.tilt_rad, q (n,4) w,x,y,z."""
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2), -1, 1)))


def invalid(why):
    print("INVALID:", why); print("RESULT INVALID"); sys.exit(2)


r = sys.argv[1]; ev = {e["name"]: e["t_us"] / 1e6 for e in json.load(open(r + "/run.json"))["events"]}
u = ULog(r + "/flight.ulg")
def g(n):
    l = [d for d in u.data_list if d.name == n and len(d.data["timestamp"])]
    if not l: invalid(n + " absent or empty")
    return l[0].data
gt = g("vehicle_local_position_groundtruth"); t = gt["timestamp"] / 1e6
ga = g("vehicle_attitude_groundtruth"); tg = ga["timestamp"] / 1e6
t0, t1, t2 = ev["vstep"], ev["vhold"], ev["vhold"] + 4.0
m = (t >= t0) & (t < t1); h = (t >= t1) & (t < t2); zs = (t >= ev["settle"]) & (t < t2); zp = (t >= t0 - 0.5) & (t < t0)
for nm, mm in (("step window", m), ("hold window", h), ("z hold window", zs), ("pre-step window", zp), ("late-step window", m & (t > t0 + 2))):
    if not mm.any(): invalid(nm + " has no samples")
vx = gt["vx"]; err = vx[m] - 2.0
rms3 = np.sqrt(np.mean(err[t[m] > t0 + 2] ** 2))
print("step window %.2f..%.2f" % (t0, t1))
print("vx RMS err over 5 s (incl. rise) %.3f m/s; last 3 s RMS %.3f; mean last 3 s %.3f" % (np.sqrt(np.mean(err ** 2)), rms3, vx[m][t[m] > t0 + 2].mean()))
hi = vx[m] > 1.8
if hi.any(): print("time to 90%% of 2 m/s: %.2f s" % (t[m][np.argmax(hi)] - t0))
else: print("time to 90%% of 2 m/s: never reached (vx max %.2f)" % vx[m].max())
he = h & (t >= t2 - END_WIN_S)
vend = abs(vx[he]).mean() if he.any() else float("nan")
print("hold: vx RMS %.3f, final |vx| %.3f" % (np.sqrt(np.mean(vx[h] ** 2)), vend))
zz = -gt["z"][zs]; zref = -gt["z"][zp].mean(); dzmax = np.abs(zz - zref).max()
print("z hold: ref %.3f, max |dz| %.3f, RMS dz %.3f; vy RMS %.3f" % (zref, dzmax, np.sqrt(np.mean((zz - zref) ** 2)), np.sqrt(np.mean(gt["vy"][m] ** 2))))
print("x travelled during step %.2f m, at end of hold %.2f" % (gt["x"][m][-1] - gt["x"][m][0], gt["x"][h][-1] - gt["x"][m][0]))
# LOC (truth, GATES.md LOC): tilt > 60 deg for > 0.2 s, or height below the pre-step height by > 2 m, or NaN, over step .. end of hold
q = np.column_stack([ga["q[%d]" % i] for i in range(4)]); w = (tg >= t0) & (tg < t2)
tl = longest_run_s(tg[w], tilt_deg(q)[w] > LOC_TILT_DEG) if w.any() else 0.0
drop = float(max(0.0, zref - (-gt["z"][(t >= t0) & (t < t2)]).min()))
nan = bool(np.isnan(vx[m | h]).any() or np.isnan(q[w]).any())
loc = tl > LOC_TILT_S or drop > LOC_DROP_M or nan
print("LOC: tilt>60 longest %.2f s, height drop %.2f m, nan %s -> %s" % (tl, drop, nan, "LOC" if loc else "no LOC"))
ok = {"rms": rms3 <= LIM_RMS, "end": vend <= LIM_VEND, "dz": dzmax <= LIM_DZ, "no_loc": not loc}   # NaN compares False
for k, x in ok.items(): print("%s %s" % ("PASS" if x else "FAIL", k))
res = all(ok.values()); print("RESULT", "PASS" if res else "FAIL"); sys.exit(0 if res else 1)
