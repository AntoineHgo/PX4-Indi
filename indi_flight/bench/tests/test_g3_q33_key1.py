"""Self-test of key 1 (bench/g3_checks.py) and of the runner timeline for the Q33 event hover (GATES "Owner amendment Q33"):
item 5 events (fault start t0, gust t0 + 12 s) on a static reference per mode, the item-2 gust skip, the item-4 main-segment window,
and the g3_timeline block of run.json. Synthetic truth with known answers (no flights).

    python3 -m pytest indi_flight/bench/tests/test_g3_q33_key1.py        (needs numpy, scipy, pytest; /tmp/g3venv)

Break-checks (S230): each rule was broken once in bench/g3_checks.py (see results/q33_tooling_s230/KEY1_README.md), the named test
had to FAIL, then the code was restored.
"""
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g3_checks as G  # noqa: E402
import g3_run as R  # noqa: E402
import scenarios as S  # noqa: E402

FS, T = 800.0, 100.0
T0, EV_DUR, MAIN_DUR, HOLD_DUR = 20.0, 23.0, 18.0, 35.0
GUST = T0 + 12.0                      # 32 s
MAIN0, HOLD0 = T0 + EV_DUR, T0 + EV_DUR + MAIN_DUR      # 43, 61  (hold 61..96)


def timeline(fault=True, wind=True, sag=True):
    us = lambda s: int(round(s * 1e6))   # noqa: E731
    return {"version": 1, "time_base": "test", "main_segment": "traj", "fault_on": fault, "wind_on": wind,
            "event_t0_us": us(T0), "gust_us": us(GUST) if wind else None, "event_end_us": us(MAIN0),
            "main_start_us": us(MAIN0), "main_end_us": us(HOLD0), "hold_start_us": us(HOLD0), "hold_end_us": us(HOLD0 + HOLD_DUR),
            "sag_ramp_start_us": 0 if sag else None, "sag_ramp_end_us": us(30.0) if sag else None}


def run_json(fault=True, wind=True, stick=False, with_timeline=True):
    ev = [{"name": "settle", "t_us": int(17e6), "dur_s": 3.0}, {"name": "event", "t_us": int(T0 * 1e6), "dur_s": EV_DUR},
          {"name": "stick" if stick else "traj", "t_us": int(MAIN0 * 1e6), "dur_s": MAIN_DUR},
          {"name": "hold", "t_us": int(HOLD0 * 1e6), "dur_s": HOLD_DUR}]
    rj = {"events": ev}
    if fault:
        rj["motor_fault"] = {"motor": 0, "thrust_scale": 0.7, "event_us": int(T0 * 1e6)}
    if wind:
        rj["disturbance"] = {"profile": "gust_x", "onset_us": int(T0 * 1e6)}
    if with_timeline:
        rj["g3_timeline"] = timeline(fault, wind)
    return rj


def make(rj=None, mode="position", pos_err=None, tilt=None, qd_tilt=None, burst=None, rate_mode=False, seed=0, delay_s=0.0):
    """Truth: hover at x = 0 outside the main segment, x = 3 sin(0.3 u) (u = time in the main segment) in it, z at 5 m. pos_err(t): extra x
    error [m]; tilt(t) / qd_tilt(t): vehicle / q_d tilt about x [deg] (default 0 = level); burst = (t_a, t_b, deg/s RMS): 30 Hz sine on p."""
    rng = np.random.default_rng(seed)
    rj = rj or run_json()
    win = G.windows_from_run_json(rj, 0.0)
    t = np.arange(0, T, 1 / FS)
    n = len(t)

    def path(tq):
        u = tq - MAIN0
        return np.where((u > 0) & (u < MAIN_DUR), 3.0 * np.sin(0.3 * u), 0.0)

    h = np.clip(t - 1.0, 0.0, 5.0)
    pos = np.stack([path(t - delay_s) + (pos_err(t) if pos_err else 0.0), np.zeros(n), -h], axis=1)
    pos[:, 2][t < 0.5] = 0.0
    th = np.radians(tilt(t)) if tilt else np.zeros(n)
    q = np.stack([np.cos(th / 2), np.sin(th / 2), np.zeros(n), np.zeros(n)], axis=1)
    w = np.radians(1.0) * rng.normal(size=(n, 3))
    if burst:
        m = (t >= burst[0]) & (t < burst[1])
        w[:, 0] += np.radians(burst[2]) * np.sqrt(2) * np.sin(2 * np.pi * 30.0 * t) * m
    cmd = 0.5 + 0.002 * rng.normal(size=(n, 4))
    tsp = np.arange(0, T, 0.01)
    sp_xyz = np.stack([path(tsp), np.zeros(len(tsp)), np.full(len(tsp), -5.0)], axis=1)
    thd = np.radians(qd_tilt(tsp)) if qd_tilt else np.zeros(len(tsp))
    att_sp = (tsp, np.stack([np.cos(thd / 2), np.sin(thd / 2), np.zeros(len(tsp)), np.zeros(len(tsp))], axis=1))
    t0, t1 = win["item3"]
    r = G.evaluate(t, pos, q, w, t, cmd, np.array([0.0, 0.0, -5.0]), t0, t1, mode=mode, step_starts=win["step_starts"],
                   track_win=win["track"], event_times=win["item5_events"], rate_mode=rate_mode, item6_win=win["item6"],
                   sp_xyz=(tsp, sp_xyz), att_sp=att_sp, sp=(tsp, sp_xyz[:, :2]),
                   hold_win=[win["hold"]["t"], win["hold"]["t"] + win["hold"]["dur_s"]])
    return r, win


