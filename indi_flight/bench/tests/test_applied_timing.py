#!/usr/bin/env python3
"""Self-test for indi_flight/bench/applied_timing.py matching and summary (plain asserts, no ULog/pyulog needed).

  python3 indi_flight/bench/tests/test_applied_timing.py
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import applied_timing as A  # noqa: E402

MS = 1000


def main():
    # fake trajectory_setpoint log at 10 ms; x ramps with setpoint k, so every send value is unique
    t = np.arange(0, 2_000_000, 10 * MS, dtype=np.int64)
    x = np.full(t.size, np.nan)
    sends, known = [], []
    # sends every 50 ms with x=k*0.1 (k=1..20); applied delay known = 4 ms * (k % 5 + 1) -> first sample >= send+delay
    for k in range(1, 21):
        ius = 50 * MS * k
        delay = 4 * MS * (k % 5 + 1)
        first = int(np.ceil((ius + delay) / (10 * MS)) * 10 * MS)  # logged on the next 10 ms grid point
        x[first // (10 * MS)] = 0.1 * k
        sends.append(dict(kind="send_pos", intended_us=ius, payload=f"x={0.1 * k:.5g};y=0;z=-5;yaw=1.5"))
        known.append(first - ius)
    # logged samples carry y,z,yaw constant; make y,z,yaw valid wherever x is valid
    cols = {"position[0]": x, "position[1]": np.where(np.isnan(x), np.nan, 0.0),
            "position[2]": np.where(np.isnan(x), np.nan, -5.0), "yaw": np.where(np.isnan(x), np.nan, 1.5)}
    # row 21: never logged -> unmatched
    sends.append(dict(kind="send_pos", intended_us=1_200_000, payload="x=9;y=0;z=-5;yaw=1.5"))
    # row 22: matches 3 samples (same value logged 3 times) -> first used
    i0 = 1_400_000 // (10 * MS) + 2
    for j in range(3):
        for c, v in (("position[0]", 7.0), ("position[1]", 0.0), ("position[2]", -5.0), ("yaw", 1.5)):
            cols[c][i0 + j] = v
    sends.append(dict(kind="send_pos", intended_us=1_400_000, payload="x=7;y=0;z=-5;yaw=1.5"))
    known.append(int(t[i0]) - 1_400_000)
    # row 23: sample exists BEFORE intended only -> unmatched (no time travel)
    sends.append(dict(kind="send_pos", intended_us=1_800_000, payload="x=0.1;y=0;z=-5;yaw=1.5"))
    # params: one applied 30 ms later, one pre-log, one never
    changes = [(900 * MS + 30 * MS, "MPC_X", 2.5)]
    initial = {"PRE": 1.0}
    sends += [dict(kind="param", intended_us=900 * MS, payload="MPC_X=2.5"),
              dict(kind="param", intended_us=0, payload="PRE=1"),
              dict(kind="sag", intended_us=900 * MS, payload="SIM_GZ_THR_SC=0.9;frac=0.1;sched_us=900000")]
    rows = A.compute_rows(sends, {"trajectory_setpoint": (t, cols)}, changes, initial, log_start_us=100 * MS,
                          tol=1e-3, window_us=500 * MS)

    pos = [r for r in rows if r["kind"] == "send_pos"]
    got = [r["delay_us"] for r in pos if r["status"] == "matched"]
    assert got == known, (got, known)
    assert pos[20]["status"] == "unmatched" and pos[20]["delay_us"] is None
    assert pos[21]["status"] == "matched" and pos[21]["n_matches"] == 3 and pos[21]["applied_us"] == int(t[i0])
    assert pos[22]["status"] == "unmatched"
    par = [r for r in rows if r["kind"] in A.PARAM_KINDS]
    assert (par[0]["status"], par[0]["delay_us"]) == ("matched", 30 * MS)
    assert par[1]["status"] == "pre_log" and par[2]["status"] == "unmatched"
    assert all(r["changed"] for r in pos)  # every payload differs from the previous one

    s = A.summarize(rows, {"send_pos": 10 * MS, "param": None, "sag": None}, step_us=4 * MS)
    sp = s["send_pos"]
    assert (sp["n"], sp["n_matched"], sp["n_unmatched"], sp["n_multi_match"]) == (23, 21, 2, 1)
    d = np.array(known)
    assert sp["all"]["p50_us"][0] == np.percentile(d, 50) and sp["all"]["max_us"][0] == d.max()
    assert abs(sp["all"]["p95_us"][1] - np.percentile(d, 95) / 4000) < 1e-9
    assert s["param"]["n_matched"] == 1 and s["sag"]["n_unmatched"] == 1

    # constant payload: every send matches, `changed` only on the first row, caveat raised
    tc = np.arange(0, 1_000_000, 200 * MS, dtype=np.int64)
    cc = {"position[0]": np.zeros(tc.size), "position[1]": np.zeros(tc.size), "position[2]": np.full(tc.size, -5.0),
          "yaw": np.full(tc.size, 1.5)}
    cs = [dict(kind="send_pos", intended_us=20 * MS * k, payload="x=0;y=0;z=-5;yaw=1.5") for k in range(1, 40)]
    rc = A.compute_rows(cs, {"trajectory_setpoint": (tc, cc)}, [], {}, 0)
    assert sum(r["changed"] for r in rc) == 1 and all(r["status"] == "matched" for r in rc)
    assert max(r["delay_us"] for r in rc) <= 200 * MS
    assert "decimation" in A.summarize(rc, {"send_pos": 200 * MS}, 4 * MS)["send_pos"]["caveat"]
    print("test_applied_timing: OK")


if __name__ == "__main__":
    main()
