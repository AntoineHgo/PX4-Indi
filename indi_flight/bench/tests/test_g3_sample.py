"""Self-test of bench/g3_sample.py. Run: python3 -m pytest -q bench/tests/test_g3_sample.py  or  python3 bench/tests/test_g3_sample.py"""
import hashlib
import json
import math
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import g3_sample as g  # noqa: E402

EPS = 1e-6
N = 300
_cache = {}


def camp(seed=11, n=N):
    if (seed, n) not in _cache:
        _cache[(seed, n)] = g.campaign(seed, n)
    return _cache[(seed, n)]


def lhs(seed=11):
    return [r for r in camp(seed) if r["kind"] == "lhs"]


def _tree_hash(d):
    h = hashlib.sha256()
    for name in sorted(os.listdir(d)):
        h.update(name.encode())
        h.update(open(os.path.join(d, name), "rb").read())
    return h.hexdigest()


def test_determinism_bytes():
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b, tempfile.TemporaryDirectory() as c:
        g.write(g.campaign(5, 300), a, 5, "campaign")
        g.write(g.campaign(5, 300), b, 5, "campaign")
        g.write(g.campaign(6, 300), c, 6, "campaign")
        assert _tree_hash(a) == _tree_hash(b)
        assert _tree_hash(a) != _tree_hash(c)
        assert len(os.listdir(a)) == 301


def test_counts_and_distinct_seeds():
    runs = camp()
    assert len(runs) == N
    assert sum(r["kind"] == "lhs" for r in runs) == 240
    for c in g.CORNERS:
        assert sum(r.get("corner") == c for r in runs) == 10
    assert len({r["sampler_seed"] for r in runs}) == N
    assert len({r["gz_seed"] for r in runs}) == N
    assert all(1 <= r["gz_seed"] <= 2**31 - 1 for r in runs)
    for n in (50, 100, 17):
        rr = g.campaign(3, n)
        assert len(rr) == n and sum(r["kind"] != "lhs" for r in rr) == round(0.2 * n)


def _in(x, lo, hi):
    return lo - EPS <= x <= hi + EPS


def test_ranges():
    for r in camp():
        f = r["factors"]
        for ax in ("roll", "pitch", "yaw"):
            assert _in(f["g1_err"][ax], 0.5, 2.0)
        assert _in(f["tau_scale"]["value"], 0.5, 3.0)
        a = f["tau_asym"]
        assert _in(a["value"], 1 / 3, 3.0)
        if not a["inverted"]:
            assert _in(a["value"], 1.0, 3.0)
        else:
            assert _in(a["value"], 1 / 3, 1.0)
        d = f["loop_delay"]
        assert _in(d["total_ms"], 0, 10) and abs(d["total_ms"] / 1.25 - round(d["total_ms"] / 1.25)) < 1e-9
        assert abs(d["act_ms"] - d["imu_ms"]) < EPS
        assert _in(f["mass_scale"]["value"], 0.7, 1.3)
        for k in ("ixx", "iyy", "izz"):
            assert _in(f["inertia_scale"][k], 0.7, 1.3)
        s = f["thrust_sag"]
        assert (_in(s["scale"], 0.7, 1.0) if s["on"] else s["scale"] == 1.0)
        sat = f["saturation"]
        if sat["on"]:      # documented widening: only draw that saturates
            assert r.get("corner") == "C3"
            assert abs(sat["scale"] - 0.27 * f["mass_scale"]["value"]) < EPS
        w = f["weak_motor"]
        assert (_in(w["scale"], 0.7, 1.0) and w["motor"] in range(4)) if w["on"] else w["scale"] == 1.0
        assert f["tel_latency"]["frames"] in (0, 1, 2, 3)
        assert _in(f["tel_dropout"]["prob"], 0, 0.2)
        assert _in(f["vibration"]["mult"], 1.0, 5.0)
        assert abs(f["vibration"]["acc_ms2"] - f["vibration"]["mult"]) < EPS
        assert abs(f["vibration"]["gyr_rads"] - 0.05 * f["vibration"]["mult"]) < EPS
        gn = f["gnss"]
        assert 80 <= gn["latency_ms"] <= 250 and gn["ekf_delay_ms"] >= 0
        assert abs(gn["ekf_delay_ms"] - gn["latency_ms"]) <= 100
        w = f["wind"]
        assert _in(w["steady_ms"], 0, 5) and _in(w["dir_deg"], 0, 360)
        assert _in(w["gust_peak_total_ms"], 3, 9) and _in(w["gust_amp_ms"], 0, 9) and abs(w["steady_ms"] + w["gust_amp_ms"] - w["gust_peak_total_ms"]) < 1e-5 or w["steady_ms"] > w["gust_peak_total_ms"] - EPS
        for k in ("tel_loss", "tel_frozen"):
            e = f[k]
            if e["on"]:
                assert _in(e["start_offset_s"], 1.0, 5.0) and e["motor"] in range(4)
        assert r["mode"] in ("position", "stabilized", "acro")


