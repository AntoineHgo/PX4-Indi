"""Synthetic self-test for g58_moving_check (known answers). pytest or python3."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g58_moving_check as g  # noqa: E402

S = 1_000_000
T_E = 10 * S   # failsafe entry


def braking_sp(v0=3.0, a=1.5, t_end=20):
    """position setpoint of a constant-deceleration stop starting at T_E from x=30 m; 250 Hz."""
    t = np.arange(0, t_end * S, 4000)
    tau = np.clip((t - T_E) / 1e6, 0, v0 / a)
    x = 30.0 + np.where(t < T_E, 0.0, v0 * tau - 0.5 * a * tau ** 2)
    return t, x


def closed_loop_truth(sp_t, sp_x, lag_s, frame=(0.0, 0.0)):
    """truth follows the setpoint delayed by lag_s (moving at 3 m/s before T_E, so a pure delay), minus the frame offset
    (setpoints are in the estimator frame = truth + offset)."""
    t = np.arange(0, sp_t[-1], 1600)
    x = np.interp(t - lag_s * 1e6, sp_t, sp_x) - frame[0]
    # before T_E the setpoint is a 3 m/s ramp: extrapolate it backwards so the delayed truth is defined
    pre = t - lag_s * 1e6 < sp_t[0]
    x[pre] = 30.0 + 3.0 * (t[pre] - lag_s * 1e6 - T_E) / 1e6 - frame[0]
    y = np.zeros_like(x) - frame[1]
    return t, np.stack([x, y], 1)


def run(lag, frame=(0.0, 0.0), nan_until=None):
    sp_t, sp_x = braking_sp()
    # before T_E the setpoint position is a ramp 30 + 3 (t - T_E); extend it so lag is a pure delay there as well
    sp_x = np.where(sp_t < T_E, 30.0 + 3.0 * (sp_t - T_E) / 1e6, sp_x)
    sp_pos = np.stack([sp_x, np.zeros_like(sp_x)], 1)
    vel = np.zeros_like(sp_pos); vel[:, 0] = np.where(sp_t < T_E, 3.0, 0.0)
    if nan_until is not None:
        sp_pos[sp_t < nan_until] = np.nan
    tt, txy = closed_loop_truth(sp_t, sp_x, lag, frame)
    return tt, txy, sp_t, sp_pos, vel


def test_lag_known_excursion():
    # truth = setpoint delayed 0.2 s; setpoint speed <= 3 m/s -> max deviation = 3 * 0.2 = 0.6 m, at window start
    tt, txy, st, sp, v = run(0.2)
    d = g.deviation(tt, txy, st, sp, v, np.zeros(2), T_E, T_E + 15 * S)
    assert abs(d["max_dev"] - 0.6) < 0.01, d
    assert d["n_nan"] == 0 and d["max_dev_vint"] is None
    assert g.verdict(0.5, d["max_dev"], 4, 4) == "PASS"


def test_lag_fail():
    tt, txy, st, sp, v = run(0.4)       # 3 * 0.4 = 1.2 m
    d = g.deviation(tt, txy, st, sp, v, np.zeros(2), T_E, T_E + 15 * S)
    assert abs(d["max_dev"] - 1.2) < 0.01, d
    assert g.verdict(0.5, d["max_dev"], 4, 4) == "FAIL"
    assert g.verdict(1.2, 0.1, 4, 4) == "FAIL"       # entry too late
    assert g.verdict(None, 0.1, 4, 4) == "NOT-COMPUTED"


def test_frame_offset_removed():
    off = (0.3, -0.2)
    tt, txy, st, sp, v = run(0.2, frame=off)
    d_raw = g.deviation(tt, txy, st, sp, v, np.zeros(2), T_E, T_E + 15 * S)
    assert d_raw["max_dev"] > 0.3                      # unaligned truth is off by the frame offset
    d = g.deviation(tt, txy, st, sp, v, np.array(off), T_E, T_E + 15 * S)
    assert abs(d["max_dev"] - 0.6) < 0.01, d
    # offset estimated from a hover: est - truth with a known constant error, 5 cm noise-free
    et = np.arange(0, 10 * S, 10_000)
    est = np.stack([np.full(len(et), 1.0 + 0.3), np.full(len(et), 2.0 - 0.2)], 1)
    gt, gxy = np.array([0, 10 * S]), np.array([[1.0, 2.0], [1.0, 2.0]])
    o = g.frame_offset(et, est, gt, gxy, 2 * S, 9 * S)
    assert np.allclose(o, [0.3, -0.2])


def test_nan_segment():
    # first 2 s of the window are velocity-only (NaN position): excluded from the verdict number, fraction reported
    tt, txy, st, sp, v = run(0.2, nan_until=T_E + 2 * S)
    d = g.deviation(tt, txy, st, sp, v, np.zeros(2), T_E, T_E + 15 * S)
    n_win = ((st >= T_E) & (st <= T_E + 15 * S)).sum()
    assert d["n_nan"] == ((st >= T_E) & (st < T_E + 2 * S)).sum()
    assert abs(d["nan_frac"] - d["n_nan"] / n_win) < 1e-9 and 0.15 < d["nan_frac"] < 0.25
    # the valid samples start after 2 s where the braking setpoint has slowed (v=0 at t=2 s): truth lag error there ~0
    assert d["max_dev"] < 0.05, d
    assert d["max_dev_vint"] is not None
    # all NaN -> no number
    d2 = g.deviation(tt, txy, st, np.full_like(sp, np.nan), v, np.zeros(2), T_E, T_E + 15 * S)
    assert d2["max_dev"] is None and d2["nan_frac"] == 1.0


def test_entry_and_window():
    t = np.arange(0, 60 * S, S // 100)
    nav = np.full(len(t), 14.0); nav[t >= 12 * S] = 4.0; nav[t >= 20 * S] = 14.0
    fs = (nav == 4).astype(float)
    te, n, how = g.find_entry(t, nav, fs, 5 * S, 17 * S)
    assert te == 12 * S and n == 4
    end, why = g.window_end(t, nav, te)
    assert end == 20 * S and "14" in why
    end, why = g.window_end(t, nav, te, kill_t=15 * S)
    assert end == 15 * S and why == "kill event"
    nav2 = np.full(len(t), 4.0); nav2[t >= 12 * S] = 4.0         # already in hold: failsafe rise only
    fs2 = (t >= 13 * S).astype(float)
    te, n, how = g.find_entry(t, nav2, fs2, 5 * S, 17 * S)
    assert te == 13 * S and "failsafe" in how
    end, why = g.window_end(t, nav2, te)
    assert end == 13 * S + 15 * S and why == "15 s"


if __name__ == "__main__":
    for k, f in list(globals().items()):
        if k.startswith("test_"):
            f(); print("ok", k)
