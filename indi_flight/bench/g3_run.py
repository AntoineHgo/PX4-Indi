#!/usr/bin/env python3
"""G3 driver: one sampler draw -> one run_scenario.py invocation (no analysis, no pass/fail).

    python3 bench/g3_run.py --seed S --n N --base-params FILE --out-root DIR [--dry-run] [--start K] [--timeout-s T]

build_run(draw, base_params_path, out_dir) is pure: returns {argv, params, applied, not_applied, notes}. Every factor of the
draw (each key of draw["factors"], plus mode and g4_typical_noise) ends in `applied` or `not_applied` (with a reason).
Design: design/g3_runner_s110.md. Flights are not exercised by the self-test; the mapping is checked against the argparse
of run_scenario.py by reading, not by flying (see UNVERIFIED in the design note).
"""
import argparse
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import g3_sample  # noqa: E402

RUN_SCENARIO = os.path.join(HERE, "run_scenario.py")
CONTROLLER = "indi"
# UNVERIFIED: no G3 scenario with the "take-off, hover, step_roll, lemniscate, hold" timeline exists in scenarios.py yet;
# o1_lemniscate (trajectory, --sched) is a stand-in. Stick modes use stick_zsine_o6 + --stick-mode.
SCENARIO_POSITION = "o1_lemniscate"
SCENARIO_STICK = "stick_zsine_o6"
# main flight segment (start of the fault / wind window) and the segment that ends an eRPM loss, per scenario
MAIN_SEGMENT = {SCENARIO_POSITION: "traj", SCENARIO_STICK: "stick"}
END_SEGMENT = "hold"
OVERRIDES_NAME = "g3_scenario_overrides.json"
RATE_HZ = 800
G1_PARAMS = (("roll", "MC_INDI_G1_R"), ("pitch", "MC_INDI_G1_P"), ("yaw", "MC_INDI_G1_Y"))
NOMINAL_EPS = 1e-9


def read_params(path):
    p = {}
    with open(path) as fh:
        for line in fh:
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            name, _, val = line.partition(" ")
            val = val.strip()
            try:
                p[name] = int(val)
            except ValueError:
                p[name] = float(val)
    return p


def fmt_params(p):
    return "".join(f"{k} {p[k]!r}\n" if isinstance(p[k], float) else f"{k} {p[k]}\n" for k in sorted(p))


def _num(x):
    return repr(float(x))


def _nominal(x, nom=1.0):
    return abs(x - nom) <= NOMINAL_EPS


def _round_ms(x):
    return int(math.floor(x + 0.5))


