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
        assert b["not_applied"]["g4_typical_noise"] == "hook missing"
        if d["factors"]["tel_frozen"]["on"]:
            assert b["not_applied"]["tel_frozen"] == "hook missing"


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
        assert float(argval(a, "--vib-acc")) == d["factors"]["vibration"]["acc_ms2"]
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
        assert b["not_applied"].keys() <= {"tel_frozen", "g4_typical_noise"}
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
