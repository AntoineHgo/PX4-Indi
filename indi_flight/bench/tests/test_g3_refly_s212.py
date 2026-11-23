"""Self-test of the S212 G3 re-fly tooling: g3_sample.py refly, g3_run.py actc override, g3_chain.sh --samples / --halt-on-fail.

Run: python3 bench/tests/test_g3_refly_s212.py  (or pytest). No flight, no simulation, no docker: the chain test uses the
smoke hooks G3_CHAIN_TEST_FLIGHT_CMD / G3_CHAIN_TEST_SCORE_CMD and a fake `docker` on PATH, in a scratch directory under
indi_flight/results whose name contains "smoke" (removed at the end).
"""
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCH = os.path.join(HERE, "..")
sys.path.insert(0, BENCH)
import g3_run as r  # noqa: E402
import g3_sample as g  # noqa: E402

REPO = os.path.abspath(os.path.join(BENCH, "..", ".."))
RESULTS = os.path.join(REPO, "indi_flight", "results")
CHAIN = os.path.join(BENCH, "g3_chain.sh")
BASE = os.path.join(BENCH, "params", "quad5in_indi_defaults.params")
SEED, N = 173, 300
_cache = {}


def synthetic_scores(fail_lhs, abort_lhs=()):
    """SCORES.tsv text of the freeze-10 layout: key 1 / key 2 FAIL on fail_lhs, an aborted UNSCORED row on abort_lhs."""
    rows = ["idx\toutcome\tkey1\tkey2\tkey1_failing\tkey2_failing\tx"]
    for i in range(N):
        if i in abort_lhs:
            rows.append(f"{i:03d}\taborted (flight watchdog: height < 0.3 m)\tUNSCORED\tUNSCORED\t-\t-\t-")
        elif i in fail_lhs:
            rows.append(f"{i:03d}\tok\tFAIL\tpass\titem2\t-\tTrue")
        else:
            rows.append(f"{i:03d}\tok\tpass\tpass\t-\t-\tTrue")
    return "\n".join(rows) + "\n"


FAIL = {3, 10, 77, 100, 239, 245}   # 245 is a corner: its failure is not a block-1 LHS pick (corners are all in block 1)
ABORT = {39}
SCORES = synthetic_scores(FAIL, ABORT)


def refly():
    if "r" not in _cache:
        _cache["r"] = g.refly(SEED, N, SCORES)
    return _cache["r"]


def test_selection_and_order():
    runs = refly()
    assert len(runs) == N
    assert [d["run_index"] for d in runs] == list(range(N))
    assert sorted(d["source_run"] for d in runs) == list(range(N))        # a permutation, nothing lost or doubled
    blk = [d["block"] for d in runs]
    assert blk == [1] * 66 + [2] * (N - 66)       # 60 corners + 5 LHS fails + 1 abort
    assert [d["source_run"] for d in runs[:60]] == list(range(240, 300))   # corners C1-C6 first, source order
    assert all(d["kind"].startswith("corner") for d in runs[:60])
    assert [d["source_run"] for d in runs[60:66]] == [3, 10, 39, 77, 100, 239]   # critical LHS, ascending source index
    assert [d["source_run"] for d in runs[66:]] == [i for i in range(240) if i not in {3, 10, 39, 77, 100, 239}]
    assert all(d["kind"] == "lhs" for d in runs[60:])


def test_expect_block1_mismatch_stops():
    try:
        g.refly(SEED, N, SCORES, expect_block1=50)
    except SystemExit as e:
        assert "6 critical" in str(e)
    else:
        raise AssertionError("count mismatch must stop")
    g.refly(SEED, N, SCORES, expect_block1=6)


def test_draws_unchanged_except_new_fields():
    src = g.campaign(SEED, N)
    for d in refly():
        s = json.loads(json.dumps(src[d["source_run"]]))
        assert {"actc", "source_run", "block"} <= set(d)
        d = {k: v for k, v in d.items() if k not in ("actc", "source_run", "block")}
        d["run_index"] = s["run_index"]
        assert d == s     # factors, hooks, sampler_seed, gz_seed identical: same plant, same noise


