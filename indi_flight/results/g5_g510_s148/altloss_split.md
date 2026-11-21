# G5.10 S148: altitude loss split (SAT vs REC), offline ULog analysis

Runs: s1, s2, s3 in this folder (INDI, sat_sustained). Offline only, no simulation.

## Event matching

- SAT and REC are taken from `sends.csv`: `SIM_GZ_THR_SC=0.274` (SAT) and `SIM_GZ_THR_SC=1.0` (REC), column `intended_sim_time_us`.
  s1 SAT 58.218 / REC 63.221; s2 58.487 / 63.490; s3 58.122 / 63.125. These equal the `g510.json` events.
- The ULog `changed_parameters` for SIM_GZ_THR_SC are logged at log start (22.09 s), so they do not give event times. Not used.
- Log time is assumed equal to sim time (same clock). Check: the response starts 0.25 s after each edge in every seed. At SAT, `indi_pos_status.a_c[2]` jumps from about 0 to -4 m/s² (up demand) at SAT+0.25 s. At REC, the motors fall at REC+0.25 s.
- Phases: pre = [SAT-1, SAT); A = SAT (5.0 s); B = [REC, REC+2); C = [REC+2, REC+5].
- Altitude is up (= -z). Reference "pre" = mean altitude over [SAT-1, SAT): s1 5.024 m (LPos), 5.007 m (GT).

## Results (s1, cells = min / max / mean; full seeds in the list below)

| quantity | pre | A (SAT) | B (REC..+2 s) | C (rest) |
|---|---|---|---|---|
| alt LPos (m) | 5.022/5.025/5.024 | 2.285/5.022/3.727 | 4.624/5.972/5.549 | 5.098/5.842/5.363 |
| alt GT (m) | 5.006/5.009/5.007 | 2.293/5.006/3.733 | 4.618/5.946/5.538 | 5.069/5.809/5.332 |
| alt setpoint z (m) | 5.023 const | 5.023 const | 5.023 const | 5.023 const |
| indi a_c[2] NED (m/s²) | -0.004/0.005/-0.001 | -17.243/-0.001/-5.472 | -1.719/7.584/4.489 | 0.033/1.746/0.383 |
| indi a_f[2] NED (m/s²) | -0.014/0.010/-0.003 | -4.206/6.239/0.007 | -14.670/2.252/0.177 | -0.197/0.289/-0.105 |
| collective -thrust_body[2] (att sp) | 0.136/0.137/0.137 | 0.137/0.713/0.496 | 0.105/0.492/0.146 | 0.134/0.139/0.138 |
| actuator_motors control[0] max | 0.137 | 0.711 | 0.492 | 0.140 |
| control[1] max | 0.137 | 0.714 | 0.492 | 0.140 |
| control[2] max | 0.137 | 0.714 | 0.492 | 0.140 |
| control[3] max | 0.137 | 0.712 | 0.492 | 0.140 |
| fraction of time any motor >= 0.99 | 0 | 0 | 0 | 0 |
| tilt att sp (deg) | 0.04/0.20/0.10 | 0.07/27.47/4.61 | 0.27/0.81/0.53 | 0.00/0.32/0.12 |
| tilt actual, vehicle_attitude (deg) | 0.02/0.17/0.08 | 0.04/24.20/4.60 | 0.34/0.80/0.56 | 0.02/0.34/0.13 |
| collective * cos(tilt sp) | 0.136/0.137/0.137 | 0.137/0.710/0.494 | 0.105/0.492/0.146 | 0.134/0.139/0.138 |

Altitude minimum and loss per phase (depth = pre reference minus phase minimum):

| seed | LPos min (m) | time of min | loss A (m) | min in B (m) | min in C (m) | REC alt (m) |
|---|---|---|---|---|---|---|
| s1 | 2.285 | SAT+1.70 s (REC-3.30 s) | 2.74 | 4.624 | 5.098 | 4.625 |
| s2 | 2.236 | SAT+1.69 s (REC-3.31 s) | 2.73 | 4.534 | 5.022 | 4.534 |
| s3 | 2.328 | SAT+1.71 s (REC-3.30 s) | 2.68 | 4.603 | 5.086 | 4.603 |

