#!/usr/bin/env python3
"""Key 1 with Q19 A: bench/g3_checks.py unchanged, except command-chatter windows overlapping [t_change, t_change+3 s]
of any nav_state change are skipped (g3_checks only skipped the rate windows). Same CLI as g3_checks.py."""
import sys
sys.path.insert(0, "indi_flight/bench")
import g3_checks as k1
_nav, _t0 = [], [0.0]
_uni, _det, _eval = k1.uniform, k1.line_detector, k1.evaluate
def uniform(t, y, ta, te):
    r = _uni(t, y, ta, te); _t0[0] = float(r[0][0]); return r
def line_detector(xg, fs, band, min_rms=None, t_start=0.0, skip=(), rms_hz=None):
    if rms_hz is not None:   # command-chatter call only
        return _det(xg, fs, band, min_rms, _t0[0], [(c, c + k1.NAV_SKIP_S) for c in _nav], rms_hz)
    return _det(xg, fs, band, min_rms, t_start, skip, rms_hz)
def evaluate(*a, **kw):
    nav = kw.get("nav_changes") if "nav_changes" in kw else (a[14] if len(a) > 14 else None)
    _nav[:] = nav or []
    return _eval(*a, **kw)
k1.uniform, k1.line_detector, k1.evaluate = uniform, line_detector, evaluate
sys.exit(k1.main())
