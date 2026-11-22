"""Self-test of bench/ident_actc.py on a synthetic plant.
Run: python3 -m pytest -q bench/tests/test_ident_actc.py  or  python3 bench/tests/test_ident_actc.py"""
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import ident_actc as ia  # noqa: E402

FS = 800.0
DT = 1.0 / FS
RPM_MAX = 10000.0
HOVER = 0.4
GAIN, ICPT = 0.95, 0.02
TLEN = 24.0


def multisine(n, seed, amp=0.025):
    """12 tones, 3-60 Hz log-spaced, random phases, `amp` per tone (peak about 3 amp, the injector band)."""
    r = np.random.default_rng(seed)
    f = np.geomspace(3.0, 60.0, 12)
    t = np.arange(n) * DT
    s = sum(np.sin(2 * np.pi * fi * t + r.uniform(0, 2 * np.pi)) for fi in f)
    return amp * s


def plant(tau_up, tau_down, delay_ms, frames, seed=0, noise=True, amp=0.025, const=False):
    """Returns (t, u, rpm). u is the logged command; the plant sees u delayed; rpm is quantised/noisy and
    delayed by `frames` samples of 1.25 ms (telemetry)."""
    n = int(TLEN * FS)
    r = np.random.default_rng(seed + 1000)
    ms = np.zeros(n) if const else multisine(n, seed, amp)
    d = int(round(delay_ms * 1e-3 * FS))
    au, ad = 1 - np.exp(-DT / tau_up), 1 - np.exp(-DT / tau_down)
    u, y, x = np.zeros(n), np.zeros(n), HOVER
    for k in range(n):
        u[k] = HOVER + ms[k]
        ud = u[k - d] if k >= d else HOVER
        x += (au if ud > x else ad) * (ud - x)
        y[k] = ICPT + GAIN * x
    rpm = np.sqrt(np.maximum(y, 0)) * RPM_MAX
    if noise:
        rpm = rpm + r.normal(0, 25.0, n)
        rpm = np.round(rpm / 20.0) * 20.0          # eRPM quantisation
    rpm = np.concatenate([np.full(frames, rpm[0]), rpm[: n - frames]])  # telemetry frames
    return np.arange(n) * DT, u, rpm


def run(tau_up, tau_down, delay_ms, frames, force_delay=None, **kw):
    t, u, rpm = plant(tau_up, tau_down, delay_ms, frames, **kw)
    r = ia.identify(t, u[:, None], t, rpm[:, None], RPM_MAX, force_delay=force_delay)
    return r["motors"][0], (delay_ms + frames * 1.25)


def closed_loop_plant(tau_up, tau_down, delay_ms, frames, K, seed=0, amp=0.025):
    """Command = multisine - K * (noisy measured y, as telemetry delivers it); true closed loop."""
    n = int(TLEN * FS)
    r = np.random.default_rng(seed + 2000)
    ms = multisine(n, seed, amp)
    d = int(round(delay_ms * 1e-3 * FS))
    au, ad = 1 - np.exp(-DT / tau_up), 1 - np.exp(-DT / tau_down)
    u, y, rpm, x = np.zeros(n), np.zeros(n), np.zeros(n), HOVER
    y0 = ICPT + GAIN * HOVER
    for k in range(n):
        ym = (rpm[k - 1 - frames] / RPM_MAX) ** 2 if k - 1 - frames >= 0 else y0
        u[k] = HOVER + ms[k] - K * (ym - y0)
        ud = u[k - d] if k >= d else HOVER
        x += (au if ud > x else ad) * (ud - x)
        y[k] = ICPT + GAIN * x
        rpm[k] = np.round((np.sqrt(max(y[k], 0)) * RPM_MAX + r.normal(0, 25.0)) / 20.0) * 20.0
    # the controller read rpm[k-1-frames]; logged telemetry is rpm shifted by the frames
    rpm_log = np.concatenate([np.full(frames, rpm[0]), rpm[: n - frames]])
    return np.arange(n) * DT, u, rpm_log


SLOW = (0.0165, 0.033, 0.099)
ASYM = ((1.0, 1.0), (1.0, 3.0), (3.0, 1.0))   # (up, down) multipliers of the fast tau: (1, 3) down-slow, (3, 1) up-slow
LINES = []


def taus(slow, a):
    """(tau_up, tau_down) with the slower one = slow; a = (m_up, m_down), asymmetry 3 puts the factor 3 on the slow side."""
    fast = slow / 3.0 if max(a) == 3.0 else slow
    return (slow if a[0] == 3.0 else fast, slow if a[1] == 3.0 else fast)


