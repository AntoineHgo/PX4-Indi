"""Q33 self-tests of the second key (bench/g3_checks_key2.py): event hover (EVENT_HOVER_SPEC.md). Synthetic data with a known answer.
Scenario times used: settle 20-23 s, event hover t0 = 23 s .. 46 s, gust at t0 + 12 = 35 s, main 46..76 s, hold 76..111 s.
Break-checks: see results/q33_tooling_s230/KEY2_README.md.
Run: cd indi_flight/bench/tests && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q test_g3_q33_key2.py"""
import os, sys
import numpy as np
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import g3_checks_key2 as K
from test_g3_checks_key2_s226 import build, box, rates, T

T0, GUST, EV_END, M0, M1, H0, H1 = 23.0, 35.0, 46.0, 46.0, 76.0, 76.0, 111.0
us = lambda s: int(round(s * 1e6))


def rj_q33(main="traj", mode=None, fault=True, wind=True, timeline=True):
    ev = [{"name": "settle", "t_us": us(T0 - 3), "dur_s": 3.0}, {"name": "event", "t_us": us(T0), "dur_s": EV_END - T0},
          {"name": main, "t_us": us(M0), "dur_s": M1 - M0}, {"name": "hold", "t_us": us(H0), "dur_s": H1 - H0}]
    rj = {"events": ev}
    if mode: rj["stick"] = {"mode": mode}
    if timeline:
        rj["g3_timeline"] = {"version": 1, "time_base": "px4", "scenario": "g3_lemniscate" if main == "traj" else "g3_stick_zsine",
                             "main_segment": main, "fault_on": fault, "wind_on": wind, "event_t0_us": us(T0),
                             "gust_us": us(GUST) if wind else None, "event_end_us": us(EV_END), "main_start_us": us(M0),
                             "main_end_us": us(M1), "hold_start_us": us(H0), "hold_end_us": us(H1),
                             "sag_ramp_start_us": None, "sag_ramp_end_us": None}
    return rj


def dx(a, b, v=1.0):
    return lambda t: np.stack([box(t, a, b, v), 0 * t, 0 * t], 1)


def tilt(a, b, v=5.0):
    return lambda t: box(t, a, b, v)


# ---------------------------------------------------------------- windows / timeline
def test_q33_key2_windows_from_timeline():
    w = K.windows_from_run(rj_q33())
    assert w["main"] == [M0, M1] and w["mode"] == "position" and w["step_t"] == [T0, GUST]
    assert w["ev5"] == [("fault@t0", T0), ("gust", GUST)] and w["event_win"] == [T0, EV_END] and w["hold"] == [H0, H1]
    assert w["item3"] == [H1 - 10, H1] and w["item6"] == [H1 - 20, H1]
    f = K.windows_from_run(rj_q33(wind=False)); g = K.windows_from_run(rj_q33(fault=False)); n = K.windows_from_run(rj_q33(fault=False, wind=False))
    assert f["step_t"] == [T0] and [e[0] for e in f["ev5"]] == ["fault@t0"]
    assert g["step_t"] == [T0, GUST] and [e[0] for e in g["ev5"]] == ["gust"]     # wind on: t0 (wind ramp) and gust are skip points, only the gust is scored
    assert n["step_t"] == [] and n["ev5"] == []
    assert K.windows_from_run(rj_q33("stick", "acro"))["mode"] == "rate" and K.windows_from_run(rj_q33("stick", "stabilized"))["mode"] == "attitude"


def test_q33_key2_event_segment_without_timeline_is_error_old_runs_unchanged():
    with pytest.raises(ValueError, match="g3_timeline"):
        K.windows_from_run(rj_q33(timeline=False))
    old = K.windows_from_run({"events": [e for e in rj_q33(timeline=False)["events"] if e["name"] != "event"]})
    assert old["step_t"] == [M0] and old["main"] == [M0, M1] and "ev5" not in old   # pre-Q33: anchor = main start


# ---------------------------------------------------------------- item 2: gust skip point
def test_q33_key2_item2_gust_skip_window():
    sp = tuple(K.windows_from_run(rj_q33())["step_t"])
    r = rates((GUST - 1, GUST + 3), step_t=sp)
    starts = [x["start_s"] for x in r["skipped_windows"]]
    assert not r["sustained"] and starts == [T0 - 3, T0 - 2, T0 - 1, T0, GUST - 3, GUST - 2, GUST - 1, GUST]   # 4 windows per skip point
    assert rates((GUST - 1, GUST + 3), step_t=(T0,))["sustained"]          # control: without the gust skip point the same sine is flagged
    assert rates((GUST - 1, GUST + 3), step_t=tuple(K.windows_from_run(rj_q33(wind=False))["step_t"]))["sustained"]   # no wind: no gust skip
    # t0 is a skip point as well
    assert not rates((T0 - 1, T0 + 3), step_t=sp)["sustained"]


# ---------------------------------------------------------------- item 4: main segment only
def test_q33_key2_item4_window_is_main_segment_only():
    # 1 m offset in the event hover and in the hold, nothing in the main segment: item 4 passes, window = main only
    r = build(rj_q33(), "position", dpos=lambda t: dx(T0, EV_END)(t) + dx(H0, H1)(t))["item4_tracking"]
    assert r["window_s"] == [M0, M1] and r["pass"] and r["horiz_rms_m"] < 0.01
    # 0.7 m in the last 19.5 s of the main segment: rms 0.7 sqrt(19.5/30) = 0.564 > 0.5 fails
    b = build(rj_q33(), "position", dpos=dx(M1 - 19.5, M1, 0.7))["item4_tracking"]
    assert not b["pass"] and abs(b["horiz_rms_m"] - 0.7 * np.sqrt(19.5 / 30)) < 0.01
    assert build(rj_q33("stick", "stabilized"), "attitude")["item4_tracking"]["applicable"] is False


