"""Self-test of bench/g3_run.py. Run: python3 -m pytest -q bench/tests/test_g3_run.py  or  python3 bench/tests/test_g3_run.py"""
import copy
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import g3_run as r  # noqa: E402
import g3_sample as g  # noqa: E402

BASE = os.path.join(HERE, "..", "params", "quad5in_indi_g1.params")
OUT = "/tmp/g3_test_out"
_cache = {}


def draws(seed=21, n=200):
    if (seed, n) not in _cache:
        _cache[(seed, n)] = g.campaign(seed, n) + g.pretest(seed)
    return _cache[(seed, n)]


def _status_dir(rj):
    import json
    import tempfile
    d = tempfile.mkdtemp(prefix="g3fin_")
    if rj is not None:
        json.dump(rj, open(os.path.join(d, "run.json"), "w"))
    return d


def test_aborted_run_gets_done_marker_and_outcome():
    import json
    d = _status_dir({"exit_status": "failed", "error": "WatchdogTrip: height", "watchdog": {"h": 0.2},
                     "metrics_status": "ok"})
    assert r.finalize(d, {"returncode": 1}) == "aborted"
    done = json.load(open(os.path.join(d, "g3_done.json")))
    assert done["outcome"] == "aborted" and done["returncode"] == 1 and "WatchdogTrip" in done["error"]
    assert not os.path.exists(os.path.join(d, "g3_failed.json"))
    assert json.load(open(os.path.join(d, "run.json")))["g3_outcome"] == "aborted"


def test_ok_and_incomplete_outcomes():
    import json
    d = _status_dir({"exit_status": "ok"})
    assert r.finalize(d, {"returncode": 0}) == "ok" and os.path.exists(os.path.join(d, "g3_done.json"))
    d = _status_dir(None)    # timeout / runner died: no verdict, retried
    assert r.finalize(d, {"returncode": None, "timeout_s": 1.0}) == "incomplete"
    assert os.path.exists(os.path.join(d, "g3_failed.json")) and not os.path.exists(os.path.join(d, "g3_done.json"))
    assert json.load(open(os.path.join(d, "g3_failed.json")))["outcome"] == "incomplete"
    d = _status_dir({"exit_status": "failed", "error": "crash"})   # K113 MINOR 5: rc 0 but run.json says failed
    assert r.finalize(d, {"returncode": 0}) == "aborted"