Note: the GT minimum is within 0.01 m of the LPos minimum in every seed (GT loss 2.67-2.74 m).
The B minimum equals the altitude at REC in all three seeds: no new drop after REC.

Timeline (s1, 0.25 s steps, t relative to SAT; altitude up in m; a_c/a_f NED; collective; tilts in deg):

```
t(SAT)  altLPos altGT  a_c_z   a_f_z   coll   tilt_sp tilt_act motmax
 0.00   5.022  5.006  -0.000  -0.007  0.137   0.20    0.17    0.137
+0.25   4.948  4.923  -3.978   6.080  0.219  19.27    8.29    0.223
+0.50   4.530  4.517 -10.712   4.050  0.345  14.03   24.15    0.350
+0.75   3.903  3.878 -15.402   0.791  0.506   9.12   15.58    0.508
+1.00   3.238  3.210 -17.196  -1.851  0.620   5.82    4.52    0.625
+1.25   2.694  2.672 -16.499  -3.522  0.694   4.88    3.15    0.695
+1.50   2.368  2.360 -13.821  -4.200  0.712   4.53    5.10    0.713
+1.75   2.289  2.299 -10.249  -3.293  0.648   3.40    4.91    0.649   <- min alt
+2.00   2.413  2.434  -7.186  -2.148  0.591   1.87    2.89    0.592
+3.00   3.654  3.677  -0.671   0.646  0.464   3.11    2.68    0.465
+4.00   4.465  4.475  -0.614   0.708  0.465   2.32    2.67    0.465
+5.00   4.625  4.620  -1.665   0.181  0.491   0.70    0.80    0.491   <- REC
+5.25   4.751  4.762   4.110  -4.215  0.199   0.61    0.67    0.200
+5.50   5.175  5.173   7.395   0.490  0.121   0.55    0.56    0.121
+6.50   5.971  5.943   3.555   1.140  0.123   0.35    0.45    0.123   <- max alt
+8.00   5.449  5.416   0.385  -0.189  0.139   0.05    0.09    0.139
+10.00  5.098  5.070   0.034  -0.058  0.137   0.05    0.05    0.137
```

s2 and s3 key rows agree (s2: +0.25 s altLPos 4.879, +1.75 s 2.241, +5.00 s 4.534, max +6.5 s 5.887;
s3: +0.25 s 4.929, +1.75 s 2.330, +5.00 s 4.603, max +6.5 s 5.935).

Tilt in the SAT window peaks at 19-24 deg at SAT+0.25-0.5 s, then falls to 3-5 deg by the altitude minimum.
The README's 45.3 deg tilt max is outside this window (it occurs later in the run).

## Answer

1. The altitude loss happens during SAT. Minimum altitude is 2.24-2.33 m (LPos) at SAT+1.7 s, i.e. REC-3.3 s. Loss versus pre is 2.68-2.74 m, all in phase A.
2. Phase A: about 2.7 m lost (all of it). Phase B: no new loss, since its minimum equals the REC altitude (4.53-4.62 m), then rises to 5.89-5.97 m (overshoot of about +0.9 m above pre). Phase C: stays above pre.
3. Thrust is not saturated at the motor level: control max is 0.71-0.714 and any motor >= 0.99 for 0% of time in every phase. The injected cap (SIM_GZ_THR_SC=0.274) is invisible to the mixer. In the first 1.7 s, a_c_z demands -17 m/s² while a_f_z is still falling (+6 m/s² at SAT+0.25 s). The collective rises from 0.14 to 0.71 over about 1.5 s. This is a thrust-build-up deficit at onset, not tilt: vertical loss from tilt is about 5-9% of thrust for about 0.5 s (cos 19-24 deg), and tilt is about 3-5 deg at the minimum. So: deficit-driven, with a small tilt contribution.
4. After REC there is no slow z-loop drop: the altitude minimum after REC equals the REC altitude. The later rise to about +0.9 m above pre is an overshoot from the restored thrust (a_c_z +7 m/s² down demand at REC+0.5 s), a separate effect.
5. Metres: A = -2.7 m (the whole loss); B = 0 m new loss (0.4 m below pre only as the tail of A); C = 0 (no loss). Unverified: whether the motor lag or the plant cap sets the 1.7 s build-up time needs a plant model.

