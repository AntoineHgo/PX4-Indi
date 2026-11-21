"""Self-test of g55_g57_key2.py on synthetic data with known answers. Run: python3 -m pytest or python3 this file."""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import g55_g57_key2 as k  # noqa: E402

LEM = dict(shape='lemniscate', ax=5.0, ay=2.5, w=6.0 / math.sqrt(50.0), laps=2, ramp_s=3.0)
CIR = dict(shape='circle', r=5.0, z_amp=0.75, w=1.0, laps=3, ramp_s=3.0)
DUR = 2 * math.pi * 2 / LEM['w'] + 3.0
T = np.arange(0, DUR + 10, 1 / 800)
HOLD = np.array([1.0, -2.0, -5.0])


def synth(offset, traj=LEM, t0=4.0):
    pos = np.array([HOLD + k.ref_offset(traj, tt - t0) + offset for tt in T])
    return pos


def test_phase_closed():
    assert abs(k.phase(LEM, DUR) - 4 * math.pi) < 1e-9
    assert abs(k.phase(LEM, 0)) < 1e-12
    assert np.allclose(k.ref_offset(LEM, DUR), 0, atol=1e-9)
    # cruise peak speed at phi = 0 is w*sqrt(ax^2+4ay^2) = 6 m/s
    sp = np.linalg.norm((k.ref_offset(LEM, 0.5 + 1e-4) - k.ref_offset(LEM, 0.5 - 1e-4)) / 2e-4)
    assert sp < 6.0 + 1e-6


def test_rms_known_offset_pass_fail():
    # constant offset (0.3, 0.4, 0.2): horizontal RMS 0.5 exactly, vertical 0.2
    h, v, _ = k.track_rms(T, synth(np.array([0.3, 0.4, 0.2])), HOLD, LEM, 4.0, DUR)
    assert abs(h - 0.5) < 1e-9 and abs(v - 0.2) < 1e-9
    h, v, _ = k.track_rms(T, synth(np.array([0.6, 0.0, 0.0])), HOLD, LEM, 4.0, DUR)  # FAIL case
    assert h > k.H_LIM
    h, v, _ = k.track_rms(T, synth(np.array([0.2, 0.0, 0.1])), HOLD, LEM, 4.0, DUR)  # PASS case
    assert h <= k.H_LIM and v <= k.V_LIM
    h, v, _ = k.track_rms(T, synth(np.array([0, 0, 0.35])), HOLD, LEM, 4.0, DUR)
    assert v > k.V_LIM
    # circle with vertical sine: zero error against itself
    h, v, _ = k.track_rms(T, synth(np.zeros(3), CIR), HOLD, CIR, 4.0, 2 * math.pi * 3 + 3.0)
    assert h < 1e-9 and v < 1e-9


def test_sinusoidal_error_rms():
    # error 0.4 sin(2 pi t) in x over an integer number of periods: RMS 0.4/sqrt(2)
    pos = synth(np.zeros(3))
    pos[:, 0] += 0.4 * np.sin(2 * math.pi * T)
    h, _, _ = k.track_rms(T, pos, HOLD, LEM, 4.0, 10.0)
    assert abs(h - 0.4 / math.sqrt(2)) < 1e-3


def vs_signals(vx_end, vx_noise):
    t = np.arange(0, 20, 1 / 100)
    vx = np.where((t >= 5) & (t < 10), 2.0, 0.0) + vx_noise
    vx = np.where(t >= 13.5, vx_end, vx)
    z = np.full_like(t, -5.0)
    return t, vx, z


def test_vel_step_pass_fail():
    t, vx, z = vs_signals(0.05, 0.0)
    rms, end, dz = k.vel_step(t, vx, z, 5.0, 10.0, 14.0)
    assert rms < 1e-9 and abs(end - 0.05) < 1e-9 and dz == 0
    t, vx, z = vs_signals(0.15, 0.0)  # FAIL: end speed 0.15 > 0.1
    assert k.vel_step(t, vx, z, 5.0, 10.0, 14.0)[1] > k.VS_END_LIM
    # constant -0.3 m/s error over the last 3 s: RMS 0.3 > 0.2 (FAIL)
    t, vx, z = vs_signals(0.0, 0.0)
    vx = np.where((t >= 7.0 + 1e-9) & (t < 10), 1.7, vx)
    assert abs(k.vel_step(t, vx, z, 5.0, 10.0, 14.0)[0] - 0.3) < 0.01
    z = np.where(t > 8, -5.4, -5.0)  # FAIL dz 0.4
    assert abs(k.vel_step(t, vx, z, 5.0, 10.0, 14.0)[2] - 0.4) < 1e-9


def quat_pitch(deg):
    h = math.radians(deg) / 2
    return np.array([math.cos(h), 0.0, math.sin(h), 0.0])


def test_edge_pass_fail():
    t = np.arange(0, 10, 1 / 200)
    hover = 0.137
    for step_frac, tilt_err, ok in ((0.10, 3.0, True), (0.30, 3.0, False), (0.10, 7.0, False)):
        thr = np.where(t >= 5.0, hover * (1 + step_frac), hover)
        q = np.tile(quat_pitch(tilt_err), (len(t), 1))
        qd = np.tile(quat_pitch(0.0), (len(t), 1))
        step, tilt = k.edge_metrics(5.0, t, thr, hover, t, q, t, qd)
        assert abs(step - step_frac) < 1e-9 and abs(tilt - tilt_err) < 1e-6
        assert (step <= k.THR_LIM_FRAC and tilt <= k.TILT_LIM_DEG) == ok


def test_loc_tilt():
    t = np.arange(0, 3, 1 / 100)
    q = np.tile(quat_pitch(70.0), (len(t), 1))
    q[t > 1.1] = quat_pitch(0.0)  # 70 deg for 1.1 s -> LOC
    assert k.loc_tilt(t, q)
    q[t > 0.1] = quat_pitch(0.0)  # 0.1 s only -> no LOC
    assert not k.loc_tilt(t, q)


if __name__ == '__main__':
    for n, f in list(globals().items()):
        if n.startswith('test_'):
            f()
            print('ok', n)