def test_actc_value_and_range():
    for d in refly():
        a = d["actc"]
        f = d["factors"]
        tm = (f["tau_up"]["value"] + f["tau_down"]["value"]) / 2
        assert g.ACTC_R[0] <= a["actc_ratio"] <= g.ACTC_R[1] + 1e-6
        assert abs(a["mc_indi_act_tc"] - a["actc_ratio"] * tm * 0.033) < 3e-6
        assert g.ACTC_PARAM_RANGE[0] <= a["mc_indi_act_tc"] <= g.ACTC_PARAM_RANGE[1]


def test_r_independent_of_draw():
    runs = refly()
    rr = [d["actc"]["actc_ratio"] for d in runs]
    assert min(rr) < 0.9 and max(rr) > 1.0 and abs(statistics.mean(rr) - 0.95) < 0.02
    for key in ("tau_scale", "tau_up", "tau_down"):
        tv = [d["factors"][key]["value"] for d in runs]
        assert abs(statistics.correlation(rr, tv)) < 0.2, key       # 300 points: |rho| > 0.2 would be p < 1e-3
    assert abs(statistics.correlation(rr, [d["source_run"] for d in runs])) < 0.2
    # one r per source index, whatever the order or the failing set
    other = g.refly(SEED, N, synthetic_scores({5, 6}))
    by = {d["source_run"]: d["actc"] for d in other}
    assert all(by[d["source_run"]] == d["actc"] for d in runs)


def test_determinism_byte_identical():
    outs = []
    for _ in range(2):
        d = tempfile.mkdtemp(prefix="refly_")
        g.write(g.refly(SEED, N, SCORES), d, SEED, "refly")
        outs.append(d)
    for name in sorted(os.listdir(outs[0])):
        assert open(os.path.join(outs[0], name), "rb").read() == open(os.path.join(outs[1], name), "rb").read()
    runs = g.load_samples(outs[0], SEED, N)
    assert runs == json.loads(json.dumps(refly()))
    for bad in ((SEED + 1, N), (SEED, N - 1)):
        try:
            g.load_samples(outs[0], *bad)
        except SystemExit:
            continue
        raise AssertionError("seed / n mismatch must stop")
    for d in outs:
        shutil.rmtree(d)


def argval(argv, flag):
    return argv[argv.index(flag) + 1] if flag in argv else None


def test_runner_applies_actc_over_params_file():
    base = r.read_params(BASE)
    assert base["MC_INDI_ACT_TC"] == 0.033
    d = refly()[70]
    b = r.build_run(d, BASE, "/nonexistent/run_070")
    assert b["params"]["MC_INDI_ACT_TC"] == d["actc"]["mc_indi_act_tc"]
    assert b["merged_params"]["MC_INDI_ACT_TC"] == d["actc"]["mc_indi_act_tc"] != 0.033
    ap = b["applied"]["actc"]
    assert ap["mc_indi_act_tc"] == d["actc"]["mc_indi_act_tc"] and ap["base_params_value"] == 0.033
    # nothing else moves: same argv and the same other params as the draw without the block
    d0 = {k: v for k, v in d.items() if k != "actc"}
    b0 = r.build_run(d0, BASE, "/nonexistent/run_070")
    assert b0["argv"] == b["argv"]
    assert {k: v for k, v in b["merged_params"].items() if k != "MC_INDI_ACT_TC"} == \
        {k: v for k, v in b0["merged_params"].items() if k != "MC_INDI_ACT_TC"}


def test_runner_backwards_compatible_and_require_flag():
    d0 = {k: v for k, v in g.campaign(SEED, N)[5].items()}
    b0 = r.build_run(d0, BASE, "/nonexistent/run_005")
    assert "MC_INDI_ACT_TC" not in b0["params"] and b0["merged_params"]["MC_INDI_ACT_TC"] == 0.033
    assert "actc" not in b0["applied"]
    r.REQUIRE_ACTC = True
    try:
        try:
            r.build_run(d0, BASE, "/nonexistent/run_005")
        except AssertionError as e:
            assert "--require-actc" in str(e)
        else:
            raise AssertionError("--require-actc must refuse a draw without the block")
        r.build_run(refly()[0], BASE, "/nonexistent/run_000")     # with the block it passes
    finally:
        r.REQUIRE_ACTC = False