## Flags

- The vehicle_local_position_setpoint z is constant at 5.02 m in the whole window (no step). The README's "3 m step" does not appear here.
- Results are from log time (assumed = sim time, checked by the 0.25 s response lag), not from a separate sim-time log.
- Motor max is 0.71, not 1.0: "saturation" in this scenario is a plant cap, so the metric "any motor >= 0.99" does not detect it.

## Scripts (run from the results folder: `python3 altloss_split.py s1`; uses ULog from pyulog at ~/.local)

`altloss_split.py` (per-phase statistics, all seeds):

```python
import sys, csv
import numpy as np
from pyulog import ULog

seed = sys.argv[1]
base = '/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g5_g510_s148/' + seed
sat = rec = None
with open(base + '/sends.csv') as f:
    for r in csv.DictReader(f):
        t = float(r['intended_sim_time_us']) / 1e6
        if 'THR_SC=0.274' in r['payload'] and sat is None:
            sat = t
        elif 'THR_SC=1.0' in r['payload'] and sat is not None and rec is None and t > sat:
            rec = t
u = ULog(base + '/flight.ulg')

def T(name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return {k: np.asarray(v, dtype=float) for k, v in d.data.items()}
    raise SystemExit('missing ' + name)

PH = {'pre': (sat - 1, sat), 'A': (sat, rec), 'B': (rec, rec + 2), 'C': (rec + 2, rec + 5.0001)}

def st(t, v):
    out = []
    for p, (lo, hi) in PH.items():
        m = (t >= lo) & (t < hi)
        out.append(f"{p} {v[m].min():.3f}/{v[m].max():.3f}/{v[m].mean():.3f}" if m.sum() else f"{p} n/a")
    return " | ".join(out)

def tilt(q):
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[1]**2 + q[2]**2), -1, 1)))

print(f"{seed} SAT={sat:.3f} REC={rec:.3f} (sends.csv intended_sim_time; phases pre/A/B/C; cells min/max/mean)")

lp = T('vehicle_local_position'); tl = lp['timestamp'] / 1e6; alt = -lp['z']
gt = T('vehicle_local_position_groundtruth'); tg = gt['timestamp'] / 1e6; altg = -gt['z']
sp = T('vehicle_local_position_setpoint'); ts = sp['timestamp'] / 1e6
ref = alt[(tl >= sat - 1) & (tl < sat)].mean()
refg = altg[(tg >= sat - 1) & (tg < sat)].mean()
print(f"ALT ref(pre mean up, LPos) {ref:.3f}  ref(GT) {refg:.3f}")
print("ALT up LPos   " + st(tl, alt))
print("ALT up GT     " + st(tg, altg))
print("ALT up SP z   " + st(ts, -sp['z']))
for nm, tt, aa, r0 in (("LPos", tl, alt, ref), ("GT", tg, altg, refg)):
    m = (tt >= sat - 1) & (tt <= rec + 5)
    i = np.argmin(np.where(m, aa, np.inf))
    loss = " | ".join(f"{p} {r0 - aa[(tt >= lo) & (tt < hi)].min():.3f}" for p, (lo, hi) in PH.items() if p != 'pre')
    print(f"LOSS {nm} min {aa[i]:.3f} at t={tt[i]:.2f} ({tt[i]-sat:+.2f} s from SAT, {tt[i]-rec:+.2f} s from REC); depth m by phase: {loss}")

ip = T('indi_pos_status'); ti = ip['timestamp'] / 1e6
print("ACC indi a_c[2] " + st(ti, ip['a_c[2]']))
print("ACC indi a_f[2] " + st(ti, ip['a_f[2]']))
print("ACC indi thrust " + st(ti, ip['thrust']))
print("ACC indi blend  " + st(ti, ip['blend']))
print("ACC LPos az(NED) " + st(tl, lp['az']))
print("ACC SP acc z    " + st(ts, sp['acceleration[2]']))
print("ACC SP thrust z " + st(ts, sp['thrust[2]']))

vas = T('vehicle_attitude_setpoint'); tas = vas['timestamp'] / 1e6
tsp = tilt([vas[f'q_d[{i}]'] for i in range(4)])
coll = -vas['thrust_body[2]']
print("ATT sp collective -thrust_body[2] " + st(tas, coll))
print("ATT sp tilt deg " + st(tas, tsp))
print("ATT sp vertical coll*cos(tilt) " + st(tas, coll * np.cos(np.radians(tsp))))
va = T('vehicle_attitude'); tv = va['timestamp'] / 1e6
print("ATT actual tilt deg " + st(tv, tilt([va[f'q[{i}]'] for i in range(4)])))

am = T('actuator_motors'); tm = am['timestamp'] / 1e6
M = np.stack([am[f'control[{i}]'] for i in range(4)], axis=1)
anyhi = (M >= 0.99).any(axis=1).astype(float)
for i in range(4):
    print(f"MOT control[{i}] " + st(tm, M[:, i]))
print("MOT any>=0.99 (min/max/mean = fraction of time) " + st(tm, anyhi))
w = (tm >= sat - 1) & (tm <= rec + 5) & (anyhi > 0)
if w.any():
    print(f"MOT first/last any>=0.99 in window: {tm[w][0]-sat:+.3f} / {tm[w][-1]-rec:+.3f} s rel SAT / REC")
```