# ---------------------------------------------------------------- item 5
def ev(r, i): return r["item5_recovery"]["events"][i]


def test_q33_key2_item5_position_both_events_position_term():
    run = lambda a, b, v=1.0: build(rj_q33(), "position", dpos=dx(a, b, v))
    ok = run(T0, T0 + 3)                                       # fault: 1 m for 3 s, back at 3 s
    assert ok["item5_recovery"]["pass"] and [e["event"] for e in ok["item5_recovery"]["events"]] == ["fault@t0", "gust"]
    assert abs(ev(ok, 0)["t_back_s"] - 3.0) < 0.01 and ev(ok, 1)["t_back_s"] == 0.0
    slow_f = run(T0, T0 + 6)                                   # fault event too slow, gust event fine
    assert not slow_f["item5_recovery"]["pass"] and not ev(slow_f, 0)["pass"] and ev(slow_f, 1)["pass"]
    slow_g = run(GUST, GUST + 6)                               # gust event too slow, fault event fine: both events scored separately
    assert not slow_g["item5_recovery"]["pass"] and ev(slow_g, 0)["pass"] and not ev(slow_g, 1)["pass"]
    assert ev(run(GUST, GUST + 3), 1)["pass"]
    re_ = run(GUST + 3, GUST + 4, 0.5)                         # re-excursion 0.5 m within 5 s of the return
    assert not re_["item5_recovery"]["pass"] and ev(re_, 1)["re_excursion"]
    assert not run(T0, T0 + 3, 0.2)["item5_recovery"]["events"][0]["t_back_s"] > 0   # 0.2 m is inside the 0.3 m band from the start


def test_q33_key2_item5_position_reference_is_hover_setpoint_not_commanded_path():
    # setpoint moves away after the event hover (main segment): irrelevant; vehicle stays on the hover point -> passes. Static ref from event hover.
    ts = np.arange(0, 120, 0.02); sx = np.where(ts > EV_END, 4.0, 0.0)
    r = build(rj_q33(), "position", sp_xy=np.stack([sx, 0 * ts], 1))
    assert r["item5_recovery"]["pass"]
    # a 2 s setpoint blip at the start of the event hover (my reading: the reference is the static hover point = median over the event hover)
    r = build(rj_q33(), "position", sp_xy=np.stack([np.where((ts >= T0) & (ts < T0 + 2), 1.0, 0.0), 0 * ts], 1))
    assert ev(r, 0)["t_back_s"] == 0.0 and r["item5_recovery"]["pass"]
    # hover setpoint 1 m off the truth throughout the event hover: never within 0.3 m -> fails closed
    r = build(rj_q33(), "position", sp_xy=np.stack([np.where(ts < EV_END, 1.0, 0.0), 0 * ts], 1))
    assert not r["item5_recovery"]["pass"] and ev(r, 0)["t_back_s"] is None


def test_q33_key2_item5_position_tilt_term_and_attitude_mode():
    run = lambda rj, mode, **k: build(rj, mode, **k)
    p = run(rj_q33(), "position", dtilt=tilt(GUST, GUST + 6))          # 5 deg for 6 s at the gust: position fine, tilt out
    assert not p["item5_recovery"]["pass"] and not ev(p, 1)["pass"] and ev(p, 0)["pass"]
    assert run(rj_q33(), "position", dtilt=tilt(T0, T0 + 2))["item5_recovery"]["pass"]
    assert not run(rj_q33(), "position", dtilt=tilt(T0, T0 + 6))["item5_recovery"]["pass"]
    rs = rj_q33("stick", "stabilized")
    a = run(rs, "attitude", dtilt=tilt(GUST, GUST + 6))
    assert a["item5_recovery"]["mode"] == "attitude" and not a["item5_recovery"]["pass"] and not ev(a, 1)["pass"] and ev(a, 0)["pass"]
    assert run(rs, "attitude", dtilt=tilt(GUST, GUST + 2))["item5_recovery"]["pass"]
    assert not run(rs, "attitude", dtilt=tilt(T0, T0 + 6))["item5_recovery"]["pass"]
    assert ev(run(rs, "attitude", dtilt=tilt(T0, T0 + 3)), 0)["t_back_s"] > 2.9
    assert run(rs, "attitude", dpos=dx(GUST, GUST + 6, 2.0))["item5_recovery"]["pass"]   # no position term in attitude mode


def test_q33_key2_item5_rate_mode_not_applicable_and_ramp_not_scored():
    r = build(rj_q33("stick", "acro"), "rate", dtilt=tilt(GUST, GUST + 9))["item5_recovery"]
    assert r["applicable"] is False and r["pass"] and r["events"] == []
    # wind only (no fault): only the gust is scored, the wind-ramp start t0 is not an event even with a big excursion there
    w = build(rj_q33(fault=False), "position", dpos=dx(T0, T0 + 9))["item5_recovery"]
    assert [e["event"] for e in w["events"]] == ["gust"] and w["pass"]
    f = build(rj_q33(wind=False), "position", dpos=dx(GUST, GUST + 9))["item5_recovery"]    # fault only: the gust time is not an event
    assert [e["event"] for e in f["events"]] == ["fault@t0"] and f["pass"]
    n = build(rj_q33(fault=False, wind=False), "position")["item5_recovery"]
    assert n["events"] == [] and n["pass"]
