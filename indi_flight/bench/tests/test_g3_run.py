"""Self-test of bench/g3_run.py. Run: python3 -m pytest -q bench/tests/test_g3_run.py  or  python3 bench/tests/test_g3_run.py"""
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