def argval(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


def parse_variant(s):
    """Same rule as run_scenario.py: KEY=positive finite float."""
    out = {}
    for kv in s.split(","):
        k, sep, v = kv.partition("=")
        x = float(v)
        assert sep and math.isfinite(x) and x > 0.0
        out[k.strip()] = x
    return out


def test_every_factor_accounted():
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        expected = set(d["factors"]) | {"mode", "g4_typical_noise"}
        assert set(b["applied"]) | set(b["not_applied"]) == expected, d["run_index"]
        assert not set(b["applied"]) & set(b["not_applied"])
        assert all(isinstance(v, str) and v for v in b["not_applied"].values())


def test_missing_hooks_reported():
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        assert "g4_typical_noise" in b["applied"]
        if d["factors"]["tel_frozen"]["on"]:
            assert "tel_frozen" in b["applied"] and "tel_frozen" not in b["not_applied"]


def test_typical_profile_in_argv():
    for d in draws()[:20]:
        b = r.build_run(d, BASE, OUT)
        a = b["argv"]
        assert float(a[a.index("--imu-noise-scale") + 1]) == 4.0
        vb = d["factors"]["vibration"]
        assert abs(float(a[a.index("--vib-acc") + 1]) - (10.0 + vb["acc_ms2"])) < 1e-3


def test_no_factor_left_unapplied():
    """S185: every drawn factor has a hook (tel_frozen included), so the abort-before-flying list is empty."""
    assert r.unapplied(draws(), BASE) == {}


def test_erpm_frozen_drawn_motor_and_window():
    """tel_frozen -> erpm_frozen override (timed, main segment anchor), mirrors tel_loss; loss and frozen are independent."""
    n = 0
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        tf = d["factors"]["tel_frozen"]
        if not tf["on"]:
            assert "erpm_frozen" not in b["overrides"]
            continue
        e = b["overrides"]["erpm_frozen"]
        assert e["motor"] == tf["motor"] and e["start_offset_s"] == tf["start_offset_s"] and e["duration_s"] == tf["duration_s"]
        assert e["start"] == r.MAIN_SEGMENT[b["applied"]["mode"]["scenario"]]
        n += 1
    assert n > 5


def test_model_variant_mapping():
    seen_on = seen_off = 0
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        mv = d["hooks"]["model_variant"]
        nominal = all(abs(v - 1.0) < 1e-9 for v in mv.values())
        if nominal:
            assert "--model-variant" not in b["argv"]
            seen_off += 1
            continue
        seen_on += 1
        got = parse_variant(argval(b["argv"], "--model-variant"))
        want = {k: v for k, v in mv.items() if abs(v - 1.0) >= 1e-9}
        assert set(got) == set(want)
        for k in want:
            assert got[k] == want[k], (k, got[k], want[k])
    assert seen_on > 100


def test_params_override_base():
    base = r.read_params(BASE)
    for d in draws()[:60]:
        b = r.build_run(d, BASE, OUT)
        m = b["merged_params"]
        for k, v in b["params"].items():
            assert m[k] == v
        for ax, name in r.G1_PARAMS:
            assert abs(m[name] - base[name] * d["factors"]["g1_ctrl_mult"][ax]) < 1e-5 * base[name]
        assert m["SIM_GZ_ERPM_LAT"] == d["factors"]["tel_latency"]["frames"]
        for k in base:
            if k not in b["params"]:
                assert m[k] == base[k]


def test_argv_flags():
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        a = b["argv"]
        assert argval(a, "--sim") == "v2" and argval(a, "--model") == "quad5in"
        assert abs(float(argval(a, "--vib-acc")) - (10.0 + d["factors"]["vibration"]["acc_ms2"])) < 1e-6
        assert int(argval(a, "--gps-dly")) == d["factors"]["gnss"]["latency_ms"]
        ekf = d["factors"]["gnss"]["ekf_delay_ms"]
        assert (argval(a, "--gnss-delay") is None) == (ekf is None)
        assert (argval(a, "--stick-mode") is None) == (d["mode"] == "position")
        assert 0 <= int(argval(a, "--dly-act") or 0) <= 10


def test_overrides_applied_and_valid():
    import json
    import scenario_overrides as so
    from scenarios import SCENARIOS
    seen = {"thrust_sag": 0, "motor_fault": 0, "erpm_loss": 0, "wind": 0}
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        f, ov = d["factors"], b["overrides"]
        assert ("--scenario-overrides" in b["argv"]) == bool(ov)
        sc = SCENARIOS[b["applied"]["mode"]["scenario"]]
        so.merge(sc, ov)                                  # valid against the real scenario (segments exist)
        json.dumps(ov)
        for k in seen:
            seen[k] += k in ov
        assert ("thrust_sag" in ov) == f["thrust_sag"]["on"] and ("erpm_loss" in ov) == f["tel_loss"]["on"]
        if f["thrust_sag"]["on"]:
            assert ov["thrust_sag"]["scale"] == f["thrust_sag"]["scale"] and "thrust_sag" in b["applied"] and "thrust_sag" not in b["not_applied"]
        mf = ov.get("motor_fault")
        mf = [] if mf is None else (mf if isinstance(mf, list) else [mf])
        assert len(mf) == f["saturation"]["on"] + f["weak_motor"]["on"]
        if f["saturation"]["on"]:
            e = [x for x in mf if "motors" in x][0]
            assert e["motors"] == [0, 1, 2, 3] and e["thrust_scale"] == f["saturation"]["scale"]
        if f["weak_motor"]["on"]:
            e = [x for x in mf if "motor" in x][0]
            assert e["motor"] == f["weak_motor"]["motor"] and e["thrust_scale"] == f["weak_motor"]["scale"]
            assert "weak_motor" in b["applied"] and "weak_motor" not in b["not_applied"]
        w = f["wind"]
        if w["steady_ms"] or w["gust_amp_ms"]:
            assert ov["wind"] == {"steady": w["steady_ms"], "peak": w["gust_peak_total_ms"], "dir_deg": w["dir_deg"]}
            assert "wind" in b["applied"] and "wind" not in b["not_applied"]
        else:
            assert "wind" not in ov
        assert b["not_applied"].keys() <= {"g4_typical_noise"}
    assert all(v > 5 for v in seen.values()), seen


def test_erpm_loss_drawn_motor_and_window():
    """M-2 / mutation (b): the override carries the drawn motor index, start offset and duration, anchored at the main segment."""
    n = 0
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        tl = d["factors"]["tel_loss"]
        if not tl["on"]:
            assert "erpm_loss" not in b["overrides"]
            continue
        e = b["overrides"]["erpm_loss"]
        assert e["motor"] == tl["motor"] and e["start_offset_s"] == tl["start_offset_s"] and e["duration_s"] == tl["duration_s"]
        assert e["start"] == r.MAIN_SEGMENT[b["applied"]["mode"]["scenario"]] and "end" not in e
        n += 1
    assert n > 5


def test_weak_motor_segment_and_motor():
    """Mutation (c): weak-motor step is at the main segment, on the drawn motor; saturation + weak motor both applied."""
    n = both = 0
    for d in draws():
        b = r.build_run(d, BASE, OUT)
        f = d["factors"]
        if not f["weak_motor"]["on"]:
            continue
        mf = b["overrides"]["motor_fault"]
        mf = mf if isinstance(mf, list) else [mf]
        e = [x for x in mf if "motor" in x][0]
        assert e["segment"] == r.MAIN_SEGMENT[b["applied"]["mode"]["scenario"]] and e["segment"] != r.END_SEGMENT
        n += 1
        both += f["saturation"]["on"]
    assert n > 5
    if not both:  # the sampler never drew both: build one by hand
        d = copy.deepcopy([x for x in draws() if x["factors"]["weak_motor"]["on"]][0])
        d["factors"]["saturation"].update(on=True, scale=0.9)
        mf = r.build_run(d, BASE, OUT)["overrides"]["motor_fault"]
        assert isinstance(mf, list) and len(mf) == 2


def test_determinism():
    a = [r.build_run(d, BASE, OUT)["argv"] for d in g.campaign(21, 50)]
    b = [r.build_run(d, BASE, OUT)["argv"] for d in g.campaign(21, 50)]
    c = [r.build_run(d, BASE, OUT)["argv"] for d in g.campaign(22, 50)]
    assert a == b and a != c


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except AssertionError as e:
                fails += 1
                print("FAIL", name, repr(e)[:200])
    sys.exit(1 if fails else 0)


def test_indi_params_carry_rate_ctl_type_1():
    """S121 TODO: the runner must request MC_RATE_CTL_TYPE 1 for controller indi (else the stock PID loop flies)."""
    d = draws()[0]
    res = r.build_run(d, BASE, OUT)
    assert r.CONTROLLER == "indi"
    assert int(res["merged_params"]["MC_RATE_CTL_TYPE"]) == 1
    assert "--controller" in res["argv"] and res["argv"][res["argv"].index("--controller") + 1] == "indi"


def test_invalid_run_is_void(monkeypatch=None):
    import json
    d = _status_dir({"exit_status": "ok"})
    orig = r.check_validity
    r.check_validity = lambda out: {"valid": False, "problems": ["x"], "checked": {}}
    try:
        status = {"returncode": 0}
        assert r.finalize(d, status) == "void"
    finally:
        r.check_validity = orig
    done = json.load(open(os.path.join(d, "g3_done.json")))
    assert done["outcome"] == "void" and done["returncode"] == 0 and done["validity"]["valid"] is False


def test_missing_params_file_is_void():  # K122 #2
    import json
    d = _status_dir({"exit_status": "ok"})
    open(os.path.join(d, "flight.ulg"), "wb").close()
    assert r.finalize(d, {"returncode": 0}) == "void"
    done = json.load(open(os.path.join(d, "g3_done.json")))
    assert done["validity"]["valid"] is False and "g3_params.txt" in done["validity"]["problems"][0]


def test_check_validity_exception_is_void():  # K122 #3
    import json
    d = _status_dir({"exit_status": "ok"})
    orig = r.check_validity

    def boom(out):
        raise ValueError("boom")
    r.check_validity = boom
    try:
        assert r.finalize(d, {"returncode": 0}) == "void"
    finally:
        r.check_validity = orig
    done = json.load(open(os.path.join(d, "g3_done.json")))
    assert done["outcome"] == "void" and "boom" in done["validity"]["problems"][0]
