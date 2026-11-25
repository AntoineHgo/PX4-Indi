"""S227 (D-G3-KEYS-S227): both G3 keys read items 2, 5, 6 the same way. Synthetic cases that fail on the pre-S227 code.
Key 1: position limit cycle windows from the hold start. Key 2: item 6 per axis, item 5 in stick mode vs q_d."""
import os, sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g3_checks as G  # noqa: E402
import g3_checks_key2 as K  # noqa: E402
import test_g3_checks_s226 as T1  # noqa: E402
import test_g3_checks_key2_s226 as T2  # noqa: E402

_EVAL = G.evaluate


def _key1_pos_cycle(osc_from, monkeypatch):
    rj = T1.run_json(fault=False, hold_dur=30.0)                      # hold 38..68; item 3 = 58..68; 3 windows 38/48/58
    win = G.windows_from_run_json(rj, 0.0)
    orig = _EVAL
    monkeypatch.setattr(G, "evaluate", lambda *a, **k: orig(*a, hold_win=[win["hold"]["t"], win["hold"]["t"] + win["hold"]["dur_s"]], **k))
    err = lambda t: 0.4 * np.sin(2 * np.pi * 0.2 * t) * (t >= osc_from)   # 0.8 m p2p per 10 s window
    r, _ = T1.make(rj=rj, pos_err=err)
    return r["item2_oscillation"]["position"]


def test_key1_position_limit_cycle_windows_start_at_hold(monkeypatch):
    p = _key1_pos_cycle(38.0, monkeypatch)                            # oscillation through the whole hold
    assert p["sustained"] and p["max_consecutive_windows"] == 3, p
    q = _key1_pos_cycle(48.0, monkeypatch)                            # only 2 hold windows oscillate: not a limit cycle
    assert not q["sustained"] and q["windows"] == 3, q


def test_key2_item6_gates_per_axis():
    rj = T2.rj_stick("acro")
    d = lambda t: np.stack([T2.box(t, 0, 120, v) for v in (4.0, 4.0, 4.0)], 1)       # 4 dps on each axis: vector 6.9, each axis 4
    r = T2.build(rj, "rate", drate=d)["item6_rate_hold"]
    assert r["rate_rms_dps"] > 5.0 and max(r["axis_rms_dps"]) < 5.0 and r["pass"], r
    d1 = lambda t: np.stack([T2.box(t, 0, 120, 6.0), 0 * t, 0 * t], 1)                # one axis at 6 dps still fails
    assert not T2.build(rj, "rate", drate=d1)["item6_rate_hold"]["pass"]


def _tilt_q(t, ang):
    a = np.radians(ang(t)); return np.stack([np.cos(a / 2), np.sin(a / 2), 0 * a, 0 * a], 1)


def test_key2_item5_stick_reference_is_commanded_attitude():
    rj = T2.rj_stick("stabilized"); te = 60.0
    ts_ = np.arange(0, 120.0, 0.02); step = lambda t: T2.box(t, te, 200, 10.0)
    follow = T2.build(rj, "attitude", dtilt=step, att_t=ts_, att_q=_tilt_q(ts_, step))["item5_recovery"]   # q_d moves, vehicle tracks it
    assert follow["pass"], follow
    stuck = T2.build(rj, "attitude", att_t=ts_, att_q=_tilt_q(ts_, step))["item5_recovery"]                # q_d moves, vehicle does not
    assert not stuck["pass"], stuck