dec = lambda t_ev, tau, a=1.0: (lambda t: np.where(t >= t_ev, a * np.exp(-(t - t_ev) / tau), 0.0))   # noqa: E731


# ---- windows from run.json (g3_timeline) ---------------------------------------------------------------------------------------------
def test_windows_from_timeline_known_answers():
    w = G.windows_from_run_json(run_json(), 0.0)
    assert w["item5_events"] == pytest.approx([20.0, 32.0]) and w["step_starts"] == pytest.approx([20.0, 32.0])
    assert w["track"] == pytest.approx([43.0, 61.0]) and w["main"]["t"] == pytest.approx(43.0) and w["main"]["dur_s"] == pytest.approx(18.0)
    assert w["item3"] == pytest.approx([86.0, 96.0]) and w["timeline"]["sag_ramp_end_s"] == pytest.approx(30.0)
    w = G.windows_from_run_json(run_json(), 12.5)                                       # ulog start_timestamp is subtracted
    assert w["item5_events"] == pytest.approx([7.5, 19.5]) and w["track"] == pytest.approx([30.5, 48.5])
    w = G.windows_from_run_json(run_json(wind=False), 0.0)                              # fault only: the t0 event, no gust
    assert w["item5_events"] == pytest.approx([20.0]) and w["step_starts"] == pytest.approx([20.0])
    w = G.windows_from_run_json(run_json(fault=False), 0.0)                             # wind only: the gust is the event; the ramp is not
    assert w["item5_events"] == pytest.approx([32.0]) and w["step_starts"] == pytest.approx([20.0, 32.0])
    w = G.windows_from_run_json(run_json(fault=False, wind=False), 0.0)
    assert w["item5_events"] == [] and w["step_starts"] == []
    assert G.windows_from_run_json(run_json(stick=True), 0.0)["track"] is None          # stick scenario: no item 4
    with pytest.raises(ValueError):                                                     # a Q33 run without the timeline is never scored on a guess
        G.windows_from_run_json(run_json(with_timeline=False), 0.0)


# ---- item 5: static reference per mode -------------------------------------------------------------------------------------------------
def test_item5_position_events_are_fault_start_and_gust():
    r, _ = make(pos_err=lambda t: dec(T0, 0.5)(t) + dec(GUST, 0.5)(t))
    it = r["item5_recovery"]
    assert it["pass"] and [e["t_event"] for e in it["events"]] == pytest.approx([T0, GUST]), it
    r, _ = make(pos_err=dec(GUST, 5.0))                  # the gust excursion needs 6 s to come back to 0.3 m: the gust event fails
    it = r["item5_recovery"]
    assert not it["pass"] and it["events"][0]["pass"] and not it["events"][1]["pass"] and it["events"][1]["t_recover_s"] > 5.0, it
    r, _ = make(pos_err=dec(T0, 5.0))                    # same for the fault start
    assert not r["item5_recovery"]["pass"] and not r["item5_recovery"]["events"][0]["pass"] and r["item5_recovery"]["events"][1]["pass"]
    r, _ = make(pos_err=lambda t: np.where((t >= GUST) & (t < MAIN0), 0.5, 0.0))     # stays 0.5 m off the hover setpoint to the main segment
    assert not r["item5_recovery"]["pass"] and not r["item5_recovery"]["events"][1]["pass"]


