"""Q27 item 8 self-test: a harness-aborted G3 run must score INVALID (never PASS) in key 1 (g3_score.sh) and key 2
(g3_checks_key2.py). Run: python3 bench/tests/test_g3_harness_abort.py"""
import json
import os
import subprocess
import sys
import tempfile

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def aborted_run(root, err="RunError: wall timeout (150s) in phase 'land' (sim t=681.77)", outcome="aborted"):
    d = os.path.join(root, "run_039")
    os.makedirs(d)
    json.dump({"exit_status": "failed", "error": err, "g3_outcome": outcome, "metrics_status": "ok"}, open(d + "/run.json", "w"))
    json.dump({"returncode": 1, "outcome": outcome, "error": err}, open(d + "/g3_done.json", "w"))
    return d


def test_status_helper():
    sys.path.insert(0, B)
    import g3_run_status as s
    with tempfile.TemporaryDirectory() as t:
        assert s.invalid_reason(aborted_run(t))
    with tempfile.TemporaryDirectory() as t:
        d = os.path.join(t, "run_001")
        os.makedirs(d)
        json.dump({"exit_status": "ok", "error": None, "g3_outcome": "ok"}, open(d + "/run.json", "w"))
        json.dump({"outcome": "ok"}, open(d + "/g3_done.json", "w"))
        assert s.invalid_reason(d) is None
    with tempfile.TemporaryDirectory() as t:  # no status files: fail closed
        os.makedirs(os.path.join(t, "r"))
        assert s.invalid_reason(os.path.join(t, "r"))


def test_key1_invalid():
    with tempfile.TemporaryDirectory() as t:
        d = aborted_run(t)  # no flight.ulg, no metrics.json: an unfixed scorer crashes or scores nothing
        subprocess.run(["bash", os.path.join(B, "g3_score.sh"), t], capture_output=True, text=True)
        j = json.load(open(d + "/g3_checks.json"))
        assert j.get("invalid") is True and not j.get("pass"), j


def test_key2_invalid():
    with tempfile.TemporaryDirectory() as t:
        d = aborted_run(t)
        out = os.path.join(t, "k2")
        subprocess.run([sys.executable, os.path.join(B, "g3_checks_key2.py"), d, "--t0", "0", "--t1", "1", "--out", out],
                       capture_output=True, text=True)
        j = json.load(open(os.path.join(out, "run_039.json")))
        assert j.get("invalid") is True and not j.get("pass"), j


if __name__ == "__main__":
    for n, f in sorted(globals().items()):
        if n.startswith("test_"):
            try:
                f()
                print("PASS", n)
            except Exception as e:  # noqa: BLE001
                print("FAIL", n, type(e).__name__, e)
                sys.exit(1)
