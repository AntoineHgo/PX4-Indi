"""S226 self-tests of the second key (bench/g3_checks_key2.py): windows from run.json (items 3 and 6), items 4-6, and the S225
item-2 fault-window skip rule. Synthetic data with a known answer. Break-checks: KEY2_BREAK=skip|chain|item3|item4|item5|item6
disables one rule and the matching test must fail (see results/q30_tooling_s226/KEY2_README.md).
Run: python3 -m pytest indi_flight/bench/tests -k key2 -q"""
import os, sys
import numpy as np
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import g3_checks_key2 as K

FS = K.FS
TS = 40.0   # fault / gust step start for the item-2 tests


# ---------------------------------------------------------------- windows from run.json
def rj_pos(t_main=60.0, dur_main=30.0, t_hold=90.0, dur_hold=25.0):
    return {"events": [{"name": "settle", "t_us": int((t_main - 3) * 1e6), "dur_s": 3.0},
                       {"name": "traj", "t_us": int(t_main * 1e6), "dur_s": dur_main},
                       {"name": "hold", "t_us": int(t_hold * 1e6), "dur_s": dur_hold}]}


def rj_stick(mode, t_main=60.0, dur_main=30.0, t_hold=90.0, dur_hold=25.0):
    return {"events": [{"name": "settle", "t_us": int((t_main - 3) * 1e6), "dur_s": 3.0},
                       {"name": "stick", "t_us": int(t_main * 1e6), "dur_s": dur_main},
                       {"name": "hold", "t_us": int(t_hold * 1e6), "dur_s": dur_hold}], "stick": {"mode": mode}}


def test_key2_windows_from_run_position():
    w = K.windows_from_run(rj_pos())
    assert w["hold"] == [90.0, 115.0] and w["hold_dur_s"] == 25.0
    assert w["item3"] == [105.0, 115.0]          # last 10 s of the hold
    assert w["item6"] == [95.0, 115.0]           # last 20 s of the hold
    assert w["main"] == [60.0, 90.0] and w["step_t"] == [60.0] and w["mode"] == "position"


def test_key2_windows_from_run_stick_modes_and_extras():
    assert K.windows_from_run(rj_stick("acro"))["mode"] == "rate"
    assert K.windows_from_run(rj_stick("stabilized"))["mode"] == "attitude"
    rj = rj_stick("acro", t_main=70.0, t_hold=100.0, dur_hold=30.0)
    rj["events"].insert(2, {"name": "tel_loss", "t_us": 80_000_000, "dur_s": 2.0})   # not a step start
    w = K.windows_from_run(rj)
    assert w["step_t"] == [70.0] and w["item3"] == [120.0, 130.0] and w["item6"] == [110.0, 130.0]
    assert K.windows_from_run(rj_pos(), legacy_win=(1.0, 4.0))["item3"] == [1.0, 4.0]    # old CLI --t0/--t1
    with pytest.raises(ValueError):
        K.windows_from_run({"events": [{"name": "traj", "t_us": 1, "dur_s": 1.0}]})


# ---------------------------------------------------------------- item 2 (S225 skip rule)
T = np.arange(0, 80, 1 / FS)


def rates(burst, amp=20.0, step_t=(TS,), hz=30.0):
    rng = np.random.default_rng(3)
    w = np.radians(rng.normal(0, 0.5, (len(T), 3)))
    m = (T >= burst[0]) & (T < burst[1])
    w[m, 0] += np.radians(amp) * np.sin(2 * np.pi * hz * T[m])
    return K.osc_rates(T, w, (), step_t)["p"]


def test_key2_item2_sine_only_straddling_fault_not_flagged():
    assert rates((TS - 1, TS + 3), step_t=())["sustained"]            # control: the same sine IS flaggable without the rule
    r = rates((TS - 1, TS + 3))
    assert not r["sustained"]
    starts = [x["start_s"] for x in r["skipped_windows"]]
    assert starts == [TS - 3, TS - 2, TS - 1, TS]                      # every 4 s window with ta <= TS < ta + 4
    assert all("S225" in x["reason"] for x in r["skipped_windows"])
    assert all(x["end_s"] - x["start_s"] == 4.0 for x in r["skipped_windows"])


def test_key2_item2_sine_persisting_after_fault_flagged():
    r = rates((TS - 1, TS + 20))
    assert r["sustained"] and r["at"][0] > TS - 0.5                    # streak starts after the skipped block
    assert any(x["flagged_if_unskipped"] for x in r["skipped_windows"])


def test_key2_item2_no_line_chains_across_skipped_window():
    # burst [TS-3, TS+4): flagged windows ta = TS-5, TS-4 | skipped TS-3..TS | TS+1, TS+2: 2 + 2, never 3 in a row
    assert not rates((TS - 3, TS + 4))["sustained"]
    assert rates((TS - 3, TS + 4), step_t=())["sustained"]


