"""Step-response traces (committed CSV) and the step metrics computed from them."""
import numpy as np

from style import path

AXES = ("roll", "pitch", "yaw")
LIM = {"roll": (5.0, 450.0), "pitch": (5.0, 450.0), "yaw": (5.0, 1350.0)}  # overshoot %, settle ms


def load(ctrl, ax):
    d = np.genfromtxt(path(f"results/report_traces/step_{ctrl}_{ax}.csv"), delimiter=",", names=True)
    return {k: d[k] for k in d.dtype.names}


def metrics(d):
    """Overshoot (%) and 2 % settling time (ms) of the attitude estimate after the step (t >= 0)."""
    m = d["t_s"] >= 0
    t, y, s = d["t_s"][m], d["att_deg"][m], d["att_sp_deg"][m]
    amp = s[-1]
    os_ = max(0.0, (y.max() - amp) / amp * 100)
    out = np.nonzero(np.abs(y - amp) > 0.02 * abs(amp))[0]
    settle = t[out[-1] + 1] * 1e3 if len(out) and out[-1] + 1 < len(t) else np.nan
    return os_, settle