def test_item5_position_mode_scores_position_and_tilt():
    # GATES 3 item 5 keeps both terms (0.3 m and 3 deg); Q33 only changes the position reference to the hover setpoint
    r, _ = make(tilt=lambda t: np.where((t >= T0) & (t < T0 + 8.0), 6.0, 0.0))   # 6 deg tilt for 8 s, position stays on the hover point
    assert not r["item5_recovery"]["pass"] and r["item5_recovery"]["uses"] == {"position": True, "attitude": True}
    r, _ = make(tilt=lambda t: np.where((t >= T0) & (t < T0 + 2.0), 6.0, 0.0))   # back within 2 s
    assert r["item5_recovery"]["pass"]


def test_item5_attitude_mode_reference_is_qd_and_not_position():
    tilt_for = lambda t_ev, d: (lambda t: np.where((t >= t_ev) & (t < t_ev + d), 6.0, 0.0))
    r, _ = make(mode="attitude", tilt=tilt_for(GUST, 6.0))        # 6 deg off q_d (level) for 6 s: > 5 s
    it = r["item5_recovery"]
    assert not it["pass"] and it["events"][0]["pass"] and not it["events"][1]["pass"] and it["uses"] == {"position": False, "attitude": True}
    r, _ = make(mode="attitude", tilt=tilt_for(GUST, 3.0))        # back within 3 s
    assert r["item5_recovery"]["pass"], r["item5_recovery"]
    r, _ = make(mode="attitude", pos_err=lambda t: np.where(t >= T0, 1.0, 0.0))   # 1 m position error: no position reference in attitude mode
    assert r["item5_recovery"]["pass"] and r["item5_recovery"]["uses"]["position"] is False
    qd = lambda t: np.where(t >= T0, 5.0, 0.0)                    # q_d itself tilted 5 deg (not level): the vehicle follows q_d
    r, _ = make(mode="attitude", tilt=qd, qd_tilt=qd)
    assert r["item5_recovery"]["pass"], r["item5_recovery"]
    r, _ = make(mode="attitude", tilt=qd)                         # vehicle 5 deg off the (level) q_d, never back
    assert not r["item5_recovery"]["pass"]


def test_item5_rate_mode_not_applicable():
    r, _ = make(mode="attitude", rate_mode=True, tilt=lambda t: np.where(t >= T0, 8.0, 0.0), pos_err=lambda t: np.where(t >= T0, 2.0, 0.0))
    assert r["item5_recovery"]["applicable"] is False and r["item5_recovery"]["pass"], r["item5_recovery"]


# ---- item 2: the gust time is skipped like the fault start --------------------------------------------------------------------------------
def test_item2_sine_straddling_gust_is_not_flagged():
    r, _ = make(burst=(GUST - 1.5, GUST + 1.5, 8.0))              # 3 s burst around the gust instant
    p = r["item2_oscillation"]["p"]
    assert not p["sustained"] and r["item2_oscillation"]["pass"], p
    tab = [x for x in r["item2_skipped_windows"] if x["start_s"] <= GUST < x["end_s"]]
    assert len(tab) == 4 and all("step start" in x["reason"] for x in tab)
    assert r["item2_step_starts"] == pytest.approx([T0, GUST])


def test_item2_sine_persisting_after_gust_is_flagged_and_unrelated_burst_is_not_skipped():
    r, _ = make(burst=(GUST - 1.5, GUST + 10.0, 8.0))             # persists 10 s past the gust
    assert r["item2_oscillation"]["p"]["sustained"] and not r["item2_oscillation"]["pass"]
    r, _ = make(burst=(T0 + 5.0, T0 + 8.0, 8.0))                  # the same 3 s burst away from t0 and the gust: no window skipped, flagged
    assert r["item2_oscillation"]["p"]["sustained"]
    assert not any(x["start_s"] <= T0 + 6.5 < x["end_s"] for x in r["item2_skipped_windows"])