def err(est, true):
    return abs(est - true) / true


def test_noise_free():
    worst = 0.0
    for slow in SLOW:
        for a in ASYM:
            tu, td = taus(slow, a)
            for dly, fr in ((0, 0), (10, 0), (5, 2)):
                m, dtrue = run(tu, td, dly, fr, noise=False)
                e = max(err(m["tau_up"], tu), err(m["tau_down"], td))
                dd = abs(m["delay_ms"] - dtrue)
                worst = max(worst, e)
                LINES.append(("noise-free", tu, td, dly, fr, m, dtrue))
                assert e <= 0.02, (tu, td, dly, fr, m["tau_up"], m["tau_down"])
                assert dd <= 1.25 + 1e-9, (tu, td, dly, fr, m["delay_ms"], dtrue)
                assert m["pass_"], (tu, td, dly, fr, m["flags"])
    return worst


def test_noisy():
    worst = 0.0
    for slow in SLOW:
        for a in ASYM:
            tu, td = taus(slow, a)
            for dly, fr in ((0, 0), (10, 3), (4, 1)):
                m, dtrue = run(tu, td, dly, fr, noise=True, seed=3)
                e = max(err(m["tau_up"], tu), err(m["tau_down"], td))
                worst = max(worst, e)
                LINES.append(("noisy", tu, td, dly, fr, m, dtrue))
                assert e <= 0.10, (tu, td, dly, fr, m["tau_up"], m["tau_down"])
                assert m["pass_"], (tu, td, dly, fr, m["flags"])
    return worst


SUB = 10   # sub-steps per sample for the continuous-time-delay plant


def plant_sub(tau_up, tau_down, delay_ms, frames, seed=0, noise=True, amp=0.025):
    """Independent plant for off-grid delays: command held (ZOH) per sample, lag integrated in SUB sub-steps per
    sample, delay applied in continuous time (resolution DT/SUB = 0.125 ms), rpm noisy/quantised, `frames` of telemetry."""
    n = int(TLEN * FS)
    r = np.random.default_rng(seed + 1000)
    ms = multisine(n, seed, amp)
    u = HOVER + ms
    ds = int(round(delay_ms * 1e-3 * FS * SUB))
    au, ad = 1 - np.exp(-DT / SUB / tau_up), 1 - np.exp(-DT / SUB / tau_down)
    y, x = np.zeros(n), HOVER
    for k in range(n):
        for j in range(SUB):
            m = (k * SUB + j - ds) // SUB
            ud = u[m] if m >= 0 else HOVER
            x += (au if ud > x else ad) * (ud - x)
        y[k] = ICPT + GAIN * x
    rpm = np.sqrt(np.maximum(y, 0)) * RPM_MAX
    if noise:
        rpm = np.round((rpm + r.normal(0, 25.0, n)) / 20.0) * 20.0
    rpm = np.concatenate([np.full(frames, rpm[0]), rpm[: n - frames]])
    return np.arange(n) * DT, u, rpm


FRAC_CASES = ((0.033, 0.033, 0.625, 0), (0.033, 0.099, 7.6, 2), (0.099, 0.033, 7.6, 2), (0.033, 0.033, 3.3, 1),
              (0.0165, 0.0165, 4.4, 1), (0.033, 0.033, 0.3, 0), (0.099, 0.099, 9.7, 3),
              (0.033, 0.033, 7.3, 0), (0.033, 0.033, 6.275, 0), (0.033, 0.099, 0.625, 0), (0.099, 0.033, 0.625, 0))


def _frac(noise, limit):
    worst = 0.0
    for tu, td, dly, fr in FRAC_CASES:
        t, u, rpm = plant_sub(tu, td, dly, fr, noise=noise, seed=3)
        m = ia.identify(t, u[:, None], t, rpm[:, None], RPM_MAX)["motors"][0]
        dtrue = dly + fr * 1.25
        e = max(err(m["tau_up"], tu), err(m["tau_down"], td))
        worst = max(worst, e)
        LINES.append(("frac-noisy" if noise else "frac-free", tu, td, dly, fr, m, dtrue))
        assert e <= limit, (tu, td, dly, fr, m["tau_up"], m["tau_down"])
        if not noise:
            assert abs(m["delay_ms"] - dtrue) <= 0.25 * 1.25 + 1e-9, (tu, td, dly, fr, m["delay_ms"], dtrue)
        assert m["pass_"], (tu, td, dly, fr, m["flags"])
    return worst