def test_lhs_stratification():
    rr = lhs()
    n = len(rr)
    def strata(vals, lo, hi, log=False):
        t = (lambda x: math.log(x / lo) / math.log(hi / lo)) if log else (lambda x: (x - lo) / (hi - lo))
        return sorted(min(n - 1, int(t(v) * n)) for v in vals)
    full = list(range(n))
    # values are rounded to 1e-6, strata are 1/240 wide: no boundary issue except exact endpoints (prob ~0)
    checks = [
        ([r["factors"]["g1_err"][a] for r in rr for a in ("roll",)], 0.5, 2.0, True),
        ([r["factors"]["g1_err"]["pitch"] for r in rr], 0.5, 2.0, True),
        ([r["factors"]["g1_err"]["yaw"] for r in rr], 0.5, 2.0, True),
        ([r["factors"]["tau_scale"]["value"] for r in rr], 0.5, 3.0, True),
        ([r["factors"]["mass_scale"]["value"] for r in rr], 0.7, 1.3, False),
        ([r["factors"]["inertia_scale"]["ixx"] for r in rr], 0.7, 1.3, False),
        ([r["factors"]["inertia_scale"]["iyy"] for r in rr], 0.7, 1.3, False),
        ([r["factors"]["inertia_scale"]["izz"] for r in rr], 0.7, 1.3, False),
        ([r["factors"]["vibration"]["mult"] for r in rr], 1.0, 5.0, True),
        ([r["factors"]["wind"]["steady_ms"] for r in rr], 0.0, 5.0, False),
        ([r["factors"]["wind"]["dir_deg"] for r in rr], 0.0, 360.0, False),
    ]
    for vals, lo, hi, log in checks:
        assert strata(vals, lo, hi, log) == full
    # discrete: delay steps (9) and telemetry latency (4) are balanced to +-2 counts per level
    for key, k, levels in (("loop_delay", "steps", 9), ("tel_latency", "frames", 4)):
        cnt = [sum(r["factors"][key][k] == i for r in rr) for i in range(levels)]
        assert max(cnt) - min(cnt) <= 2, (key, cnt)   # 240/9 = 26.7 per level


def _frac(rr, pred):
    return sum(1 for r in rr if pred(r)) / len(rr)


def test_conditional_fractions_n300():
    rr = lhs()
    tol = 0.02                                                     # stratified: normally exact to 1/240
    f = lambda r: r["factors"]
    assert abs(_frac(rr, lambda r: f(r)["thrust_sag"]["on"]) - 0.40) <= tol
    assert abs(_frac(rr, lambda r: f(r)["weak_motor"]["on"]) - 0.30) <= tol
    assert abs(_frac(rr, lambda r: f(r)["tel_dropout"]["on"]) - 0.40) <= tol
    assert abs(_frac(rr, lambda r: f(r)["tel_loss"]["on"]) - 0.20) <= tol
    assert abs(_frac(rr, lambda r: f(r)["tel_frozen"]["on"]) - 0.20) <= tol
    assert abs(_frac(rr, lambda r: f(r)["tau_asym"]["inverted"]) - 0.10) <= tol
    assert abs(_frac(rr, lambda r: f(r)["gnss"]["matched"]) - 0.50) <= tol
    assert abs(_frac(rr, lambda r: r["mode"] == "position") - 0.70) <= tol
    assert abs(_frac(rr, lambda r: r["mode"] == "stabilized") - 0.20) <= tol
    assert abs(_frac(rr, lambda r: r["mode"] == "acro") - 0.10) <= tol
    assert not any(f(r)["saturation"]["on"] for r in rr)           # LHS never saturates
    allr = camp()
    assert abs(_frac(allr, lambda r: r["mode"] == "acro") - 0.10) <= 0.04


