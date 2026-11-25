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
import run_validity  # noqa: E402

# D-NOISE-PROF typical profile (same values as bench/gate_g4.sh "typ")
TYPICAL_VIB_ACC, TYPICAL_VIB_GYR, TYPICAL_IMU_NSC = 10.0, 0.0, 4.0

RUN_SCENARIO = os.path.join(HERE, "run_scenario.py")
CONTROLLER = "indi"
# S214 (Q30 B): dedicated G3 scenarios, main segment of o1_lemniscate / stick_zsine_o6 then a hold of scenarios.G3_HOLD_S;
# steady wind and sag held to the end (wind hold_to_end, sag ramp_s). The stand-ins stay selectable (--legacy-scenarios) for
# runs flown before S214 and for the tests of the old behaviour.
SCENARIO_POSITION_LEGACY = "o1_lemniscate"
SCENARIO_STICK_LEGACY = "stick_zsine_o6"
SCENARIO_POSITION_G3 = "g3_lemniscate"
SCENARIO_STICK_G3 = "g3_stick_zsine"
LEGACY_SCENARIOS = False  # set by --legacy-scenarios
SCENARIO_POSITION = SCENARIO_POSITION_G3
SCENARIO_STICK = SCENARIO_STICK_G3
G3_SCENARIOS = (SCENARIO_POSITION_G3, SCENARIO_STICK_G3)
# main flight segment (start of the fault / wind window) and the segment that ends an eRPM loss, per scenario
MAIN_SEGMENT = {SCENARIO_POSITION_LEGACY: "traj", SCENARIO_STICK_LEGACY: "stick", SCENARIO_POSITION_G3: "traj", SCENARIO_STICK_G3: "stick"}
POSITION_SCENARIOS = (SCENARIO_POSITION_LEGACY, SCENARIO_POSITION_G3)  # position mode: the horizontal gates apply (keys 1 and 2)
END_SEGMENT = "hold"
OVERRIDES_NAME = "g3_scenario_overrides.json"
GNSS_MATCHED = False  # set by --override-gnss-matched (S191 probe): EKF GNSS delay compensation := drawn latency
RATE_HZ = 800
REQUIRE_ACTC = False  # --require-actc: a draw without the S211 `actc` block is refused
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
    # S121: the INDI rate module starts only from MC_RATE_CTL_TYPE 1 (run_scenario maps it to MC_INDI_EN at boot);
    # the airframe G1 file does not carry it, so every S112-S118 "indi" probe flew the stock rate loop.
    params = {"MC_RATE_CTL_TYPE": "1"} if CONTROLLER == "indi" else {}
    applied, not_applied, notes = {}, {}, {}
    argv = []

    # fixed set-up ------------------------------------------------------------------------------------------------
    mode = draw["mode"]
    hold = not LEGACY_SCENARIOS  # S214 scenarios: hold to the end, steady wind and final sag held
    if mode == "position":
        scenario = SCENARIO_POSITION_G3 if hold else SCENARIO_POSITION_LEGACY
        sched = ["--sched"]
        stick = []
    else:
        scenario = SCENARIO_STICK_G3 if hold else SCENARIO_STICK_LEGACY
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

    # controller ACT_TC (S211 Q28): the draw's value replaces the params-file value; draws without `actc` are unchanged
    ac = draw.get("actc")
    if ac is not None:
        want = g3_sample.actc_block(f, ac["actc_ratio"])  # re-derive from the drawn plant, refuse a stale value
        if abs(want["mc_indi_act_tc"] - ac["mc_indi_act_tc"]) > 2e-6 or abs(want["tau_mean"] - ac["tau_mean"]) > 1e-5:
            raise AssertionError(f"actc block does not match the drawn tau: {ac} vs {want}")
        params["MC_INDI_ACT_TC"] = ac["mc_indi_act_tc"]
        applied["actc"] = {**ac, "base_params_value": base.get("MC_INDI_ACT_TC"),
                           "via": "param MC_INDI_ACT_TC (replaces the params-file value)"}
    elif REQUIRE_ACTC:
        raise AssertionError("--require-actc: draw has no `actc` block")

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
                           "via": "--model-variant tau_up/tau_down" if ({"tau_up", "tau_down"} & mv_keys) else "nominal"}
    for k in ("tau_up", "tau_down"):
        applied[k] = {"value": f[k]["value"], "via": "--model-variant tau x " + k if k in mv_keys or "tau" in mv_keys else "nominal"}
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
        tf = f["tel_frozen"]
        ov["erpm_frozen"] = {"motor": int(tf["motor"]), "start": main_seg, "start_offset_s": tf["start_offset_s"],
                             "duration_s": tf["duration_s"]}
        applied["tel_frozen"] = {"motor": tf["motor"], "start": main_seg, "start_offset_s": tf["start_offset_s"],
                                 "duration_s": tf["duration_s"], "via": "scenario-overrides erpm_frozen (timed, sim time, SIM_GZ_ERPM_FRZ)"}
        notes["tel_frozen"] = (f"anchor = start of '{main_seg}': rpm frozen from +{tf['start_offset_s']} s for "
                               f"{tf['duration_s']} s (sim time), errorcount not incremented")
    else:
        applied["tel_frozen"] = {"on": False}

    # vibration ---------------------------------------------------------------------------------------------------
    vb = f["vibration"]
    # G4 typical profile goes underneath the drawn vibration (GATES G3 table): one rotor line, so the amplitudes add
    # (same rpm line, in phase: the conservative sum). UNVERIFIED choice, see g3_setup_s175/README.md.
    acc_tot, gyr_tot = TYPICAL_VIB_ACC + vb["acc_ms2"], TYPICAL_VIB_GYR + vb["gyr_rads"]
    argv += ["--vib-acc", _num(acc_tot), "--vib-gyr", _num(gyr_tot), "--imu-noise-scale", _num(TYPICAL_IMU_NSC)]
    applied["vibration"] = {"acc_ms2": vb["acc_ms2"], "gyr_rads": vb["gyr_rads"], "mult": vb["mult"],
                            "effective_acc_ms2": acc_tot, "effective_gyr_rads": gyr_tot}

    # GNSS --------------------------------------------------------------------------------------------------------------
    g = f["gnss"]
    argv += ["--gps-dly", str(int(g["latency_ms"]))]
    ekf_dly = g["latency_ms"] if GNSS_MATCHED else g["ekf_delay_ms"]   # S191 probe: --override-gnss-matched
    if ekf_dly is not None:
        argv += ["--gnss-delay", str(int(ekf_dly))]
    applied["gnss"] = {"latency_ms": g["latency_ms"], "ekf_delay_ms": ekf_dly, "drawn_ekf_delay_ms": g["ekf_delay_ms"]}

    # thrust: sag (ramp over the window), saturation (all motors step), weak motor (one motor step) -------------------------
    sg, sat, wk = f["thrust_sag"], f["saturation"], f["weak_motor"]
    if sg["on"]:
        if hold:  # S214: ramp fixed at the drawn length from the scenario start, then constant to the end
            ov["thrust_sag"] = {"scale": sg["scale"], "ramp_s": float(sg["ramp_s"])}
            applied["thrust_sag"] = {"scale": sg["scale"], "ramp_s": sg["ramp_s"],
                                     "via": "scenario-overrides thrust_sag ramp_s (linear ramp over the drawn length, then constant)"}
            notes["thrust_sag"] = f"ramp {sg['ramp_s']} s from the scenario start, final value held to the end (S214)"
        else:
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
        if hold:  # S214: steady wind to the scenario end (gust at +12 s of the main segment, ends before the hold)
            ov["wind"]["hold_to_end"] = True
        applied["wind"] = {"steady_ms": w["steady_ms"], "gust_peak_total_ms": w["gust_peak_total_ms"], "dir_deg": w["dir_deg"],
                           "via": f"scenario-overrides wind, profile starts at '{main_seg}'"}
        notes["wind"] = ("gust_x timing is fixed (2 s ramp, 10 s hold, 1 s gust, then steady) from the segment start; the drawn "
                         f"gust_offset_s {w.get('gust_offset_s')} is not used"
                         + ("; steady wind held to the scenario end (S214)" if hold else "; profile cleared at 28 s"))

    if ov:
        argv += ["--scenario-overrides", os.path.join(out_dir, OVERRIDES_NAME)]

    # G4 typical-noise profile ------------------------------------------------------------------------------------------
    applied["g4_typical_noise"] = {"vib_acc_ms2": TYPICAL_VIB_ACC, "vib_gyr_rads": TYPICAL_VIB_GYR,
                                   "imu_noise_scale": TYPICAL_IMU_NSC, "via": "run_scenario --vib-acc/--vib-gyr/--imu-noise-scale"}

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


