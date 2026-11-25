"""Self-test of key 1 (bench/g3_checks.py) for the S214 / S225 G3 text: item 3 window from run.json, items 4, 5, 6, and the
item-2 fault / gust window skip. Synthetic truth with known answers; python3 -m pytest indi_flight/bench/tests/test_g3_checks_s226.py

Break-check (S226): G3_BREAK=skip|item3|item4|item5|item6 blinds one rule in an autouse fixture (module patched); the matching test
must then FAIL and the others stay green, e.g.  G3_BREAK=skip python3 -m pytest .../test_g3_checks_s226.py -q
"""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g3_checks as G  # noqa: E402

FS, T = 800.0, 70.0
T_FAULT, MAIN_DUR, T_HOLD, HOLD_DUR = 20.0, 18.0, 38.0, 25.0     # hold 38..63: item 3 = 53..63, item 6 = 43..63
BREAK = os.environ.get("G3_BREAK", "")


@pytest.fixture(autouse=True)
def _break(monkeypatch):
    if BREAK == "skip":
        orig = G.line_detector
        monkeypatch.setattr(G, "line_detector", lambda *a, **k: orig(*a, **{**k, "skip_points": ()}))
    elif BREAK == "item3":
        monkeypatch.setattr(G, "ITEM3_LAST_S", 25.0)           # window = the whole hold, transient included
    elif BREAK == "item4":
        monkeypatch.setattr(G, "TRACK_H_RMS_M", 1e9)
        monkeypatch.setattr(G, "TRACK_V_RMS_M", 1e9)
    elif BREAK == "item5":
        monkeypatch.setattr(G, "item5_recovery", lambda *a, **k: {"applicable": True, "pass": True, "events": []})
    elif BREAK == "item6":
        monkeypatch.setattr(G, "RATE_HOLD_RMS_DPS", 1e9)


def run_json(fault=True, gust=False, stick=False, erpm_loss=False, hold_dur=HOLD_DUR):
    ev = [{"name": "settle", "t_us": int(17e6), "dur_s": 3.0},
          {"name": "stick" if stick else "traj", "t_us": int(T_FAULT * 1e6), "dur_s": MAIN_DUR},
          {"name": "hold", "t_us": int(T_HOLD * 1e6), "dur_s": hold_dur}]
    rj = {"events": ev}
    if fault:
        rj["motor_fault"] = {"motor": 0, "thrust_scale": 0.7, "event_us": int(T_FAULT * 1e6)}
    if gust:
        rj["disturbance"] = {"profile": "gust_x", "onset_us": int(T_FAULT * 1e6)}
    if erpm_loss:
        rj["erpm_loss"] = {"motor": 1, "start": "traj", "start_offset_s": 3.0, "duration_s": 2.0}
    return rj


def make(rj=None, pos_err=None, alt_err=None, delay_s=0.0, tilt=None, rate_amp=None, rate_win=None, burst=None, mode="position",
         rate_mode=False, seed=0):
    """Truth that follows the setpoint x = 3 sin(0.3 (t - T_FAULT)) in the main segment (0 elsewhere), z at 5 m.
    pos_err(t) -> extra x error [m]; alt_err(t) -> extra height error [m]; delay_s: truth lags the path; tilt(t) -> tilt [deg] about x;
    rate_amp (deg/s RMS, 1 Hz sine on p) over rate_win; burst = (t_a, t_b, deg/s RMS) 30 Hz sine on p."""
    rng = np.random.default_rng(seed)
    rj = rj or run_json()
    win = G.windows_from_run_json(rj, 0.0)
    t = np.arange(0, T, 1 / FS)
    n = len(t)

    def path(tq):
        u = tq - T_FAULT
        return np.where((u > 0) & (u < MAIN_DUR), 3.0 * np.sin(0.3 * u), 0.0)

    h = np.clip(t - 1.0, 0.0, 5.0)
    x = path(t - delay_s) + (pos_err(t) if pos_err else 0.0)
    pos = np.stack([x, np.zeros(n), -(h + (alt_err(t) if alt_err else 0.0))], axis=1)
    pos[:, 2][t < 0.5] = 0.0
    th = np.radians(tilt(t)) if tilt else np.zeros(n)
    q = np.stack([np.cos(th / 2), np.sin(th / 2), np.zeros(n), np.zeros(n)], axis=1)
    w = np.radians(1.0) * rng.normal(size=(n, 3))
    if rate_amp:
        m = (t >= rate_win[0]) & (t < rate_win[1])
        w[:, 0] += np.radians(rate_amp) * np.sqrt(2) * np.sin(2 * np.pi * 1.0 * t) * m
    if burst:
        m = (t >= burst[0]) & (t < burst[1])
        w[:, 0] += np.radians(burst[2]) * np.sqrt(2) * np.sin(2 * np.pi * 30.0 * t) * m
    cmd = 0.5 + 0.002 * rng.normal(size=(n, 4))
    tsp = np.arange(0, T, 0.01)
    sp_xyz = np.stack([path(tsp), np.zeros(len(tsp)), np.full(len(tsp), -5.0)], axis=1)
    att_sp = (tsp, np.tile([1.0, 0.0, 0.0, 0.0], (len(tsp), 1)))
    t0, t1 = win["item3"]
    r = G.evaluate(t, pos, q, w, t, cmd, np.array([0.0, 0.0, -5.0]), t0, t1, mode=mode, step_starts=win["step_starts"],
                   track_win=win["track"], event_times=win["step_starts"], rate_mode=rate_mode, item6_win=win["item6"],
                   sp_xyz=(tsp, sp_xyz), att_sp=att_sp, sp=(tsp, sp_xyz[:, :2]))
    return r, win


