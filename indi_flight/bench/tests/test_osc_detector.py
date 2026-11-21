import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import osc_detector as od

FS = 800.0


def sig(rms, dur, f0=12.0, noise_rms=1.0, seed=0, t_on=0.0, t_off=None):
    rng = np.random.default_rng(seed)
    t = np.arange(0, dur, 1 / FS)
    on = (t >= t_on) & (t < (t_off if t_off is not None else dur + 1))
    s = rms * np.sqrt(2) * np.sin(2 * np.pi * f0 * t) * on
    return t, s + rng.normal(0, noise_rms, len(t))


def run(rms, **kw):
    t, p = sig(rms, 8.0, **kw)
    z = np.zeros_like(p)
    return od.detect(t, p, z, z)


def test_4dps_not_flagged():
    for sd in range(5):
        w, s = run(4.0, seed=sd)
        assert not any(x["flagged"] for x in w) and not s


def test_8dps_flagged():
    for sd in range(5):
        w, s = run(8.0, seed=sd)
        assert s and sum(x["flagged"] for x in w) >= 3


def test_short_burst_not_sustained():
    # burst over the last 3 s of a 9 s record: exactly the 2 final windows flag (Hann edge weighting)
    t, p = sig(40.0, 9.0, t_on=6.0)
    z = np.zeros_like(p)
    w, s = od.detect(t, p, z, z)
    assert sum(x["flagged"] for x in w) == 2 and not s


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("ok", n)
