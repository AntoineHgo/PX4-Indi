#!/usr/bin/env python3
"""T3 ulog check of the reference airframe. Usage: t3_analyze.py <run_dir> (reads flight.ulg, phases.json)."""
import json, sys
import numpy as np
from pyulog import ULog

d = sys.argv[1]
u = ULog(f"{d}/flight.ulg")
ph = json.load(open(f"{d}/phases.json"))
D = {x.name + str(x.multi_id): x.data for x in u.data_list}
t0 = u.start_timestamp  # us


def T(n, k="timestamp"):
    return (D[n][k] - t0) * 1e-6 if False else (D[n]["timestamp"] - 0) * 1e-6


def sel(n, t, a, b):
    m = (t >= a) & (t < b)
    return m


# MAVLink time_boot_ms == PX4 sim time; ulog timestamp is the same clock (us since boot)
res = {}
hv0, hv1 = ph["t_at_alt"] + 5, ph["t_hover_end"]
print("hover window", hv0, hv1)
tm = T("actuator_motors0")
m = sel("", tm, hv0, hv1)
mot = np.vstack([D["actuator_motors0"][f"control[{i}]"] for i in range(4)]).T[m]
print("actuator_motors mean per motor (hover)", mot.mean(0), "mean all", mot.mean())
if "vehicle_thrust_setpoint0" in D:
    tt = T("vehicle_thrust_setpoint0"); mm = sel("", tt, hv0, hv1)
    thr = -D["vehicle_thrust_setpoint0"]["xyz[2]"][mm]
    print("thrust setpoint z (hover) mean", thr.mean(), "std", thr.std())
    res["thrust_sp_hover"] = float(thr.mean())
th = D["hover_thrust_estimate0"]; tth = T("hover_thrust_estimate0")
mm = sel("", tth, hv0, hv1)
print("hover_thrust_estimate mean", th["hover_thrust"][mm].mean(), "end", th["hover_thrust"][-1], "valid", th["valid"][mm].mean())
res["hover_thrust_est"] = float(th["hover_thrust"][mm].mean())
for name in ("esc_status0",):
    if name in D:
        te = T(name); mm = sel("", te, hv0, hv1)
        e = D[name]
        rpm = np.vstack([e[f"esc[{i}].esc_rpm"] for i in range(4)]).T[mm]
        print("esc_rpm (eRPM or rpm field) hover mean", rpm.mean(0), "-> rad/s if rpm field is mech:", rpm.mean(0) * 2 * np.pi / 60)
        res["esc_rpm_hover"] = rpm.mean(0).tolist()
# rates
tr = T("vehicle_angular_velocity0"); w = D["vehicle_angular_velocity0"]
mm = sel("", tr, hv0, hv1)
for ax in range(3):
    x = w[f"xyz[{ax}]"][mm]
    print(f"hover body rate axis {ax}: mean {x.mean():+.4f} rms(about mean) {x.std():.4f} rad/s, max|.| {abs(x).max():.3f}")
    res[f"rate_rms_hover_{ax}"] = float(x.std())
# tracking across the whole flight: rate error
ts = T("vehicle_rates_setpoint0"); rs = D["vehicle_rates_setpoint0"]
a, b = ph["t_step_alt"] - 3, ph["t_land_cmd"]
for ax, k in enumerate(("roll", "pitch", "yaw")):
    ws = np.interp(ts, tr, w[f"xyz[{ax}]"])
    mk = (ts >= a) & (ts < b)
    err = rs[k][mk] - ws[mk]
    print(f"rate tracking {k} (steps window): rms err {np.sqrt((err**2).mean()):.3f} rad/s, rate sp rms {np.sqrt((rs[k][mk]**2).mean()):.3f}, max|sp| {abs(rs[k][mk]).max():.2f}")