def unapplied(draws, base_params_path, out_root="/nonexistent"):
    """{run_index: not_applied dict} for every draw that has a declared factor the runner cannot apply."""
    bad = {}
    for d in draws:
        na = build_run(d, base_params_path, os.path.join(out_root, f"run_{d['run_index']:03d}"))["not_applied"]
        if na:
            bad[d["run_index"]] = na
    return bad


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


def check_validity(out):
    """run_validity.check_run on out/flight.ulg with the params the runner wrote (g3_params.txt); None if no ulog."""
    ulg, pp = os.path.join(out, "flight.ulg"), os.path.join(out, "g3_params.txt")
    if not os.path.exists(ulg):
        return None
    if not os.path.exists(pp):  # K122 #2: requested params unknown -> cannot verify -> fail closed
        return {"valid": False, "problems": ["g3_params.txt missing, requested params cannot be checked"], "checked": {}}
    return run_validity.check_run(ulg, read_params(pp), CONTROLLER, expected_rate_hz=RATE_HZ)


def finalize(out, status, extra=None):
    """Record the outcome in g3_done.json (and in run.json as g3_outcome). An aborted run is a finished FAILURE: it gets
    the done marker (outcome 'aborted', not retried, counted as a failure by the campaign). Only an incomplete run
    (timeout, no run.json) gets g3_failed.json and no done marker, so it is retried on the next invocation."""
    outcome, rj = classify(out, status)
    status["outcome"] = outcome
    try:
        validity = check_validity(out)
    except Exception as e:  # noqa: BLE001  K122 #3: an unverifiable run must not pass or lose its outcome
        validity = {"valid": False, "problems": [f"check_validity raised {type(e).__name__}: {e}"], "checked": {}}
    if validity is not None:
        status["validity"] = validity
        if not validity["valid"] and outcome in ("ok", "aborted"):
            outcome = status["outcome"] = "void"  # flew the wrong controller / wrong params: not a usable run
    if outcome == "aborted":
        status["error"] = rj.get("error")
        status["watchdog"] = rj.get("watchdog")
        status["metrics_status"] = rj.get("metrics_status")
    if rj is not None:
        rj["g3_outcome"] = outcome
        if extra:
            rj.update(extra)
        with open(os.path.join(out, "run.json"), "w") as fh:
            json.dump(rj, fh, indent=1)
    if outcome in ("ok", "aborted", "void"):
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
    ap.add_argument("--override-gnss-matched", action="store_true",
                    help="probe: set --gnss-delay equal to the drawn GNSS latency (all other factors unchanged)")
    ap.add_argument("--speed", type=float, default=1.0,
                    help="sim speed factor passed to run_scenario.py --speed (1.0: not passed, argv unchanged)")
    ap.add_argument("--samples", help="directory of run_NNN.json draws (g3_sample.py refly) instead of the seed's campaign")
    ap.add_argument("--legacy-scenarios", action="store_true",
                    help="pre-S214 stand-in scenarios (o1_lemniscate / stick_zsine_o6, 3 s hold, wind cleared at 28 s, sag over the window)")
    ap.add_argument("--require-actc", action="store_true", help="refuse a draw without the S211 `actc` block")
    a = ap.parse_args()
    global GNSS_MATCHED, REQUIRE_ACTC, LEGACY_SCENARIOS
    LEGACY_SCENARIOS = a.legacy_scenarios
    GNSS_MATCHED = a.override_gnss_matched
    REQUIRE_ACTC = a.require_actc

    draws = g3_sample.load_samples(a.samples, a.seed, a.n) if a.samples else g3_sample.campaign(a.seed, a.n)
    sel = [d for d in draws if d["run_index"] >= a.start and (a.stop is None or d["run_index"] <= a.stop)]
    bad = unapplied(sel, a.base_params, a.out_root)
    if bad:  # set-up fault: abort before anything is flown or written
        for i, na in sorted(bad.items()):
            print(f"ABORT run_{i:03d}: declared factor(s) not applicable: {na}", file=sys.stderr)
        print("g3_run: refusing to fly, a declared plant/noise factor would be not_applied", file=sys.stderr)
        sys.exit(3)
    for d in sel:
        out = os.path.join(a.out_root, f"run_{d['run_index']:03d}")
        r = build_run(d, a.base_params, out)
        if a.speed != 1.0:
            r["argv"] += ["--speed", _num(a.speed)]
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
        extra = {"g3_actc_applied": r["applied"]["actc"]} if "actc" in r["applied"] else None
        finalize(out, status, extra)
        print(f"run_{d['run_index']:03d}: {status}", flush=True)


if __name__ == "__main__":
    main()