def test_key2_item2_window_boundary_and_other_starts_not_skipped():
    r = rates((TS - 1, TS + 3), step_t=(TS + 30.0,))                   # a step start far outside the burst: nothing near it skipped
    assert r["sustained"] and [x["start_s"] for x in r["skipped_windows"]][:1] == [TS + 27.0]
    # window [TS-4, TS) does not contain TS (half-open on the last sample), window [TS, TS+4) does
    assert (TS - 4) not in [x["start_s"] for x in rates((TS - 1, TS + 3))["skipped_windows"]]


def test_key2_item2_nav_skip_still_works_with_reasons():
    rng = np.random.default_rng(2); w = np.radians(rng.normal(0, 0.5, (len(T), 3)))
    b = (T >= 40) & (T < 44); w[b, 0] += np.radians(30.0) * np.sin(2 * np.pi * 30 * T[b])
    r = K.osc_rates(T, w, [39.5], ())["p"]
    assert not r["sustained"] and r["skipped_windows"] and all("Q15" in x["reason"] for x in r["skipped_windows"])


# ---------------------------------------------------------------- items 3-6 through analyse()
def build(rj, mode, dur=120.0, dpos=None, drate=None, dtilt=None, **kw):
    """Hover at 5 m over the setpoint; dpos(t) -> (n,3) offsets (x, y, h), drate(t) -> (n,3) deg/s, dtilt(t) -> deg about x."""
    t = np.arange(0, dur, 1 / FS); n = len(t); rng = np.random.default_rng(0)
    h = np.where(t < 3, np.linspace(0, 5, n), 5.0) * 1.0; h = np.minimum(h, 5.0) + rng.normal(0, 0.002, n)
    pos = np.stack([rng.normal(0, 0.002, n), rng.normal(0, 0.002, n), -h], 1)
    if dpos is not None:
        o = dpos(t); pos[:, 0] += o[:, 0]; pos[:, 1] += o[:, 1]; h = h + o[:, 2]; pos[:, 2] = -h
    w = np.radians(rng.normal(0, 0.5, (n, 3)))
    if drate is not None: w += np.radians(drate(t))
    ang = np.zeros(n) if dtilt is None else np.radians(dtilt(t))
    q = np.stack([np.cos(ang / 2), np.sin(ang / 2), 0 * ang, 0 * ang], 1)
    ts_ = np.arange(0, dur, 0.02); rw = K.windows_from_run(rj)
    args = dict(t=t, q=q, w=w, pos=pos, h=h, motors_t=t, motors=0.14 + rng.normal(0, 0.003, (n, 4)), hold0=rw["hold"][0], hold1=rw["hold"][1],
                gc_t=[], mode=mode, sp_t=ts_, sp_xy=np.zeros((len(ts_), 2)), sp_z=np.full(len(ts_), -5.0), runwin=rw,
                position_mode=(mode == "position"), att_t=ts_, att_q=np.tile([1.0, 0, 0, 0], (len(ts_), 1)))
    args.update(kw)
    return K.analyse(**args)


def box(t, a, b, v):
    return np.where((t >= a) & (t < b), v, 0.0)


def test_key2_item3_window_is_last_10s_of_hold():
    off = lambda a, b: (lambda t: np.stack([box(t, a, b, 0.5), 0 * t, 0 * t], 1))   # 0.5 m horizontal offset in [a, b)
    last = build(rj_pos(), "position", dpos=off(105.0, 115.0))["item3_steady_state"]
    before = build(rj_pos(), "position", dpos=off(95.0, 105.0))["item3_steady_state"]   # 10-20 s before the end: outside the window
    assert last["window_s"] == [105.0, 115.0] and not last["pass"] and abs(last["horiz_rms_m"] - 0.5) < 0.01
    assert before["pass"] and before["horiz_rms_m"] < 0.01


def test_key2_item4_tracking_rms_limits():
    # offset from te+10.5 s to the end of the traj window (60..90): rms = off * sqrt(19.5 / 30)
    f = np.sqrt(19.5 / 30)
    def run(dx=0.0, dz=0.0):
        return build(rj_pos(), "position", dpos=lambda t: np.stack([box(t, 70.5, 90, dx), 0 * t, box(t, 70.5, 90, dz)], 1))["item4_tracking"]
    a = run(dx=0.7); b = run(dx=0.6); c = run(dz=0.45); d = run(dz=0.35)
    assert abs(a["horiz_rms_m"] - 0.7 * f) < 0.01 and not a["pass"]       # 0.56 > 0.5
    assert b["pass"] and abs(b["horiz_rms_m"] - 0.6 * f) < 0.01           # 0.48 <= 0.5
    assert abs(c["vert_rms_m"] - 0.45 * f) < 0.01 and not c["pass"]       # 0.36 > 0.3
    assert d["pass"]                                                      # 0.28 <= 0.3
    assert a["window_s"] == [60.0, 90.0]