# oscillation: spectrum peak of gyro in hover (>5 Hz)
fs = 1 / np.median(np.diff(tr)); x = w["xyz[0]"][mm]
f = np.fft.rfftfreq(len(x), 1 / fs); P = abs(np.fft.rfft(x - x.mean()))
print("gyro-x fs", fs, "peak freq above 3 Hz", f[3 * len(x) // int(fs) + np.argmax(P[(f > 3)])] if False else f[f > 3][np.argmax(P[f > 3])])
# attitude follows
tq = T("vehicle_attitude_setpoint0"); qs = D["vehicle_attitude_setpoint0"]
ta = T("vehicle_attitude0"); qa = D["vehicle_attitude0"]
def eul(q0, q1, q2, q3):
    return (np.arctan2(2*(q0*q1+q2*q3), 1-2*(q1**2+q2**2)), np.arcsin(np.clip(2*(q0*q2-q3*q1), -1, 1)))
ra, pa = eul(qa["q[0]"], qa["q[1]"], qa["q[2]"], qa["q[3]"])
rsp, psp = eul(qs["q_d[0]"], qs["q_d[1]"], qs["q_d[2]"], qs["q_d[3]"])
mk = (tq >= a) & (tq < b)
for nm, act, sp_ in (("roll", ra, rsp), ("pitch", pa, psp)):
    ai = np.interp(tq[mk], ta, act); e = np.degrees(ai - sp_[mk])
    print(f"attitude {nm}: rms err {np.sqrt((e**2).mean()):.2f} deg, max|sp| {np.degrees(abs(sp_[mk]).max()):.1f} deg")
# position steps
tp = T("vehicle_local_position0"); lp = D["vehicle_local_position0"]
p0 = ph["p0"]
def step(name, t_on, t_off, key, tgt):
    mk = (tp >= t_on) & (tp < t_off); y = lp[key][mk]; tt = tp[mk] - t_on
    d = tgt - y[0]
    prog = (y - y[0]) / d
    t10 = tt[np.argmax(prog > 0.1)]; t90 = tt[np.argmax(prog > 0.9)] if (prog > 0.9).any() else np.nan
    print(f"{name}: step {d:+.2f} m, rise 10-90% {t90 - t10:.2f} s, overshoot {100 * (prog.max() - 1):.1f} %, final err {y[-1] - tgt:+.3f} m, t90 {t90:.2f}")
    res[name] = dict(rise_s=float(t90 - t10), overshoot_pct=float(100 * (prog.max() - 1)), final_err_m=float(y[-1] - tgt))
step("alt_step_+1m", ph["t_step_alt"], ph["t_step_x"], "z", p0[2] - 1.0)
step("x_step_+2m", ph["t_step_x"], ph["t_back"], "x", p0[0] + 2.0)
json.dump(res, open(f"{d}/t3_metrics.json", "w"), indent=1)

# extra: rate loop lag/gain, motor saturation, high-frequency content, yaw
print("--- extra ---")
am = np.vstack([D["actuator_motors0"][f"control[{i}]"] for i in range(4)]).T
fl = (tm > ph["t_arm"] + 2) & (tm < ph["t_land_cmd"])
print("actuator_motors in flight: min", am[fl].min(), "max", am[fl].max())
for ax, k in enumerate(("roll", "pitch", "yaw")):
    mk = (ts >= a) & (ts < b)
    ws = np.interp(ts[mk], tr, w[f"xyz[{ax}]"]); sp_ = rs[k][mk]
    dt_ = np.median(np.diff(ts[mk])); best = None
    for lag in range(0, 40):
        e = np.sqrt(np.mean((sp_[: len(sp_) - lag] - ws[lag:]) ** 2))
        best = (e, lag) if best is None or e < best[0] else best
    print(f"{k}: best-lag {best[1] * dt_ * 1e3:.0f} ms, residual rms {best[0]:.3f} rad/s")
x = w["xyz[0]"][mm]; y = w["xyz[1]"][mm]
f = np.fft.rfftfreq(len(x), 1 / fs)
for nm, s in (("x", x), ("y", y)):
    P = abs(np.fft.rfft(s - s.mean())) ** 2
    print(f"gyro-{nm} hover band power fraction 0-3Hz {P[f<3].sum()/P.sum():.2f}, 3-20Hz {P[(f>=3)&(f<20)].sum()/P.sum():.2f}, >20Hz {P[f>=20].sum()/P.sum():.2f}")
ty = T("vehicle_attitude0"); q = D["vehicle_attitude0"]
yaw = np.arctan2(2*(q["q[0]"]*q["q[3]"]+q["q[1]"]*q["q[2]"]), 1-2*(q["q[2]"]**2+q["q[3]"]**2))
for t_ in (ph["t_arm"]+1, ph["t_at_alt"], ph["t_hover_end"], ph["t_back"]):
    print(f"yaw at t={t_:.0f}: {np.degrees(np.interp(t_, ty, yaw)):.1f} deg")

mk = (ty >= ph["t_step_yaw"]) & (ty < ph["t_land_cmd"]); yy = np.unwrap(yaw[mk]); tt = ty[mk] - ph["t_step_yaw"]
prog = (yy - yy[0]) / 0.7854
t10 = tt[np.argmax(prog > 0.1)]; t90 = tt[np.argmax(prog > 0.9)]
print(f"yaw step +45 deg: rise 10-90% {t90 - t10:.2f} s, overshoot {100 * (prog.max() - 1):.1f} %, final err {np.degrees(yy[-1] - yy[0] - 0.7854):+.2f} deg")
