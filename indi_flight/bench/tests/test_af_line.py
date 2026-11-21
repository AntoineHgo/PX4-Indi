import os, sys
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from af_line import amp_spectrum, peak


def test_known_sine_jittered_timestamps():
    rng = np.random.default_rng(1)
    t = np.cumsum(rng.uniform(0.008, 0.0144, 6000))  # irregular ~88.9 Hz
    A, f0 = 0.25, 6.84
    x = A * np.sin(2 * np.pi * f0 * t + 0.7) + 0.3
    f, a = amp_spectrum(t, x, 10.0, 20.0)
    pf, pa = peak(f, a, 2.0, 10.0)
    assert abs(pf - f0) < 0.1
    assert abs(pa - A) / A < 0.05


if __name__ == "__main__":
    test_known_sine_jittered_timestamps(); print("ok")