# ---- windows from run.json --------------------------------------------------------------------------------------------------------
def test_windows_from_run_json_known_answers():
    w = G.windows_from_run_json(run_json(), 0.0)
    assert w["item3"] == pytest.approx([53.0, 63.0]) and w["item6"] == pytest.approx([43.0, 63.0])
    assert w["track"] == pytest.approx([20.0, 38.0]) and w["step_starts"] == [pytest.approx(20.0)]
    assert w["hold"]["dur_s"] == HOLD_DUR and w["main"]["name"] == "traj"
    w = G.windows_from_run_json(run_json(), 12.5)                      # ulog start_timestamp is subtracted
    assert w["item3"] == pytest.approx([40.5, 50.5]) and w["step_starts"] == [pytest.approx(7.5)]
    assert G.windows_from_run_json(run_json(stick=True), 0.0)["track"] is None          # stick scenario: no item 4
    assert G.windows_from_run_json(run_json(fault=False, gust=True), 0.0)["step_starts"] == [pytest.approx(20.0)]
    assert G.windows_from_run_json(run_json(fault=False), 0.0)["step_starts"] == []     # no fault, no gust: nothing to skip
    assert G.windows_from_run_json(run_json(hold_dur=3.0), 0.0)["item3"] is None        # old 3 s hold: no S214 window


# ---- item 3 on the S214 window ----------------------------------------------------------------------------------------------------
def test_item3_uses_last_10s_of_hold():
    off_early = lambda t: np.where((t >= T_HOLD) & (t < 52.0), 0.5, 0.0)    # transient early in the hold, gone before 53 s
    r, _ = make(alt_err=off_early)
    assert r["window_s"] == pytest.approx([53.0, 63.0])
    assert r["item3_steady_state"]["pass"], r["item3_steady_state"]
    off_late = lambda t: np.where((t >= 55.0) & (t < 63.0), 0.5, 0.0)      # inside the window: altitude mean error ~0.4 m
    r, _ = make(alt_err=off_late)
    assert not r["item3_steady_state"]["pass"]


# ---- item 4 ------------------------------------------------------------------------------------------------------------------------
def test_item4_tracking():
    r, _ = make(delay_s=0.3)                                             # RMS ~ 3 * 0.3 * 0.3 / sqrt 2 = 0.19 m
    assert r["item4_tracking"]["pass"], r["item4_tracking"]
    r, _ = make(delay_s=1.5)                                             # RMS ~ 0.95 m > 0.5 m
    assert not r["item4_tracking"]["pass"] and r["item4_tracking"]["horizontal_rms_m"]["value"] > 0.5
    r, _ = make(alt_err=lambda t: np.where((t > T_FAULT) & (t < T_HOLD), 0.4, 0.0))      # vertical RMS 0.4 m > 0.3 m
    assert not r["item4_tracking"]["pass"] and r["item4_tracking"]["vertical_rms_m"]["value"] > 0.3