def test_fractional_delay_noise_free():
    return _frac(False, 0.02)


def test_fractional_delay_noisy():
    return _frac(True, 0.10)


def test_closed_loop():
    worst = 0.0
    for slow in SLOW:
        for a in ASYM:
            tu, td = taus(slow, a)
            t, u, rpm = closed_loop_plant(tu, td, 10, 3, K=1.5, seed=5)
            m = ia.identify(t, u[:, None], t, rpm[:, None], RPM_MAX)["motors"][0]
            e = max(err(m["tau_up"], tu), err(m["tau_down"], td))
            worst = max(worst, e)
            LINES.append(("closed-loop", tu, td, 10, 3, m, 10 + 3 * 1.25))
            assert e <= 0.10, (tu, td, m["tau_up"], m["tau_down"])
            assert m["pass_"], (tu, td, m["flags"])
    return worst


def test_forced_delay_mismatch_fails():
    """Truth 10 ms + 2 frames = 10.5 ms (8.4 samples); the fit is forced to d = 2 and d = 18 samples (about 10 ms off)."""
    for tu, td in ((0.033, 0.033), (0.011, 0.033), (0.099, 0.099)):
        for noise in (False, True):
            t, u, rpm = plant(tu, td, 10, 2, noise=noise, seed=7)
            r0 = ia.identify(t, u[:, None], t, rpm[:, None], RPM_MAX)["motors"][0]
            assert r0["pass_"], r0["flags"]
            for forced in (2, 18):
                m = ia.identify(t, u[:, None], t, rpm[:, None], RPM_MAX, force_delay=forced)["motors"][0]
                LINES.append((f"forced d={forced}", tu, td, 10, 2, m, 10 + 2 * 1.25))
                assert not m["pass_"], (tu, td, noise, forced, m["residual"], m["structure"], m["flags"])


def test_unexcited_fails():
    for noise in (False, True):
        t, u, rpm = plant(0.033, 0.033, 5, 1, noise=noise, const=True)
        m = ia.identify(t, u[:, None], t, rpm[:, None], RPM_MAX)["motors"][0]
        assert not m["pass_"], m
    # excitation far below the measurement noise (0.002 per tone) must also fail
    t, u, rpm = plant(0.033, 0.033, 5, 1, noise=True, amp=0.002)
    m = ia.identify(t, u[:, None], t, rpm[:, None], RPM_MAX)["motors"][0]
    LINES.append(("weak exc.", 0.033, 0.033, 5, 1, m, 6.25))
    assert not m["pass_"], m


def test_symmetric_vs_asymmetric_info():
    for slow in SLOW:
        for a in ASYM[1:]:
            tu, td = taus(slow, a)
            m, _ = run(tu, td, 5, 1, noise=True, seed=11)
            print(f"info asym tau_up {1e3*tu:.1f} tau_down {1e3*td:.1f}: tau_sym {1e3*m['tau_sym']:.1f} ms "
                  f"= {m['tau_sym']/max(tu, td):.3f} x tau_slow, {m['tau_sym']/((tu+td)/2):.3f} x tau_mean")


def main():
    t0 = time.time()
    for name, f in sorted(globals().items()):
        if name.startswith("test_") and callable(f):
            t1 = time.time()
            w = f()
            print(f"{name}: ok  worst tau error {100*w:.2f} %  ({time.time()-t1:.0f} s)" if w is not None else f"{name}: ok ({time.time()-t1:.0f} s)")
    print("rows: kind tau_up tau_down delay frames | est up down delay_ms resid se_tau")
    for k, tu, td, dly, fr, m, dtrue in LINES:
        print(f"{k:12s} {1e3*tu:6.1f} {1e3*td:6.1f} {dly:5.2f} {fr} | {1e3*m['tau_up']:6.1f} {1e3*m['tau_down']:6.1f} "
              f"{m['delay_ms']:5.2f} (true {dtrue:5.2f}) resid {m['residual']:.3f} struct {m['structure']:.3f} se {m['se_ln_tau_up']:.3f}/{m['se_ln_tau_down']:.3f}/"
              f"{m['se_delay_samples']:.2f} {'PASS' if m['pass_'] else 'FAIL ' + ','.join(m['flags'])}")
    print(f"total {time.time()-t0:.0f} s")


if __name__ == "__main__":
    main()