def test_corner_pins_exact():
    by = {}
    for r in camp():
        if "corner" in r:
            by.setdefault(r["corner"], []).append(r["factors"])
    for c, fs in by.items():
        assert len(fs) == 10
        for f in fs:
            if c == "C1":
                assert all(f["g1_err"][a] == 2.0 for a in ("roll", "pitch", "yaw"))
                assert f["tau_scale"]["value"] == 3.0 and f["loop_delay"]["total_ms"] == 10.0
            if c == "C2":
                assert all(f["g1_err"][a] == 0.5 for a in ("roll", "pitch", "yaw"))
                assert f["mass_scale"]["value"] == 1.3 and f["thrust_sag"]["on"] and f["thrust_sag"]["scale"] == 0.7
                assert all(f["inertia_scale"][k] == 1.3 for k in ("ixx", "iyy", "izz"))
            if c == "C3":
                assert f["saturation"]["on"] and f["wind"]["gust_peak_total_ms"] == 9.0 and f["mass_scale"]["value"] == 1.3
                assert abs(f["saturation"]["scale"] - 0.27 * 1.3) < EPS and not f["thrust_sag"]["on"]
            if c == "C4":
                g_ = f["gnss"]
                assert g_["latency_ms"] == 250 and not g_["matched"] and g_["ekf_delay_ms"] == 150
                assert f["wind"]["steady_ms"] == 5.0 and all(f["g1_err"][a] == 2.0 for a in ("roll", "pitch", "yaw"))
            if c == "C5":
                assert f["vibration"]["mult"] == 5.0 and f["tel_frozen"]["on"] and f["tel_dropout"]["on"]
                assert f["tel_dropout"]["prob"] == 0.2 and f["tau_scale"]["value"] == 0.5
            if c == "C6":
                assert f["weak_motor"]["on"] and f["weak_motor"]["scale"] == 0.7
                assert f["tau_scale"]["value"] == 3.0 and f["loop_delay"]["total_ms"] == 10.0
    # the rest is drawn: the unpinned G1 axis in C1..: tau in C2 takes many values
    assert len({f["tau_scale"]["value"] for f in by["C2"]}) > 5


def test_matched_gnss_delay_equals_latency():
    n_m = 0
    for r in camp():
        g_ = r["factors"]["gnss"]
        if g_["matched"]:
            n_m += 1
            assert g_["ekf_delay_ms"] == g_["latency_ms"] and g_["mismatch_offset_ms"] == 0
            assert r["hooks"]["run_scenario_args"]["--gnss-delay"] == r["hooks"]["run_scenario_args"]["--gps-dly"]
        else:
            assert g_["ekf_delay_ms"] == max(0, g_["latency_ms"] + g_["mismatch_offset_ms"])
    assert n_m > 100


def test_pretest_set():
    rr = g.pretest(9)
    assert len(rr) == 20 and len({r["sampler_seed"] for r in rr}) == 20
    assert sum(r["kind"] == "pretest sampled" for r in rr) == 5
    ext = [r for r in rr if r["kind"].startswith("pretest x_")]
    assert len(ext) == 15
    x = {r["kind"].split()[1]: r["factors"] for r in ext}
    assert x["x_tau"]["tau_scale"]["value"] == 3.0 and x["x_tau"]["loop_delay"]["total_ms"] == 0.0
    assert x["x_saturation"]["saturation"]["on"] and x["x_vib"]["vibration"]["mult"] == 5.0
    assert x["x_gnss"]["gnss"]["latency_ms"] == 250 and x["x_gnss"]["gnss"]["ekf_delay_ms"] == 150
    assert x["x_wind"]["wind"]["gust_peak_total_ms"] == 9.0 and x["x_mass"]["wind"]["steady_ms"] == 0.0
    assert x["x_tel_frozen"]["tel_frozen"]["on"] and not x["x_tel_frozen"]["tel_loss"]["on"]
    assert x["x_asym"]["tau_asym"]["value"] == 3.0
    assert all(r["g4_typical_noise"]["profile"] is None for r in rr)


def test_json_roundtrip_and_keys():
    r = camp()[0]
    s = json.loads(json.dumps(r))
    for k in ("sampler_seed", "run_index", "kind", "gz_seed", "factors", "hooks", "mode", "timeline", "g4_typical_noise"):
        assert k in s


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("PASS", name)
            except Exception as e:  # noqa: BLE001
                fails += 1
                import traceback
                traceback.print_exc(limit=2)
                print("FAIL", name, repr(e)[:200])
    print("failures:", fails)
    sys.exit(1 if fails else 0)
