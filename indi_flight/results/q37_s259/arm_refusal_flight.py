#!/usr/bin/env python3
"""Test 7: arming is refused while the rpm telemetry is stale or missing, accepted once it is back, then takeoff and hover.

Why a script: run_scenario.py has no hook between boot and arm that changes the telemetry (its erpm-loss params are timed
inside a flight). This wraps its main(): Sim.cmd is patched so the arm commands of the runner's own retry loop drive the
phases, everything else (boot, params, takeoff, hover, metrics) is the unchanged runner.

  arm attempts 1-4: SIM_GZ_ERPM_LOSS = 15 (every eRPM frame fails: samples go stale)  -> must be refused
  arm attempts 5-8: loss cleared, `failure esc off` on all ESCs (online flags cleared) -> must be refused
  arm attempt 9   : `failure esc ok` (telemetry back)                                  -> must be accepted, then takeoff
Usage: arm_refusal_flight.py <run_scenario.py arguments>   (needs --out; result in OUT/arm_refusal.json, prints TEST7 PASS|FAIL)
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "bench"))
import run_scenario as rs  # noqa: E402

STALE_LAST, MISSING_LAST, ACCEPT_AT = 4, 8, 9
state = {"attempts": []}
orig_cmd = rs.Sim.cmd


def phase_actions(sim, n):
    if n == 1:
        sim.set_param("SIM_GZ_ERPM_LOSS", 15)
    elif n == STALE_LAST + 1:
        sim.set_param("SIM_GZ_ERPM_LOSS", 0)
        sim.cli("px4-failure", "esc", "off", "-i", "0")
    elif n == ACCEPT_AT:
        sim.cli("px4-failure", "esc", "ok", "-i", "0")
    sim.run(0.5, what=f"settle_before_arm_{n}")


def cmd(self, command, p1=0, *args, **kw):
    if command != 400 or p1 != 1:
        return orig_cmd(self, command, p1, *args, **kw)
    n = len(state["attempts"]) + 1
    phase_actions(self, n)
    accepted = orig_cmd(self, command, p1, *args, **kw)
    phase = "stale" if n <= STALE_LAST else "missing" if n <= MISSING_LAST else "restored"
    state["attempts"].append({"attempt": n, "phase": phase, "sim_t_s": round(self.t, 2), "accepted": bool(accepted)})
    if n < ACCEPT_AT and accepted:
        raise rs.RunError(f"arming accepted at attempt {n} while telemetry is {phase}")
    return accepted


def ulog_summary(out):
    """Reply stream of the module (registration id 0, can_arm_and_run transitions) and standalone events, from flight.ulg."""
    from pyulog import ULog
    res = {}
    try:
        u = ULog(os.path.join(out, "flight.ulg"), ["arming_check_reply", "event"])
        for d in u.data_list:
            t = d.data["timestamp"] * 1e-6
            if d.name == "arming_check_reply":
                rows = [(round(float(t[i]), 2), int(d.data["registration_id"][i]), bool(d.data["can_arm_and_run"][i]))
                        for i in range(len(t))]
                changes = [r for i, r in enumerate(rows) if i == 0 or rows[i - 1][1:] != r[1:]]
                res["reply_changes_t_reg_can_arm"] = changes
                res["reply_count"] = len(rows)
            elif d.name == "event":
                ev = {}
                for i in range(len(t)):
                    a0 = [int(d.data[f"arguments[{k}]"][i]) for k in range(2)]
                    ev.setdefault((int(d.data["id"][i]), a0[0] + 256 * a0[1], int(d.data["log_levels"][i])), []).append(round(float(t[i]), 1))
                res["events_id_arg0_levels"] = {f"id=0x{k[0]:x} arg0={k[1]} levels=0x{k[2]:x}": v for k, v in ev.items()}
    except Exception as e:  # noqa: BLE001
        res["ulog_error"] = repr(e)
    return res


def verdict(out):
    att = state["attempts"]
    ok = (len(att) == ACCEPT_AT and not any(a["accepted"] for a in att[:-1]) and att[-1]["accepted"])
    lines = []
    try:
        for ln in open(os.path.join(out, "px4.log"), errors="replace"):
            if re.search(r"Arming denied|rpm telemetry|arming check registered|Armed by|Takeoff|Ready for takeoff", ln):
                lines.append(ln.rstrip())
    except OSError:
        pass
    ok = ok and any("Armed by" in ln for ln in lines)
    json.dump({"pass": ok, "attempts": att, "ulog": ulog_summary(out), "px4_log_lines": lines}, open(os.path.join(out, "arm_refusal.json"), "w"), indent=1)
    print("TEST7", "PASS" if ok else "FAIL", json.dumps(att))
    return ok


if __name__ == "__main__":
    out = sys.argv[sys.argv.index("--out") + 1]
    rs.Sim.cmd = cmd
    rs.LOG_TOPICS = rs.LOG_TOPICS + ["arming_check_reply", "event"]
    rs.T_ARM_S = 15.0  # the 9 attempts take about 13 s of sim time; the accepted one then lands near the runner's usual T_ARM_S of 30 s
    rc = 1
    try:
        rc = rs.main()
    except SystemExit as e:
        rc = e.code
    ok = verdict(out)
    sys.exit(0 if (ok and not rc) else 1)
