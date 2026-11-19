"""S133 T7: velocity-only offboard check. usage: offb_vel_check.py run_dir"""
import sys, json, numpy as np
from pyulog import ULog
r = sys.argv[1]; ev = {e["name"]: e["t_us"] / 1e6 for e in json.load(open(r + "/run.json"))["events"]}
u = ULog(r + "/flight.ulg"); g = lambda n: [d for d in u.data_list if d.name == n][0].data
gt = g("vehicle_local_position_groundtruth"); t = gt["timestamp"] / 1e6
t0, t1, t2 = ev["vstep"], ev["vhold"], ev["vhold"] + 4.0
m = (t >= t0) & (t < t1)
vx = gt["vx"]; err = vx[m] - 2.0
print("step window %.2f..%.2f" % (t0, t1))
print("vx RMS err over 5 s (incl. rise) %.3f m/s; last 3 s RMS %.3f; mean last 3 s %.3f" % (np.sqrt(np.mean(err ** 2)), np.sqrt(np.mean(err[t[m] > t0 + 2] ** 2)), vx[m][t[m] > t0 + 2].mean()))
k = np.argmax(vx[m] > 1.8); print("time to 90%% of 2 m/s: %.2f s" % (t[m][k] - t0))
h = (t >= t1) & (t < t2); print("hold: vx RMS %.3f, final |vx| %.3f" % (np.sqrt(np.mean(vx[h] ** 2)), abs(vx[h][-1])))
zs = (t >= ev["settle"]) & (t < t2); zz = -gt["z"][zs]; zref = -gt["z"][(t >= t0 - 0.5) & (t < t0)].mean()
print("z hold: ref %.3f, max |dz| %.3f, RMS dz %.3f; vy RMS %.3f" % (zref, np.abs(zz - zref).max(), np.sqrt(np.mean((zz - zref) ** 2)), np.sqrt(np.mean(gt["vy"][m] ** 2))))
print("x travelled during step %.2f m, at end of hold %.2f" % (gt["x"][m][-1] - gt["x"][m][0], gt["x"][h][-1] - gt["x"][m][0]))
