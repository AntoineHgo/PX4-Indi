#!/usr/bin/env python3
"""S191: trace a body-rate q line (default ~2 Hz) across loops of one G3 flight log. numpy + pyulog only, native sample rates,
no zero-order hold: amplitudes/phases are least-squares sine fits on the native samples of each topic.
Usage: g3_line_trace_s191.py FLIGHT.ulg [f_hz=2.0] [t_a t_b ...]   (times = seconds since ulog start, scorer clock)
Prints (1) 4 s/1 s sliding q line scan (truth q, 1.5-3 Hz peak, rms dps), nav_state changes, (2) for each given window the
amplitude and phase (deg, relative to q; positive = signal leads q) of each signal at the line frequency."""
import sys
import numpy as np

def ls_fit(t, x, f, a, b):
    """Hann-weighted complex amplitude (A*exp(j*phi), x ~ Re(c*exp(j*2pi f t))) of x on native samples in [a,b); None if <8 samples"""
    m = (t >= a) & (t < b) & np.isfinite(x)
    if m.sum() < 8: return None
    tt = t[m]; y = x[m] - x[m].mean()
    M = np.stack([np.cos(2 * np.pi * f * tt), np.sin(2 * np.pi * f * tt)], 1)
    w = np.sqrt(np.sin(np.pi * (tt - a) / (b - a)) ** 2 + 1e-9)   # Hann weight (sqrt for lstsq): suppresses leakage of big slow trajectory motion
    c, *_ = np.linalg.lstsq(M * w[:, None], y * w, rcond=None)
    return complex(c[0], -c[1])

def window_scan(t, x, fmin, fmax, win=4.0, step=1.0, t_lo=None, t_hi=None):
    """x on native (near-uniform) samples; Hann FFT peak in [fmin,fmax] per window -> [(t_start, f_peak, rms_dps_at_peak+-0.25Hz)]"""
    fs = (len(t) - 1) / (t[-1] - t[0]); n = int(round(win * fs)); out = []
    s = t_lo if t_lo is not None else t[0]
    while s + win <= (t_hi if t_hi is not None else t[-1]):
        i0 = int(np.searchsorted(t, s)); seg = x[i0:i0 + n]
        if len(seg) == n and np.isfinite(seg).all():
            seg = seg - seg.mean(); w = np.hanning(n); X = np.fft.rfft(seg * w); f = np.fft.rfftfreq(n, 1 / fs)
            P = np.abs(X) ** 2; k = np.flatnonzero((f >= fmin) & (f <= fmax)); kp = k[np.argmax(P[k])]
            amp = 2 * np.abs(X[kp]) / np.sum(w)   # sine amplitude at the peak bin
            out.append((s, f[kp], amp / np.sqrt(2)))
        s += step
    return out