def test_key2_item4_not_applicable_outside_position_mode():
    r = build(rj_stick("stabilized"), "attitude")["item4_tracking"]
    assert r["applicable"] is False and r["pass"]


def test_key2_item5_recovery_position_mode():
    te = 60.0
    def run(a, b, dx):
        return build(rj_pos(), "position", dpos=lambda t: np.stack([box(t, a, b, dx), 0 * t, 0 * t], 1))
    ok = run(te, te + 3, 1.0)["item5_recovery"]                        # displaced 1 m for 3 s, back at te + 3 <= 5 s
    assert ok["pass"] and abs(ok["events"][0]["t_back_s"] - 3.0) < 0.01
    late = run(te, te + 6, 1.0)["item5_recovery"]                      # back after 6 s: too slow
    assert not late["pass"] and late["events"][0]["t_back_s"] > 5.0
    re_ = run(te + 3, te + 4, 0.5)["item5_recovery"]                   # within at te, excursion 0.5 m at te + 3 (< 5 s after return)
    assert not re_["pass"] and re_["events"][0]["re_excursion"]
    far = run(te + 7, te + 8, 0.5)["item5_recovery"]                   # excursion later than te + 5 s after the return: outside the 5 + 5 s scope
    assert far["pass"]
    clean = build(rj_pos(), "position")
    assert clean["item5_recovery"]["pass"] and clean["item5_recovery"]["events"][0]["t_back_s"] == 0.0


def test_key2_item5_attitude_part_and_modes():
    te = 60.0
    tilt = lambda a, b: (lambda t: box(t, a, b, 5.0))
    assert build(rj_pos(), "position", dtilt=tilt(te, te + 2))["item5_recovery"]["pass"]            # 5 deg off for 2 s, then back
    assert not build(rj_pos(), "position", dtilt=tilt(te, te + 6))["item5_recovery"]["pass"]        # 5 deg off for 6 s
    assert build(rj_stick("stabilized"), "attitude", dtilt=tilt(te, te + 2))["item5_recovery"]["pass"]   # vs pre-event attitude
    assert not build(rj_stick("stabilized"), "attitude", dtilt=tilt(te, te + 6))["item5_recovery"]["pass"]
    assert build(rj_stick("acro"), "rate", dtilt=tilt(te, te + 9))["item5_recovery"]["applicable"] is False
    # a reported-only (telemetry) event never gates
    r = build(rj_pos(), "position", dpos=lambda t: np.stack([box(t, 80.0, 95.0, 1.0), 0 * t, 0 * t], 1), tel_events=[("tel_loss", 80.0)])
    assert r["item5_recovery"]["pass"] and not r["item5_recovery"]["events"][1]["gated"] and not r["item5_recovery"]["events"][1]["pass"]


def test_key2_item6_rate_rms_last_20s_of_hold():
    rj = rj_stick("acro")                                              # hold 90..115, item 6 window 95..115
    burst = lambda a, b, v: (lambda t: np.stack([box(t, a, b, v), 0 * t, 0 * t], 1))
    inside = build(rj, "rate", drate=burst(95.0, 100.0, 12.0))["item6_rate_hold"]    # 12 dps for 5 of 20 s -> rms 6 dps
    outside = build(rj, "rate", drate=burst(90.0, 95.0, 12.0))["item6_rate_hold"]    # same burst just before the window
    small = build(rj, "rate", drate=burst(95.0, 100.0, 8.0))["item6_rate_hold"]      # 8 dps for 5 of 20 s -> rms 4 dps
    drift = build(rj, "rate", drate=burst(0.0, 120.0, 6.0))["item6_rate_hold"]       # constant 6 dps drift counts
    assert inside["window_s"] == [95.0, 115.0] and abs(inside["rate_rms_dps"] - 6.0) < 0.1 and not inside["pass"]
    assert outside["pass"] and small["pass"] and abs(small["rate_rms_dps"] - 4.0) < 0.1
    assert not drift["pass"]
    assert build(rj_pos(), "position", drate=burst(0.0, 120.0, 20.0))["item6_rate_hold"]["applicable"] is False


def test_key2_item6_short_hold_fails_closed():
    r = build(rj_stick("acro", dur_hold=15.0), "rate")["item6_rate_hold"]
    assert not r["pass"]


def test_key2_overall_pass_and_legacy():
    clean = build(rj_pos(), "position")
    assert clean["pass"] and clean["pass_items_1_3"]
    bad4 = build(rj_pos(), "position", dpos=lambda t: np.stack([box(t, 70.5, 90, 0.9), 0 * t, 0 * t], 1))
    assert not bad4["item4_tracking"]["pass"] and bad4["pass_items_1_3"] and not bad4["pass"]   # item 4 is in 'pass', not in the S225 line
    leg = build(rj_pos(), "position", dpos=lambda t: np.stack([box(t, 70.5, 90, 0.9), 0 * t, 0 * t], 1), legacy=True)
    assert leg["pass"]      # legacy re-scoring keeps pass = items 1-3