def build_run(draw, base_params_path, out_dir):
    f = draw["factors"]
    base = read_params(base_params_path)
    params = {}
    applied, not_applied, notes = {}, {}, {}
    argv = []

    # fixed set-up ------------------------------------------------------------------------------------------------
    mode = draw["mode"]
    if mode == "position":
        scenario = SCENARIO_POSITION
        sched = ["--sched"]
        stick = []
    else:
        scenario = SCENARIO_STICK
        sched = []
        stick = ["--stick-mode", mode] + (["--stick-pilot"] if mode in ("stabilized", "acro") else [])
    params_path = os.path.join(out_dir, "g3_params.txt")
    argv += ["--scenario", scenario, "--controller", CONTROLLER, "--model", "quad5in", "--sim", "v2",
             "--rate-hz", str(RATE_HZ), "--seed", str(int(draw["sampler_seed"]) % (2 ** 31)),
             "--sim-seed", str(int(draw["gz_seed"])), "--out", out_dir, "--params", params_path] + sched + stick
    applied["mode"] = {"value": mode, "scenario": scenario}

    # controller G1 multiplier (g1_err / g1_ratio are the drawn e; the written multiplier is k = e / I_scale) ----------
    mult = f["g1_ctrl_mult"]
    missing = [name for ax, name in G1_PARAMS if name not in base]
    if missing:
        for k in ("g1_ctrl_mult", "g1_err", "g1_ratio"):
            not_applied[k] = f"base params lack nominal {','.join(missing)}"
    else:
        for ax, name in G1_PARAMS:
            params[name] = round(base[name] * mult[ax], 6)
        applied["g1_ctrl_mult"] = {ax: mult[ax] for ax, _ in G1_PARAMS}
        applied["g1_err"] = "via g1_ctrl_mult: PX4 params MC_INDI_G1_R/P/Y = base x k"
        applied["g1_ratio"] = "alias of g1_err, via g1_ctrl_mult"

    # model variant -----------------------------------------------------------------------------------------------
    mv = draw["hooks"]["model_variant"]
    items = []
    for key in ("tau", "tau_up", "tau_down", "mass", "ixx", "iyy", "izz"):
        if key in mv and not _nominal(mv[key]):
            items.append(f"{key}={_num(mv[key])}")
    if items:
        argv += ["--model-variant", ",".join(items)]
    mv_keys = {k.split("=")[0] for k in items}
    applied["tau_scale"] = {"value": f["tau_scale"]["value"], "via": "--model-variant tau" if "tau" in mv_keys else "nominal"}
    applied["tau_asym"] = {"value": f["tau_asym"]["value"],
                           "via": "--model-variant tau_down" if "tau_down" in mv_keys else "nominal"}
    applied["mass_scale"] = {"value": f["mass_scale"]["value"], "via": "--model-variant mass" if "mass" in mv_keys else "nominal"}
    applied["inertia_scale"] = {k: f["inertia_scale"][k] for k in ("ixx", "iyy", "izz")}

    # loop delay: run_scenario takes integer ms 0..10 -------------------------------------------------------------------
    ld = f["loop_delay"]
    da, di = _round_ms(ld["act_ms"]), _round_ms(ld["imu_ms"])
    if da:
        argv += ["--dly-act", str(da)]
    if di:
        argv += ["--dly-imu", str(di)]
    applied["loop_delay"] = {"requested_act_ms": ld["act_ms"], "requested_imu_ms": ld["imu_ms"],
                             "act_ms": da, "imu_ms": di}
    if abs(da - ld["act_ms"]) > 1e-9 or abs(di - ld["imu_ms"]) > 1e-9:
        notes["loop_delay"] = "--dly-act/--dly-imu are integer ms; 1.25 ms-step draw rounded to nearest ms"

    # telemetry ---------------------------------------------------------------------------------------------------
    lat = int(f["tel_latency"]["frames"])
    params["SIM_GZ_ERPM_LAT"] = lat
    applied["tel_latency"] = {"frames": lat, "via": "param SIM_GZ_ERPM_LAT"}
    td = f["tel_dropout"]
    if td["on"]:
        argv += ["--erpm-drop", _num(td["prob"])]
        applied["tel_dropout"] = {"prob": td["prob"]}
    else:
        applied["tel_dropout"] = {"on": False}
    ov = {}   # --scenario-overrides content (bench/scenario_overrides.py)
    main_seg = MAIN_SEGMENT[scenario]
    tl = f["tel_loss"]
    if tl["on"]:
        ov["erpm_loss"] = {"motor": int(tl["motor"]), "start": main_seg, "start_offset_s": tl["start_offset_s"],
                           "duration_s": tl["duration_s"]}
        applied["tel_loss"] = {"motor": tl["motor"], "start": main_seg, "start_offset_s": tl["start_offset_s"],
                               "duration_s": tl["duration_s"], "via": "scenario-overrides erpm_loss (timed, sim time)"}
        notes["tel_loss"] = (f"anchor = start of '{main_seg}' (the single anchor of all timed G3 events): loss from "
                             f"+{tl['start_offset_s']} s for {tl['duration_s']} s (sim time)")
    else:
        applied["tel_loss"] = {"on": False}
    if f["tel_frozen"]["on"]:
        not_applied["tel_frozen"] = "hook missing"
    else:
        applied["tel_frozen"] = {"on": False}

    # vibration ---------------------------------------------------------------------------------------------------
    vb = f["vibration"]
    argv += ["--vib-acc", _num(vb["acc_ms2"]), "--vib-gyr", _num(vb["gyr_rads"])]
    applied["vibration"] = {"acc_ms2": vb["acc_ms2"], "gyr_rads": vb["gyr_rads"], "mult": vb["mult"]}

    # GNSS --------------------------------------------------------------------------------------------------------------
    g = f["gnss"]
    argv += ["--gps-dly", str(int(g["latency_ms"]))]
    if g["ekf_delay_ms"] is not None:
        argv += ["--gnss-delay", str(int(g["ekf_delay_ms"]))]
    applied["gnss"] = {"latency_ms": g["latency_ms"], "ekf_delay_ms": g["ekf_delay_ms"]}

    # thrust: sag (ramp over the window), saturation (all motors step), weak motor (one motor step) -------------------------
    sg, sat, wk = f["thrust_sag"], f["saturation"], f["weak_motor"]
    if sg["on"]:
        ov["thrust_sag"] = {"scale": sg["scale"]}
        applied["thrust_sag"] = {"scale": sg["scale"], "via": "scenario-overrides thrust_sag (linear ramp over the whole window)"}
        notes["thrust_sag"] = f"ramp length is the scenario window, not the drawn ramp_s {sg.get('ramp_s')}"
    else:
        applied["thrust_sag"] = {"on": False}
    faults = []
    if sat["on"]:
        faults.append({"segment": main_seg, "motors": [0, 1, 2, 3], "thrust_scale": sat["scale"]})
        applied["saturation"] = {"scale": sat["scale"], "via": f"scenario-overrides motor_fault, all motors, step at '{main_seg}'"}
    else:
        applied["saturation"] = {"on": False}
    if wk["on"]:
        faults.append({"segment": main_seg, "motor": int(wk["motor"]), "thrust_scale": wk["scale"]})
        applied["weak_motor"] = {"motor": wk["motor"], "scale": wk["scale"],
                                 "via": f"scenario-overrides motor_fault, step at '{main_seg}' (multiplies with saturation)"}
    else:
        applied["weak_motor"] = {"on": False}
    if faults:
        ov["motor_fault"] = faults[0] if len(faults) == 1 else faults

    # wind: gust_x profile, world frame, direction = where the air moves to --------------------------------------------------
    w = f["wind"]
    if w["steady_ms"] == 0.0 and w["gust_amp_ms"] == 0.0:
        applied["wind"] = {"steady_ms": 0.0, "gust_amp_ms": 0.0}
    else:
        ov["disturbance"] = "gust_x"
        ov["dist_segment"] = main_seg
        ov["wind"] = {"steady": w["steady_ms"], "peak": w["gust_peak_total_ms"], "dir_deg": w["dir_deg"]}
        applied["wind"] = {"steady_ms": w["steady_ms"], "gust_peak_total_ms": w["gust_peak_total_ms"], "dir_deg": w["dir_deg"],
                           "via": f"scenario-overrides wind, profile starts at '{main_seg}'"}
        notes["wind"] = ("gust_x timing is fixed (2 s ramp, 10 s hold, 1 s gust, 15 s hold, 28 s) from the segment start; the drawn "
                         f"gust_offset_s {w.get('gust_offset_s')} is not used")

    if ov:
        argv += ["--scenario-overrides", os.path.join(out_dir, OVERRIDES_NAME)]

    # G4 typical-noise profile ------------------------------------------------------------------------------------------
    not_applied["g4_typical_noise"] = "hook missing"

    # every factor accounted for (loud, never silent) ----------------------------------------------------------------------
    expected = set(f) | {"mode", "g4_typical_noise"}
    got = set(applied) | set(not_applied)
    if expected - got:
        raise AssertionError(f"unaccounted factors: {sorted(expected - got)}")
    if set(applied) & set(not_applied):
        raise AssertionError(f"factor in both: {sorted(set(applied) & set(not_applied))}")

    merged = dict(base)
    merged.update(params)
    return {"argv": argv, "params": params, "overrides": ov, "merged_params": merged, "applied": applied, "not_applied": not_applied,
            "notes": notes}