def main():
    from pyulog import ULog
    log = sys.argv[1]; f0 = float(sys.argv[2]) if len(sys.argv) > 2 else 2.0
    wins = [float(v) for v in sys.argv[3:]]
    u = ULog(log); st = u.start_timestamp; D = {}
    for d in u.data_list:
        if d.multi_id == 0: D[d.name] = d.data
    T = lambda n: (D[n]["timestamp"].astype(np.int64) - st) * 1e-6
    g = D["sim_ground_truth"]; tg = T("sim_ground_truth")
    q_truth = np.degrees(g["angular_velocity[1]"])
    print("logged rates Hz:", {n: round((len(D[n]['timestamp']) - 1) / (T(n)[-1] - T(n)[0]), 1) for n in
          ("sim_ground_truth", "vehicle_angular_velocity", "vehicle_attitude", "vehicle_local_position", "vehicle_local_position_setpoint", "indi_pos_status") if n in D})
    vs = D["vehicle_status"]; tv = T("vehicle_status"); ch = np.flatnonzero(np.diff(vs["nav_state"])) + 1
    print("nav_state changes (t,state):", [(round(float(tv[i]), 1), int(vs["nav_state"][i])) for i in ch])
    print("q truth line scan 1.5-3 Hz (t_start, f, rms dps):")
    print("  " + " ".join(f"{a:.0f}:{f:.2f}/{r:.1f}" for a, f, r in window_scan(tg, q_truth, 1.5, 3.0, t_lo=20.0)))
    # signals; forward/right = NED x,y rotated by mean yaw of the window
    qa = D["vehicle_attitude"]; ta = T("vehicle_attitude")
    w_, x_, y_, z_ = (qa[f"q[{i}]"] for i in range(4))
    pitch = np.degrees(np.arcsin(np.clip(2 * (w_ * y_ - z_ * x_), -1, 1)))
    roll = np.degrees(np.arctan2(2 * (w_ * x_ + y_ * z_), 1 - 2 * (x_ * x_ + y_ * y_)))
    yaw = np.arctan2(2 * (w_ * z_ + x_ * y_), 1 - 2 * (y_ * y_ + z_ * z_))
    qd = D["vehicle_attitude_setpoint"]; tqd = T("vehicle_attitude_setpoint")
    w2, x2, y2, z2 = (qd[f"q_d[{i}]"] for i in range(4))
    pitch_sp = np.degrees(np.arcsin(np.clip(2 * (w2 * y2 - z2 * x2), -1, 1)))
    lp = D["vehicle_local_position"]; tl = T("vehicle_local_position"); sp = D["vehicle_local_position_setpoint"]; tsp = T("vehicle_local_position_setpoint")
    ps = D["indi_pos_status"] if "indi_pos_status" in D else None
    for a in wins[0::2]:
        b = wins[wins.index(a) + 1]
        yw = np.angle(np.mean(np.exp(1j * yaw[(ta >= a) & (ta < b)]))); c, s_ = np.cos(yw), np.sin(yw)
        fwd = lambda X, Y: c * X + s_ * Y; rgt = lambda X, Y: -s_ * X + c * Y
        sig = [("q truth dps", tg, q_truth), ("q logged dps", T("vehicle_angular_velocity"), np.degrees(D["vehicle_angular_velocity"]["xyz[1]"])),
               ("pitch deg", ta, pitch), ("roll deg", ta, roll), ("pitch_sp(q_d) deg", tqd, pitch_sp),
               ("vx_est fwd m/s", tl, fwd(lp["vx"], lp["vy"])), ("vx_sp fwd m/s", tsp, fwd(sp["vx"], sp["vy"])),
               ("a_sp fwd m/s2", tsp, fwd(sp["acceleration[0]"], sp["acceleration[1]"])), ("a_sp right m/s2", tsp, rgt(sp["acceleration[0]"], sp["acceleration[1]"])),
               ("x_est fwd m", tl, fwd(lp["x"], lp["y"])), ("x_sp fwd m", tsp, fwd(sp["x"], sp["y"])),
               ("truth vx fwd m/s", tg, fwd(g["vx"], g["vy"]))]
        if ps is not None:
            tps = T("indi_pos_status")
            sig += [("a_c fwd m/s2", tps, fwd(ps["a_c[0]"], ps["a_c[1]"])), ("a_f fwd m/s2", tps, fwd(ps["a_f[0]"], ps["a_f[1]"])),
                    ("t_c fwd", tps, fwd(ps["t_c[0]"], ps["t_c[1]"]))]
        if "trajectory_setpoint" in D:
            tt_, ts_ = T("trajectory_setpoint"), D["trajectory_setpoint"]
            sig += [("traj_sp x fwd m", tt_, fwd(ts_["position[0]"], ts_["position[1]"])), ("traj_sp v fwd m/s", tt_, fwd(ts_["velocity[0]"], ts_["velocity[1]"]))]
        fs_ = np.arange(1.0, 3.0001, 0.02); amps = [abs(ls_fit(tg, q_truth, f, a, b) or 0) for f in fs_]
        print(f"  best q line freq in window: {fs_[int(np.argmax(amps))]:.2f} Hz (amp {max(amps):.2f} dps); using f0={f0}")
        ref = ls_fit(tg, q_truth, f0, a, b)
        print(f"window [{a},{b}) f={f0} Hz yaw={np.degrees(yw):.0f} deg; phase rel q (+ = leads), amplitude")
        for name, t, x in sig:
            cc = ls_fit(t, np.asarray(x, float), f0, a, b)
            if cc is None or ref is None: print(f"  {name:20s} n/a"); continue
            print(f"  {name:20s} amp {abs(cc):9.4f}  phase {np.degrees(np.angle(cc / ref)):7.1f}")

if __name__ == "__main__":
    main()