# ---- item 4: the main segment only -------------------------------------------------------------------------------------------------------
def test_item4_window_is_the_main_segment_only():
    r, win = make(pos_err=lambda t: np.where((t > T0) & (t < MAIN0 - 1.0), 3.0, 0.0))    # 3 m off in the event hover: not item 4
    assert r["item4_tracking"]["pass"] and r["item4_tracking"]["window_s"] == pytest.approx([MAIN0, HOLD0]), r["item4_tracking"]
    assert win["track"] == pytest.approx([43.0, 61.0])
    r, _ = make(pos_err=lambda t: np.where((t >= MAIN0 + 0.5) & (t < MAIN0 + 8.5), 1.0, 0.0))   # 1 m for 8 s inside it: RMS 0.67 m > 0.5 m
    assert not r["item4_tracking"]["pass"] and r["item4_tracking"]["horizontal_rms_m"]["value"] > 0.5
    r, _ = make(delay_s=0.3)                                      # limits unchanged: 0.3 s lag, RMS ~0.19 m passes
    assert r["item4_tracking"]["pass"]


# ---- runner side: scenario, timeline, run.json ---------------------------------------------------------------------------------------------
def test_event_hover_scenario_and_timeline():
    import disturbance as D
    assert S.G3_EVENT_HOVER_S == pytest.approx(D.WIND_RAMP_T + D.WIND_HOLD1_T + D.GUST_T + 10.0) == pytest.approx(23.0)
    for name, main in (("g3_lemniscate", "traj"), ("g3_stick_zsine", "stick")):
        assert [x[0] for x in S.SCENARIOS[name]["segments"]] == ["settle", "event", main, "hold"]
        tl = R.plan_timeline(name, {"motor_fault": {}, "wind": {}, "thrust_sag": {"scale": 0.9, "ramp_s": 30.0}})
        d = {n: x for n, x, _ in S.SCENARIOS[name]["segments"]}
        assert tl["event_t0_us"] == 3_000_000 and tl["gust_us"] == tl["event_t0_us"] + 12_000_000
        assert tl["event_end_us"] == tl["main_start_us"] == 26_000_000 and tl["hold_start_us"] == tl["main_end_us"]
        assert tl["main_end_us"] - tl["main_start_us"] == int(round(d[main] * 1e6)) and tl["hold_end_us"] - tl["hold_start_us"] == 35_000_000
        assert tl["sag_ramp_start_us"] == 0 and tl["sag_ramp_end_us"] == 30_000_000
        assert R.plan_timeline(name, {})["gust_us"] is None and R.plan_timeline(name, {})["sag_ramp_end_us"] is None
        assert R.ANCHOR_SEGMENT[name] == "event"


def test_run_timeline_from_run_json_and_finalize(tmp_path):
    base = 1_000_000_000          # PX4 clock offset: segment times are absolute
    segs, t = [], base + 2_000_000
    for n, dur, _ in S.SCENARIOS["g3_lemniscate"]["segments"]:
        segs.append({"name": n, "t_us": t, "dur_s": dur})
        t += int(round(dur * 1e6))
    rj = {"scenario": "g3_lemniscate", "events": segs, "motor_fault": {"event_us": segs[1]["t_us"]},
          "disturbance": {"onset_us": segs[1]["t_us"]}, "thrust_sag": {"t0_us": base, "dur_s": 31.5}, "exit_status": "ok"}
    tl = R.run_timeline(rj)
    assert tl["event_t0_us"] == base + 5_000_000 and tl["gust_us"] == base + 17_000_000 and tl["main_start_us"] == base + 28_000_000
    assert tl["sag_ramp_start_us"] == base and tl["sag_ramp_end_us"] == base + 31_500_000 and tl["fault_on"] and tl["wind_on"]
    assert R.run_timeline({**rj, "scenario": "o1_lemniscate"}) is None
    out = str(tmp_path)
    json.dump(rj, open(os.path.join(out, "run.json"), "w"))
    orig = R.check_validity
    R.check_validity = lambda o: None
    try:
        R.finalize(out, {"returncode": 0})
    finally:
        R.check_validity = orig
    assert json.load(open(os.path.join(out, "run.json")))["g3_timeline"] == tl