`timeline.py` (0.25 s timeline, `python3 timeline.py s1`):

```python
import sys, csv
import numpy as np
from pyulog import ULog
seed = sys.argv[1]
base = '/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g5_g510_s148/' + seed
sat = rec = None
with open(base + '/sends.csv') as f:
    for r in csv.DictReader(f):
        t = float(r['intended_sim_time_us']) / 1e6
        if 'THR_SC=0.274' in r['payload'] and sat is None: sat = t
        elif 'THR_SC=1.0' in r['payload'] and sat is not None and rec is None and t > sat: rec = t
u = ULog(base + '/flight.ulg')
def T(name):
    for d in u.data_list:
        if d.name == name and d.multi_id == 0:
            return {k: np.asarray(v, dtype=float) for k, v in d.data.items()}
def tilt(q):
    return np.degrees(np.arccos(np.clip(1 - 2 * (q[1]**2 + q[2]**2), -1, 1)))
lp = T('vehicle_local_position'); gt = T('vehicle_local_position_groundtruth')
ip = T('indi_pos_status'); vas = T('vehicle_attitude_setpoint'); va = T('vehicle_attitude')
am = T('actuator_motors'); sp = T('vehicle_local_position_setpoint')
tl = lp['timestamp']/1e6; tg = gt['timestamp']/1e6; ti = ip['timestamp']/1e6
tas = vas['timestamp']/1e6; tv = va['timestamp']/1e6; tm = am['timestamp']/1e6; ts = sp['timestamp']/1e6
tsp = tilt([vas[f'q_d[{i}]'] for i in range(4)]); tact = tilt([va[f'q[{i}]'] for i in range(4)])
mmax = np.max(np.stack([am[f'control[{i}]'] for i in range(4)], axis=1), axis=1)
def at(tt, vv, t0):
    i = max(np.searchsorted(tt, t0, side='right') - 1, 0); return vv[i]
def row(t0):
    return (f"{t0-sat:+6.2f} {-at(tl,lp['z'],t0):7.3f} {-at(tg,gt['z'],t0):7.3f} {-at(ts,sp['z'],t0):7.3f} "
            f"{at(ti,ip['a_c[2]'],t0):8.3f} {at(ti,ip['a_f[2]'],t0):8.3f} {-at(tas,vas['thrust_body[2]'],t0):6.3f} "
            f"{at(tas,tsp,t0):6.2f} {at(tv,tact,t0):6.2f} {at(tm,mmax,t0):6.3f}")
print(f"{seed} timeline; t rel SAT | altLPos altGT altSPz(up m) | a_c_z a_f_z (NED) | collective tilt_sp tilt_act motmax")
grid = np.arange(sat - 1, rec + 5.0001, 0.25)
for t0 in grid:
    print(row(t0))
```