# ---- item 5 ------------------------------------------------------------------------------------------------------------------------
def test_item5_recovery():
    dec = lambda tau, a=1.0: (lambda t: np.where(t >= T_FAULT, a * np.exp(-(t - T_FAULT) / tau), 0.0))
    r, _ = make(pos_err=dec(0.5))                                          # 0.3 m after 0.6 s, then quiet
    assert r["item5_recovery"]["pass"], r["item5_recovery"]
    assert r["item5_recovery"]["events"][0]["t_recover_s"] < 1.5
    r, _ = make(pos_err=dec(5.0))                                          # reaches 0.3 m after 6 s > 5 s
    assert not r["item5_recovery"]["pass"] and r["item5_recovery"]["events"][0]["t_recover_s"] > 5.0
    bump = lambda t: dec(0.5)(t) + np.where((t > T_FAULT + 4.0) & (t < T_FAULT + 4.5), 0.5, 0.0)   # re-excursion 3.4 s after recovery
    r, _ = make(pos_err=bump)
    assert not r["item5_recovery"]["pass"]
    tilt6 = lambda t: np.where((t >= T_FAULT) & (t < T_FAULT + 6.0), 6.0, 0.0)                   # 6 deg tilt for 6 s: not within 3 deg in 5 s
    r, _ = make(tilt=tilt6, mode="attitude")                               # Q33: tilt vs q_d only in attitude mode
    assert not r["item5_recovery"]["pass"] and r["item5_recovery"]["uses"]["attitude"]
    r, _ = make(tilt=tilt6)                                                # position mode keeps the 3 deg tilt term
    assert not r["item5_recovery"]["pass"] and r["item5_recovery"]["uses"]["attitude"]
    r, _ = make(rj=run_json(fault=False))                                  # no fault or gust: no event, not applicable
    assert r["item5_recovery"]["applicable"] is False and r["item5_recovery"]["pass"]


# ---- item 6 ------------------------------------------------------------------------------------------------------------------------
def test_item6_rate_hold_last_20s():
    r, _ = make(mode="attitude", rate_mode=True)
    assert r["item6_rate_hold"]["pass"], r["item6_rate_hold"]
    r, _ = make(mode="attitude", rate_mode=True, rate_amp=8.0, rate_win=(43.0, 63.0))      # 8 deg/s RMS inside the last 20 s
    assert not r["item6_rate_hold"]["pass"] and r["item6_rate_hold"]["rms_dps"]["p"] > 5.0
    r, _ = make(mode="attitude", rate_mode=True, rate_amp=8.0, rate_win=(38.0, 42.9))      # before the last 20 s: not scored
    assert r["item6_rate_hold"]["pass"], r["item6_rate_hold"]
    r, _ = make(mode="attitude", rate_mode=False)                          # not a rate-mode run
    assert r["item6_rate_hold"]["applicable"] is False


# ---- item 2: fault / gust windows --------------------------------------------------------------------------------------------------
def test_item2_sine_straddling_fault_is_not_flagged():
    r, _ = make(burst=(T_FAULT - 1.5, T_FAULT + 1.5, 8.0))                 # 3 s burst around the fault instant
    p = r["item2_oscillation"]["p"]
    assert not p["sustained"] and r["item2_oscillation"]["pass"], p
    assert p["skipped_windows"] == 4 and len(r["item2_skipped_windows"]) == 4


def test_item2_sine_persisting_after_fault_is_flagged():
    r, _ = make(burst=(T_FAULT - 1.5, T_FAULT + 10.0, 8.0))                # persists 10 s past the fault
    assert r["item2_oscillation"]["p"]["sustained"] and not r["item2_oscillation"]["pass"] and not r["pass"]


def test_item2_skipped_window_table_and_no_chaining():
    r, _ = make(burst=(T_FAULT - 2.5, T_FAULT + 2.5, 8.0))                 # 5 s sine centred on the fault: windows flagged on both sides of the skip
    tab = r["item2_skipped_windows"]
    assert len(tab) == 4 and all(x["start_s"] <= T_FAULT < x["end_s"] and "step start" in x["reason"] for x in tab)
    assert all(abs((x["end_s"] - x["start_s"]) - 4.0) < 1e-6 for x in tab) and r["item2_step_starts"] == [pytest.approx(T_FAULT)]
    # without the skip these windows chain into one sustained line (checked by the G3_BREAK=skip run); with it, no line chains across it
    assert not r["item2_oscillation"]["p"]["sustained"] and 0 < r["item2_oscillation"]["p"]["flagged_windows"] < G.MIN_WINDOWS + 1


def test_item2_telemetry_loss_start_is_not_skipped():
    rj = run_json(fault=False, erpm_loss=True)
    r, win = make(rj=rj, burst=(T_FAULT - 1.5, T_FAULT + 1.5, 8.0))
    assert win["step_starts"] == [] and r["item2_skipped_windows"] == []
    assert r["item2_oscillation"]["p"]["sustained"] and not r["item2_oscillation"]["pass"]


def test_gust_step_also_skips():
    r, _ = make(rj=run_json(fault=False, gust=True), burst=(T_FAULT - 1.5, T_FAULT + 1.5, 8.0))
    assert r["item2_oscillation"]["pass"] and len(r["item2_skipped_windows"]) == 4