def command(argv):
    return [sys.executable, RUN_SCENARIO] + argv


def classify(out, status):
    """Outcome of a finished runner call. 'ok'; 'aborted' = the flight ran and ended early (watchdog trip, crash, no
    ulog: run.json exit_status 'failed'); 'incomplete' = no verdict (timeout, runner died before writing run.json)."""
    try:
        with open(os.path.join(out, "run.json")) as fh:
            rj = json.load(fh)
    except (OSError, ValueError):
        rj = None
    if rj is not None and rj.get("exit_status") == "failed":  # K113 MINOR 5: a failed run.json wins over rc 0
        return "aborted", rj
    if status.get("returncode") == 0:
        return "ok", rj
    return "incomplete", rj


def finalize(out, status):
    """Record the outcome in g3_done.json (and in run.json as g3_outcome). An aborted run is a finished FAILURE: it gets
    the done marker (outcome 'aborted', not retried, counted as a failure by the campaign). Only an incomplete run
    (timeout, no run.json) gets g3_failed.json and no done marker, so it is retried on the next invocation."""
    outcome, rj = classify(out, status)
    status["outcome"] = outcome
    if outcome == "aborted":
        status["error"] = rj.get("error")
        status["watchdog"] = rj.get("watchdog")
        status["metrics_status"] = rj.get("metrics_status")
    if rj is not None:
        rj["g3_outcome"] = outcome
        with open(os.path.join(out, "run.json"), "w") as fh:
            json.dump(rj, fh, indent=1)
    if outcome in ("ok", "aborted"):
        with open(os.path.join(out, "g3_done.json"), "w") as fh:
            fh.write(json.dumps(status) + "\n")
    else:  # no finished marker: the run is retried on the next invocation
        with open(os.path.join(out, "g3_failed.json"), "w") as fh:
            fh.write(json.dumps(status) + "\n")
    return outcome


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--seed", type=int, required=True, help="G3 master seed")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--base-params", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--dry-run", action="store_true", help="print the commands, write nothing but nothing is flown")
    ap.add_argument("--start", type=int, default=0, help="first run index to process")
    ap.add_argument("--stop", type=int, default=None, help="last run index to process (inclusive); draws still use --n")
    ap.add_argument("--timeout-s", type=float, default=1800.0, help="wall-clock timeout per run")
    a = ap.parse_args()

    draws = g3_sample.campaign(a.seed, a.n)
    for d in draws:
        if d["run_index"] < a.start or (a.stop is not None and d["run_index"] > a.stop):
            continue
        out = os.path.join(a.out_root, f"run_{d['run_index']:03d}")
        r = build_run(d, a.base_params, out)
        cmd = command(r["argv"])
        if a.dry_run:
            print(" ".join(cmd))
            continue
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "g3_draw.json"), "w") as fh:
            fh.write(json.dumps({"draw": d, "build": r, "command": cmd}, indent=1, sort_keys=True) + "\n")
        with open(os.path.join(out, "g3_params.txt"), "w") as fh:
            fh.write(fmt_params(r["merged_params"]))
        if r["overrides"]:
            with open(os.path.join(out, OVERRIDES_NAME), "w") as fh:
                fh.write(json.dumps(r["overrides"], indent=1, sort_keys=True) + "\n")
        done = os.path.join(out, "g3_done.json")
        if os.path.exists(done):
            print(f"run_{d['run_index']:03d}: finished marker present, skipped", flush=True)
            continue
        try:
            with open(os.path.join(out, "g3_stdout.txt"), "w") as so:
                p = subprocess.run(cmd, stdout=so, stderr=subprocess.STDOUT, timeout=a.timeout_s)
            status = {"returncode": p.returncode}
        except subprocess.TimeoutExpired:
            status = {"returncode": None, "timeout_s": a.timeout_s}
        finalize(out, status)
        print(f"run_{d['run_index']:03d}: {status}", flush=True)


if __name__ == "__main__":
    main()
