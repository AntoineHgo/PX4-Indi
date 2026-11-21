"""Self-test of bench/run_validity.py with fake ulog objects. Run: python3 -m pytest -q tests/test_run_validity.py"""
import os
import sys
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import run_validity as rv  # noqa: E402


def topic(name, hz, n=2000):
    dt = int(round(1e6 / hz))
    return SimpleNamespace(name=name, data={"timestamp": [i * dt for i in range(n)]})


def ulog(params, topics=()):
    return SimpleNamespace(initial_parameters=params, data_list=list(topics))


REQ = {"MC_INDI_G1_R": 1586.3197, "MC_RATE_CTL_TYPE": 1}
LOG = {"MC_INDI_G1_R": 1586.3197021484375, "MC_INDI_EN": 1}


def run(u, req, ctl):
    return rv.check_run("unused", req, ctl, _ulog=u)


def test_valid_indi():
    r = run(ulog(LOG, [topic("indi_rate_status", 800)]), REQ, "indi")
    assert r["valid"], r["problems"]


def test_indi_en_zero_invalid():
    r = run(ulog(dict(LOG, MC_INDI_EN=0), [topic("indi_rate_status", 800)]), REQ, "indi")
    assert not r["valid"] and any("MC_INDI_EN" in p for p in r["problems"])


def test_param_mismatch_invalid():
    r = run(ulog(dict(LOG, MC_INDI_G1_R=1500.0), [topic("indi_rate_status", 800)]), REQ, "indi")
    assert not r["valid"] and any("MC_INDI_G1_R" in p for p in r["problems"])


def test_missing_param_invalid():
    r = run(ulog(LOG, [topic("indi_rate_status", 800)]), dict(REQ, MC_FOO=1.0), "indi")
    assert not r["valid"] and any("MC_FOO" in p for p in r["problems"])


def test_low_rate_invalid():
    r = run(ulog(LOG, [topic("indi_rate_status", 400)]), REQ, "indi")
    assert not r["valid"] and any("rate" in p for p in r["problems"])


def test_indi_topic_absent_invalid():
    assert not run(ulog(LOG), REQ, "indi")["valid"]


def test_pos_module_required_when_requested():
    req = dict(REQ, MC_INDI_POS_EN=1)
    u = ulog(dict(LOG, MC_INDI_POS_EN=1), [topic("indi_rate_status", 800)])
    assert not run(u, req, "indi")["valid"]
    u = ulog(dict(LOG, MC_INDI_POS_EN=1), [topic("indi_rate_status", 800), topic("indi_pos_status", 100)])
    assert run(u, req, "indi")["valid"]


def test_valid_pid():
    r = run(ulog({"MC_INDI_EN": 0, "MC_ROLLRATE_P": 0.15}), {"MC_ROLLRATE_P": 0.15}, "pid")
    assert r["valid"], r["problems"]


def test_pid_with_indi_topic_invalid():
    r = run(ulog({"MC_INDI_EN": 0}, [topic("indi_rate_status", 800)]), {}, "pid")
    assert not r["valid"] and any("indi_rate_status" in p for p in r["problems"])


def test_pid_with_indi_en_invalid():
    assert not run(ulog({"MC_INDI_EN": 1}), {}, "pid")["valid"]


def test_ca_r_w_max_alias_translated():  # K122 #1
    u = ulog(dict(LOG, MC_INDI_W_MAX=1000.0), [topic("indi_rate_status", 800)])
    assert run(u, dict(REQ, CA_R_W_MAX=1000.0), "indi")["valid"]
    r = run(ulog(dict(LOG, MC_INDI_W_MAX=900.0), [topic("indi_rate_status", 800)]), dict(REQ, CA_R_W_MAX=1000.0), "indi")
    assert not r["valid"] and any("MC_INDI_W_MAX" in p for p in r["problems"])


def test_pid_default_alias_valid():
    # S186: g3 pre-test launched PID runs as "pid_default"; they were voided as unknown controller
    r = run(ulog({"MC_INDI_EN": 0}), {}, "pid_default")
    assert r["valid"], r["problems"]


def test_pid_alias_still_checks_pid():
    r = run(ulog({"MC_INDI_EN": 0}, [topic("indi_rate_status", 800)]), {}, "pid_default")
    assert not r["valid"] and any("pid run" in p for p in r["problems"])


def test_unknown_controller_void():
    assert not run(ulog({"MC_INDI_EN": 0}), {}, "foo")["valid"]