def test_runner_refuses_stale_actc_block():
    d = json.loads(json.dumps(refly()[70]))
    d["actc"]["mc_indi_act_tc"] = round(d["actc"]["mc_indi_act_tc"] * 1.2, 6)
    try:
        r.build_run(d, BASE, "/nonexistent/run_070")
    except AssertionError as e:
        assert "does not match" in str(e)
    else:
        raise AssertionError("an actc value that does not follow from the drawn tau must be refused")


def test_dry_run_cli_with_samples():
    d = tempfile.mkdtemp(prefix="refly_cli_")
    g.write(refly(), d, SEED, "refly")
    cmd = [sys.executable, os.path.join(BENCH, "g3_run.py"), "--seed", str(SEED), "--n", str(N), "--base-params", BASE,
           "--out-root", "/nonexistent/out", "--dry-run", "--start", "60", "--stop", "61", "--samples", d, "--require-actc"]
    out = subprocess.run(cmd, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    assert len(out.stdout.strip().splitlines()) == 2 and "/nonexistent/out/run_060" in out.stdout
    bad = subprocess.run(cmd[:cmd.index("--samples")] + ["--require-actc"], capture_output=True, text=True)
    assert bad.returncode != 0     # the seed's own campaign has no actc block: refused
    shutil.rmtree(d)


def test_finalize_records_applied_value_in_run_json():
    d = tempfile.mkdtemp(prefix="g3fin_")
    json.dump({"exit_status": "ok"}, open(os.path.join(d, "run.json"), "w"))
    blk = {"mc_indi_act_tc": 0.0421}
    assert r.finalize(d, {"returncode": 0}, {"g3_actc_applied": blk}) == "ok"
    assert json.load(open(os.path.join(d, "run.json")))["g3_actc_applied"] == blk
    shutil.rmtree(d)


# ------------------------------------------------------------------------------------------------------------------
# chain: --samples pin and --halt-on-fail (smoke hooks, fake docker)
# ------------------------------------------------------------------------------------------------------------------
FLIGHT = ('mkdir -p "$OUT" && echo "{\\"outcome\\": \\"ok\\"}" > "$OUT/g3_done.json" && '
          'echo "{\\"provenance\\": {\\"binary_sha256\\": \\"$(head -1 "$OUT/../chain_freeze.sha256" | cut -d" " -f1)\\"}}"'
          ' > "$OUT/run.json" && echo "{\\"draw\\": {\\"source_run\\": $((10#${OUT##*_}))}}" > "$OUT/g3_draw.json"')
# run 2: key 1 only fails item 2; run 3: both keys fail item 3 only; run 4: both keys fail item 2 (and 3)
SCORE = ('case "$IDX" in 2) a=\'["item2"]\'; b="[]"; k1=FAIL; k2=pass;; 3) a=\'["item3"]\'; b=\'["item3"]\'; k1=FAIL; k2=FAIL;; '
         '4) a=\'["item2","item3"]\'; b=\'["item2"]\'; k1=FAIL; k2=FAIL;; *) a="[]"; b="[]"; k1=pass; k2=pass;; esac; '
         'echo "{\\"idx\\": $IDX, \\"outcome\\": \\"ok\\", \\"key1\\": \\"$k1\\", \\"key2\\": \\"$k2\\", \\"key1_failing\\": $a, '
         '\\"key2_failing\\": $b, \\"key2_col5_g4_chatter_pass\\": true}" > "$OUT/chain_score.json"')


def abort_flight(done_json):
    """Flight hook: run 2 ends with the given g3_done.json (aborted), the others are ok."""
    return FLIGHT + ' && if [ "${OUT##*_}" = 002 ]; then echo \'' + done_json + '\' > "$OUT/g3_done.json"; fi'


ABORT_WD = '{"outcome": "aborted", "error": "WatchdogTrip: tilt", "watchdog": {"reason": "tilt > 60 deg for 0.5 s"}}'
ABORT_INFRA = '{"outcome": "aborted", "error": "RunError: gz sim exited early"}'


def chain(env, *args):
    return subprocess.run(["bash", CHAIN, *args], capture_output=True, text=True, env=env, timeout=120)


def wait_end(d, timeout=90):
    t0 = time.time()
    while time.time() - t0 < timeout:
        st = os.path.join(d, "chain_status.json")
        if os.path.exists(st) and json.load(open(st)).get("state") in ("halted", "finished", "stopped"):
            return json.load(open(st))
        time.sleep(0.5)
    raise AssertionError("chain did not end: " + open(os.path.join(d, "chain.log")).read()[-800:])


def test_chain_halt_on_fail_and_samples_pin():
    sha = subprocess.run(["sha256sum", os.path.join(REPO, "build/px4_sitl_default/bin/px4")], capture_output=True, text=True)
    lock = os.path.join(REPO, "indi_flight", "logs", "flight_chain.lock")
    if sha.returncode != 0 or subprocess.run(["flock", "-n", lock, "true"], capture_output=True).returncode != 0:
        print("SKIP chain test: no SITL binary or the chain lock is held")
        return
    sha = sha.stdout.split()[0]
    shim = tempfile.mkdtemp(prefix="fakedocker_")
    open(os.path.join(shim, "docker"), "w").write('#!/bin/sh\n[ "$1 $2" = "image inspect" ] && echo sha256:fake\nexit 0\n')
    os.chmod(os.path.join(shim, "docker"), 0o755)
    env = dict(os.environ, PATH=shim + ":" + os.environ["PATH"], G3_CHAIN_TEST_FLIGHT_CMD=FLIGHT, G3_CHAIN_TEST_SCORE_CMD=SCORE)
    samples = os.path.join(RESULTS, "g3_selftest_smoke_s212_samples")
    d1, d2, d3 = (os.path.join(RESULTS, f"g3_selftest_smoke_s212_{x}") for x in "abc")
    other = samples + "_other"
    for p in (samples, other, d1, d2, d3):
        shutil.rmtree(p, ignore_errors=True)
    g.write(refly(), samples, SEED, "refly")
    try:
        # a hook outside a *smoke* directory is refused
        o = chain(env, "start", os.path.join(RESULTS, "g3_selftest_s212_zzz"), "0", "5", "--allow-binary", sha)
        assert o.returncode != 0 and "smoke" in o.stderr
        # a: halt on both-key item 2 at run 4; run 2 (one key) and run 3 (item 3) do not halt
        o = chain(env, "start", d1, "0", "5", "--allow-binary", sha, "--samples", samples, "--halt-on-fail")
        st = wait_end(d1)
        assert st["state"] == "halted" and st["done"] == 5, st
        h = json.load(open(os.path.join(d1, "HALT_ON_FAIL.json")))
        assert h["idx"] == 4 and h["items"] == "item2" and h["source_run"] == "4", h
        assert "HALT_ON_FAIL run_004" in open(os.path.join(d1, "CHAIN_HALTED")).read()
        assert not os.path.exists(os.path.join(d1, "run_005"))
        assert open(os.path.join(d1, "chain_samples")).read().strip() == os.path.relpath(samples, REPO)
        assert os.path.exists(os.path.join(d1, "chain_halt_on_fail"))
        assert "g3_selftest_smoke_s212_samples/index.json" in open(os.path.join(d1, "chain_freeze.sha256")).read()
        # a halted DIR refuses a start; a different samples dir is refused after the pin
        assert chain(env, "start", d1, "--allow-binary", sha).returncode != 0
        os.remove(os.path.join(d1, "CHAIN_HALTED"))
        os.remove(os.path.join(d1, "HALT_ON_FAIL.json"))
        shutil.copytree(samples, other)
        o = chain(env, "start", d1, "--samples", other)
        assert o.returncode != 0 and "differs" in o.stderr, o.stderr
        # resume: the failed run 4 is kept, the chain goes on and finishes
        o = chain(env, "start", d1, "--allow-binary", sha)
        st = wait_end(d1)
        assert st["state"] == "finished" and st["done"] == 6, st
        assert not os.path.exists(os.path.join(d1, "HALT_ON_FAIL.json"))
        # b: same failures, no flag: no halt
        chain(env, "start", d2, "0", "5", "--allow-binary", sha, "--samples", samples)
        st = wait_end(d2)
        assert st["state"] == "finished" and st["done"] == 6, st
        assert not os.path.exists(os.path.join(d2, "chain_halt_on_fail"))
        # d: an aborted flight result (O-12 watchdog) halts with abort_flight; an infra abort does not
        d4, d5 = d1 + "_wd", d1 + "_infra"
        shutil.rmtree(d4, ignore_errors=True)
        shutil.rmtree(d5, ignore_errors=True)
        env4 = dict(env, G3_CHAIN_TEST_FLIGHT_CMD=abort_flight(ABORT_WD))
        chain(env4, "start", d4, "0", "5", "--allow-binary", sha, "--samples", samples, "--halt-on-fail")
        st = wait_end(d4)
        h = json.load(open(os.path.join(d4, "HALT_ON_FAIL.json")))
        assert st["state"] == "halted" and h["reason"] == "abort_flight" and h["idx"] == 2, (st, h)
        assert not os.path.exists(os.path.join(d4, "run_003"))
        env5 = dict(env, G3_CHAIN_TEST_FLIGHT_CMD=abort_flight(ABORT_INFRA))
        chain(env5, "start", d5, "0", "3", "--allow-binary", sha, "--samples", samples, "--halt-on-fail")
        st = wait_end(d5)
        assert st["state"] == "finished" and not os.path.exists(os.path.join(d5, "HALT_ON_FAIL.json")), st
        shutil.rmtree(d4)
        shutil.rmtree(d5)
        # e: a run scored on restart (skip_done) is judged; an already scored stopping run is not judged again
        d6 = d1 + "_skip"
        shutil.rmtree(d6, ignore_errors=True)
        chain(env, "start", d6, "0", "3", "--allow-binary", sha, "--samples", samples, "--halt-on-fail")
        assert wait_end(d6)["state"] == "finished"
        os.remove(os.path.join(d6, "CHAIN_FINISHED"))
        os.remove(os.path.join(d6, "run_003", "chain_score.json"))
        sc6 = SCORE.replace('case "$IDX" in', 'case "$IDX" in 3) a=\'["item2"]\'; b=\'["item2"]\'; k1=FAIL; k2=FAIL;;', 1)
        env6 = dict(env, G3_CHAIN_TEST_SCORE_CMD=sc6)
        chain(env6, "start", d6, "--allow-binary", sha)
        st = wait_end(d6)
        h = json.load(open(os.path.join(d6, "HALT_ON_FAIL.json")))
        assert st["state"] == "halted" and h["idx"] == 3 and h["items"] == "item2", (st, h)
        os.remove(os.path.join(d6, "CHAIN_HALTED"))
        os.remove(os.path.join(d6, "HALT_ON_FAIL.json"))
        chain(env6, "start", d6, "--allow-binary", sha)
        assert wait_end(d6)["state"] == "finished" and not os.path.exists(os.path.join(d6, "HALT_ON_FAIL.json"))
        shutil.rmtree(d6)
        # f: scoring that leaves no score stops the chain with score_pending
        d7 = d1 + "_pend"
        shutil.rmtree(d7, ignore_errors=True)
        env7 = dict(env, G3_CHAIN_TEST_SCORE_CMD="true")
        chain(env7, "start", d7, "0", "3", "--allow-binary", sha, "--samples", samples, "--halt-on-fail")
        st = wait_end(d7)
        h = json.load(open(os.path.join(d7, "HALT_ON_FAIL.json")))
        assert st["state"] == "halted" and h["reason"] == "score_pending" and h["idx"] == 0, (st, h)
        assert not os.path.exists(os.path.join(d7, "run_001"))
        shutil.rmtree(d7)
        # c: no --samples: a seed-campaign DIR as before (no pin file, the flight command has no --samples)
        chain(env, "start", d3, "0", "1", "--allow-binary", sha)
        wait_end(d3)
        assert not os.path.exists(os.path.join(d3, "chain_samples"))
    finally:
        for p in (samples, other, d1, d2, d3, shim):
            shutil.rmtree(p, ignore_errors=True)


def test_chain_flight_command_carries_samples_flags():
    src = open(CHAIN).read()
    assert '${SAMPLES:+--samples "$SAMPLES" --require-actc}' in src


if __name__ == "__main__":
    n = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print("ok", name)
    print(f"{n} tests passed")
