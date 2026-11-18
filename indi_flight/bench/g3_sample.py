#!/usr/bin/env python3
"""G3 robustness campaign sampler (GATES.md "3. G3 Robustness campaign", S94 decisions).

    python3 bench/g3_sample.py campaign MASTER_SEED --n 300 --out DIR
    python3 bench/g3_sample.py pretest  MASTER_SEED --out DIR

Writes run_000.json ... and index.json. Pure stdlib, deterministic: same master seed -> byte-identical files.
Design notes and the factor -> hook map: design/g3_sampler_s108.md. No hook is applied here; each run JSON carries a
`hooks` block naming the bench flag / model_variant key / PX4 param that applies each factor today (status per factor).

Every factor is decoded from a unit-cube coordinate `u[dim]`. LHS runs take u from a Latin hypercube (one point per
stratum per dimension), corner runs from independent uniform draws with the named factors pinned, pretest extreme runs
from a nominal point with one factor pinned.
"""
import argparse
import hashlib
import json
import math
import os
import random

SCHEMA = 1
FLIGHT_S = 100.0
# nominal flight timeline (PROPOSED in GATES): take-off ~, hover 25, step_roll, lemniscate 30, hold 20 at the end.
HOLD_S = 20.0
HOLD_START_NOMINAL_S = FLIGHT_S - HOLD_S

# ranges (owner floors) -------------------------------------------------------------------------------------------
G1_ERR = (0.5, 2.0)          # realised controller G1 / plant G1, log-uniform, per axis (ctrl mult = e / I_scale)
TAU = (0.5, 3.0)             # log-uniform, x nominal
ASYM = (1.0, 3.0)            # tau_down / tau_up, log-uniform; inverted: (1/3, 1)
ASYM_INV_FRAC = 0.10         # widening
DELAY_STEP_MS, DELAY_STEPS = 1.25, 9          # 0 .. 10 ms
MASS = (0.7, 1.3)
INERTIA = (0.7, 1.3)
SAG_FRAC, SAG = 0.40, (0.7, 1.0)
SAG_RAMP_S = 10.0
WEAK_FRAC, WEAK = 0.30, (0.7, 1.0)
SAT_HOVER_MARGIN = 2.0       # available thrust = 2.0 x hover thrust of the drawn mass
SAT_SCALE_NOMINAL_MASS = 0.27  # spec: "scale about 0.27 on nominal mass"
TEL_LAT = (0, 3)             # frames
DROP_FRAC, DROP = 0.40, (0.0, 0.20)
LOSS_FRAC, LOSS_S = 0.20, 2.0
FROZEN_FRAC, FROZEN_S = 0.20, 1.0
VIB = (1.0, 5.0)             # x the x1 point
VIB_X1_ACC, VIB_X1_GYR = 1.0, 0.05   # m/s^2, rad/s per rotor (provisional, decision 1)
GNSS_LAT = (80, 250)         # ms, integer ms so that "matched" is exact
GNSS_MATCH_FRAC = 0.50
GNSS_MISMATCH = (-100, 100)  # ms around the latency, min 0
WIND = (0.0, 5.0)            # steady m/s
GUST_PEAK = (3.0, 9.0)       # m/s, peak TOTAL wind (steady + gust), 9 m/s = 10 % W
MODE_MIX = (("position", 0.70), ("stabilized", 0.20), ("acro", 0.10))
# event timing: ALL offsets are s after the ANCHOR = start of the runner's main segment (traj / stick); S111 single anchor.
# (was: inside the hold segment (s after hold start): gust at the start, telemetry faults start in [1, 5]
GUST_OFFSET_S = 0.0
FAULT_START = (1.0, 5.0)

CORNER_FRAC = 0.20
# corner pins: dim -> u value (0 or 1 end of the range). Flags are 'on' for u=0 (u < fraction), see decode().
CORNERS = {
    "C1": {"g1_r": 1, "g1_p": 1, "g1_y": 1, "tau": 1, "delay": 1},
    "C2": {"g1_r": 0, "g1_p": 0, "g1_y": 0, "mass": 1, "sag_on": 0, "sag": 0, "ix": 1, "iy": 1, "iz": 1},
    "C3": {"sat_on": 0, "gust_pk": 1, "mass": 1},
    "C4": {"gnss_lat": 1, "gnss_match": 1, "gnss_off": 0, "wind_s": 1, "g1_r": 1, "g1_p": 1, "g1_y": 1},
    "C5": {"vib": 1, "frz_on": 0, "drop_on": 0, "drop": 1, "tau": 0},
    "C6": {"weak_on": 0, "weak": 0, "tau": 1, "delay": 1},
}
# pretest: one extreme per injector group (15 runs) + 5 sampled. Extreme = the end the corners use.
PRETEST_EXTREMES = {
    "x_g1": {"g1_r": 1, "g1_p": 1, "g1_y": 1},
    "x_tau": {"tau": 1},
    "x_asym": {"asym": 1, "asym_inv": 1},          # asym_inv u=1 -> not inverted, ratio 3
    "x_delay": {"delay": 1},
    "x_mass": {"mass": 1},
    "x_inertia": {"ix": 1, "iy": 1, "iz": 1},
    "x_sag": {"sag_on": 0, "sag": 0},
    "x_weak": {"weak_on": 0, "weak": 0},
    "x_saturation": {"sat_on": 0},
    "x_tel_lat_drop": {"lat": 1, "drop_on": 0, "drop": 1},
    "x_tel_loss": {"loss_on": 0},
    "x_tel_frozen": {"frz_on": 0},
    "x_vib": {"vib": 1},
    "x_gnss": {"gnss_lat": 1, "gnss_match": 1, "gnss_off": 0},
    "x_wind": {"wind_s": 1, "gust_pk": 1},
}
# the nominal point: everything absent / x1; mode position
NOMINAL_U = {
    "g1_r": None, "g1_p": None, "g1_y": None, "tau": None, "asym": 0.0, "asym_inv": 1.0, "delay": 0.0,
    "mass": None, "ix": None, "iy": None, "iz": None, "sag_on": 1.0, "sag": 1.0, "weak_on": 1.0, "weak": 1.0,
    "weak_motor": 0.0, "sat_on": 1.0, "lat": 0.0, "drop_on": 1.0, "drop": 0.0, "loss_on": 1.0, "loss_motor": 0.0,
    "loss_t": 0.0, "frz_on": 1.0, "frz_motor": 0.0, "frz_t": 0.0, "vib": 0.0, "gnss_lat": 0.0,
    "gnss_match": 0.0, "gnss_off": 0.5, "wind_s": 0.0, "wind_dir": 0.0, "gust_pk": 0.0, "mode": 0.0,
}
DIMS = sorted(NOMINAL_U)
# sat_on is never drawn: the saturation corner is set only by the C3 pin (sat_on = 0), see decode()
DIMS_FREE = [d for d in DIMS if d != "sat_on"]


def _nominal_u():
    u = dict(NOMINAL_U)
    for k in ("g1_r", "g1_p", "g1_y"):
        u[k] = 0.5          # log-uniform [0.5, 2]: u=0.5 -> 1.0
    u["tau"] = math.log(1.0 / TAU[0]) / math.log(TAU[1] / TAU[0])   # tau x1
    for k in ("mass", "ix", "iy", "iz"):
        u[k] = 0.5
    # gust nominal = none: handled by decode (gust_pk u=0 gives 3 m/s), so nominal runs use `no_wind`
    return u


# ---------------------------------------------------------------------------------------------------------------
def lin(u, lo, hi):
    return lo if u <= 0 else hi if u >= 1 else lo + u * (hi - lo)


def logu(u, lo, hi):
    return lo if u <= 0 else hi if u >= 1 else min(hi, max(lo, lo * math.exp(u * math.log(hi / lo))))


def pick(u, n):
    return min(n - 1, max(0, int(u * n)))


def r6(x):
    return round(float(x), 6)


def digest_int(*parts, bits=63):
    h = hashlib.sha256(":".join(str(p) for p in parts).encode()).digest()
    return int.from_bytes(h[:8], "big") >> (64 - bits)


def decode(u, no_wind=False, no_gnss=False):
    """Unit-cube point -> factor dict in physical units (with nominals)."""
    f = {}
    # M4 (D-G3-SAMPLER-K108): the drawn e is the realised controller/plant G1 ratio. The plant rate-loop G1 scales as
    # 1/I_scale per axis, so the controller G1 multiplier written to the run is k = e / I_scale (k * I_scale = e).
    isc = {"roll": r6(lin(u["ix"], *INERTIA)), "pitch": r6(lin(u["iy"], *INERTIA)), "yaw": r6(lin(u["iz"], *INERTIA))}
    e = {"roll": r6(logu(u["g1_r"], *G1_ERR)), "pitch": r6(logu(u["g1_p"], *G1_ERR)), "yaw": r6(logu(u["g1_y"], *G1_ERR))}
    f["g1_err"] = {**e, "nominal": 1.0, "unit": "e = realised controller G1 / plant G1 (alias of g1_ratio)"}
    f["g1_ratio"] = {**e, "nominal": 1.0, "unit": "e, log-uniform [0.5, 2], controller G1 / plant G1"}
    f["g1_ctrl_mult"] = {**{a: r6(e[a] / isc[a]) for a in e}, "i_scale": isc, "nominal": 1.0,
                         "unit": "k = e / I_scale(axis): multiplier on nominal controller G1 (plant G1 ~ G1_nom / I_scale)"}
    tau = logu(u["tau"], *TAU)
    f["tau_scale"] = {"value": r6(tau), "nominal": 1.0, "unit": "x nominal motor tau (up and down)"}
    inv = u["asym_inv"] < ASYM_INV_FRAC
    ratio = logu(u["asym"], *ASYM)
    if inv:
        ratio = 1.0 / ratio                      # [1/3, 1]
    f["tau_asym"] = {"value": r6(ratio), "inverted": bool(inv), "nominal": 1.0, "unit": "tau_down / tau_up"}
    k = pick(u["delay"], DELAY_STEPS)
    d = k * DELAY_STEP_MS
    f["loop_delay"] = {"total_ms": r6(d), "act_ms": r6(d / 2), "imu_ms": r6(d / 2), "steps": k, "nominal": 0.0,
                       "unit": "ms, 1.25 ms steps, 50 % actuator path / 50 % IMU path"}
    f["mass_scale"] = {"value": r6(lin(u["mass"], *MASS)), "nominal": 1.0, "unit": "x nominal mass"}
    f["inertia_scale"] = {"ixx": r6(lin(u["ix"], *INERTIA)), "iyy": r6(lin(u["iy"], *INERTIA)),
                          "izz": r6(lin(u["iz"], *INERTIA)), "nominal": 1.0, "unit": "x nominal diag inertia"}
    mass = f["mass_scale"]["value"]
    sat = u["sat_on"] <= 0.0          # only the C3 pin (and the pretest extreme) sets it
    sag_on = u["sag_on"] < SAG_FRAC
    f["thrust_sag"] = {"on": bool(sag_on and not sat), "scale": r6(lin(u["sag"], *SAG)) if (sag_on and not sat) else 1.0,
                       "ramp_s": SAG_RAMP_S, "nominal": 1.0, "unit": "available thrust scale, uniform, all motors"}
    f["saturation"] = {"on": bool(sat), "scale": r6(SAT_SCALE_NOMINAL_MASS * mass) if sat else 1.0,
                       "hover_margin": SAT_HOVER_MARGIN, "nominal": 1.0,
                       "unit": "available thrust scale = 0.27 x mass_scale (2.0 x hover thrust); replaces sag"}
    if sat:
        f["thrust_sag"] = {"on": False, "scale": 1.0, "ramp_s": SAG_RAMP_S, "nominal": 1.0,
                           "unit": "replaced by saturation"}
    weak_on = u["weak_on"] < WEAK_FRAC
    f["weak_motor"] = {"on": bool(weak_on), "motor": pick(u["weak_motor"], 4),
                       "scale": r6(lin(u["weak"], *WEAK)) if weak_on else 1.0, "nominal": 1.0,
                       "unit": "one motor available thrust scale"}
    f["tel_latency"] = {"frames": pick(u["lat"], TEL_LAT[1] + 1), "nominal": 0, "unit": "eRPM frames"}
    drop_on = u["drop_on"] < DROP_FRAC
    f["tel_dropout"] = {"on": bool(drop_on), "prob": r6(lin(u["drop"], *DROP)) if drop_on else 0.0, "nominal": 0.0,
                        "unit": "probability of a dropped eRPM frame, whole flight"}
    loss_on = u["loss_on"] < LOSS_FRAC
    f["tel_loss"] = {"on": bool(loss_on), "motor": pick(u["loss_motor"], 4), "duration_s": LOSS_S,
                     "start_offset_s": r6(lin(u["loss_t"], *FAULT_START)) if loss_on else None,
                     "nominal": None, "unit": "s after anchor (main-segment start); total eRPM loss on one motor"}
    frz_on = u["frz_on"] < FROZEN_FRAC
    f["tel_frozen"] = {"on": bool(frz_on), "motor": pick(u["frz_motor"], 4), "duration_s": FROZEN_S,
                       "start_offset_s": r6(lin(u["frz_t"], *FAULT_START)) if frz_on else None,
                       "nominal": None, "unit": "s after anchor (main-segment start); rpm bit-identical for 1 s on one motor"}
    vm = logu(u["vib"], *VIB)
    f["vibration"] = {"mult": r6(vm), "acc_ms2": r6(VIB_X1_ACC * vm), "gyr_rads": r6(VIB_X1_GYR * vm),
                      "x1_point": {"acc_ms2": VIB_X1_ACC, "gyr_rads": VIB_X1_GYR, "status": "provisional (S94 dec. 1)"},
                      "nominal": 1.0, "unit": "x the x1 point per rotor"}
    lat = int(round(lin(u["gnss_lat"], *GNSS_LAT)))
    matched = u["gnss_match"] < GNSS_MATCH_FRAC
    off = int(round(lin(u["gnss_off"], *GNSS_MISMATCH)))
    ekf = lat if matched else max(0, lat + off)
    if no_gnss:
        lat, matched, off, ekf = 0, True, 0, None
    f["gnss"] = {"latency_ms": lat, "matched": bool(matched), "ekf_delay_ms": ekf,
                 "mismatch_offset_ms": 0 if matched else off, "nominal": 0, "unit": "ms (SENS_GNSS0_DELAY = ekf_delay_ms; None = stock)"}
    if no_wind:
        f["wind"] = {"steady_ms": 0.0, "dir_deg": 0.0, "gust_peak_total_ms": 0.0, "gust_amp_ms": 0.0,
                     "gust_offset_s": None, "nominal": 0.0, "unit": "m/s, direction = where the air moves to"}
    else:
        # M2 (D-G3-SAMPLER-K108): peak U[3, 9] total, then steady U[0, min(5, peak - 1)] -> gust amp >= 1, peak <= 9.
        # Corner C4 pins wind_s = 1.0 (never produced by a free draw): steady 5, peak U[6, 9].
        if u["wind_s"] >= 1.0:
            pk, s = lin(u["gust_pk"], 6.0, GUST_PEAK[1]), WIND[1]
        else:
            pk = lin(u["gust_pk"], *GUST_PEAK)
            s = lin(u["wind_s"], WIND[0], min(WIND[1], pk - 1.0))
        f["wind"] = {"steady_ms": r6(s), "dir_deg": r6(lin(u["wind_dir"], 0.0, 360.0)),
                     "gust_peak_total_ms": r6(pk), "gust_amp_ms": r6(pk - s),
                     "gust_offset_s": GUST_OFFSET_S, "nominal": 0.0,
                     "unit": "m/s, direction = where the air moves to; gust added on the steady wind"}
    acc, mode = 0.0, MODE_MIX[-1][0]
    for name, p in MODE_MIX:
        acc += p
        if u["mode"] < acc - 1e-12:
            mode = name
            break
    return f, mode


# hooks ---------------------------------------------------------------------------------------------------------
def hooks_for(f, gz_seed):
    """How today's bench applies each factor (status keys EXISTS/PARTIAL/MISSING are in design/g3_sampler_s108.md)."""
    g = f["gnss"]
    ld = f["loop_delay"]
    vm = f["vibration"]
    h = {
        "run_scenario_args": {
            "--model": "quad5in", "--sim": "v2", "--sim-seed": gz_seed,
            "--dly-act": ld["act_ms"], "--dly-imu": ld["imu_ms"],
            "--gps-dly": g["latency_ms"], "--gnss-delay": g["ekf_delay_ms"],
            "--vib-acc": vm["acc_ms2"], "--vib-gyr": vm["gyr_rads"],
            "--erpm-drop": f["tel_dropout"]["prob"],
            "--imu-noise-scale": None,   # placeholder, see g4_typical_noise
        },
        "px4_params": {
            "MC_INDI_G1_R": {"x_nominal": f["g1_ctrl_mult"]["roll"]},
            "MC_INDI_G1_P": {"x_nominal": f["g1_ctrl_mult"]["pitch"]},
            "MC_INDI_G1_Y": {"x_nominal": f["g1_ctrl_mult"]["yaw"]},
            "SIM_GZ_ERPM_LAT": f["tel_latency"]["frames"],
        },
        "model_variant": {"tau": f["tau_scale"]["value"], "tau_up": 1.0, "tau_down": f["tau_asym"]["value"],
                          "mass": f["mass_scale"]["value"], "ixx": f["inertia_scale"]["ixx"],
                          "iyy": f["inertia_scale"]["iyy"], "izz": f["inertia_scale"]["izz"]},
        "timed": [],
        "disturbance": {"profile": "gust_x (needs parametrised steady/peak/direction)", "steady_ms": f["wind"]["steady_ms"],
                        "gust_amp_ms": f["wind"]["gust_amp_ms"], "dir_deg": f["wind"]["dir_deg"],
                        "start": "anchor (main-segment start); gust_offset_s not used (fixed profile timing)"},
    }
    sag = f["thrust_sag"] if f["thrust_sag"]["on"] else f["saturation"]
    if sag["on"]:
        h["timed"].append({"hook": "SIM_GZ_THR_SC", "ramp_to": sag["scale"], "ramp_s": SAG_RAMP_S, "t0": "anchor (main-segment start)"})
    w = f["weak_motor"]
    if w["on"]:
        h["timed"].append({"hook": "SIM_GZ_EC_MAX{motor+1} scaled (motor_fault)", "motor": w["motor"], "thrust_scale": w["scale"],
                           "t0": "anchor (main-segment start)"})
    for key, p in (("tel_loss", "SIM_GZ_ERPM_LOSS bit"), ("tel_frozen", "frozen rpm (no hook)")):
        e = f[key]
        if e["on"]:
            h["timed"].append({"hook": p, "motor": e["motor"], "t_after_anchor_s": e["start_offset_s"],
                               "duration_s": e["duration_s"]})
    return h


# sampling ------------------------------------------------------------------------------------------------------
def lhs_points(rng, n, dims):
    # sat_on is added back as the constant 1.0 (off)
    """One point per stratum per dimension, independent permutation per dimension."""
    cols = {}
    for d in dims:
        perm = list(range(n))
        rng.shuffle(perm)
        cols[d] = [(perm[i] + rng.random()) / n for i in range(n)]
    return [{**{d: cols[d][i] for d in dims}, "sat_on": 1.0} for i in range(n)]


def free_point(rng, dims):
    return {**{d: rng.random() for d in dims}, "sat_on": 1.0}


def split_counts(n):
    n_corner = int(round(CORNER_FRAC * n))
    base, rem = divmod(n_corner, len(CORNERS))
    per = {c: base + (1 if i < rem else 0) for i, c in enumerate(CORNERS)}
    return n - n_corner, per


def make_run(master, idx, kind, u, extra=None, no_wind=False, no_gnss=False):
    seed = digest_int("g3", master, "run", idx)
    gz_seed = 1 + digest_int("g3", master, "gz", idx, bits=30)
    f, mode = decode(u, no_wind=no_wind, no_gnss=no_gnss)
    run = {"schema": SCHEMA, "master_seed": master, "run_index": idx, "kind": kind, "sampler_seed": seed,
           "gz_seed": gz_seed, "airframe": "quad5in", "flight_s": FLIGHT_S, "mode": mode,
           "timeline": {"hold_start_nominal_s": HOLD_START_NOMINAL_S, "hold_s": HOLD_S,
                        "note": "event offsets are seconds after the hold segment starts"},
           "factors": f, "g4_typical_noise": {"profile": None, "status": "placeholder: G4 typical profile does not exist yet"},
           "hooks": hooks_for(f, gz_seed)}
    if extra:
        run.update(extra)
    return run


def campaign(master, n):
    n_lhs, per = split_counts(n)
    runs, idx = [], 0
    rng = random.Random(digest_int("g3", master, "lhs"))
    for u in lhs_points(rng, n_lhs, DIMS_FREE):
        runs.append(make_run(master, idx, "lhs", u))
        idx += 1
    crng = random.Random(digest_int("g3", master, "corners"))
    for c, cnt in per.items():
        for j in range(cnt):
            u = free_point(crng, DIMS_FREE)
            u.update({k: float(v) for k, v in CORNERS[c].items()})
            runs.append(make_run(master, idx, f"corner {c}", u, {"corner": c, "pins": CORNERS[c]}))
            idx += 1
    return runs


def pretest(master):
    runs, idx = [], 0
    for name, pins in PRETEST_EXTREMES.items():
        u = _nominal_u()
        u.update({k: float(v) for k, v in pins.items()})
        runs.append(make_run(master, idx, f"pretest {name}", u, {"pins": pins}, no_wind=(name != "x_wind"),
                              no_gnss=(name != "x_gnss")))
        idx += 1
    rng = random.Random(digest_int("g3", master, "pretest_lhs"))
    for u in lhs_points(rng, 5, DIMS_FREE):
        runs.append(make_run(master, idx, "pretest sampled", u))
        idx += 1
    return runs


def write(runs, out, master, what):
    os.makedirs(out, exist_ok=True)
    index = {"schema": SCHEMA, "what": what, "master_seed": master, "n": len(runs), "runs": []}
    for r in runs:
        name = f"run_{r['run_index']:03d}.json"
        with open(os.path.join(out, name), "w") as fh:
            fh.write(json.dumps(r, indent=1, sort_keys=True) + "\n")
        index["runs"].append({"file": name, "run_index": r["run_index"], "kind": r["kind"], "sampler_seed": r["sampler_seed"],
                              "gz_seed": r["gz_seed"], "mode": r["mode"]})
    with open(os.path.join(out, "index.json"), "w") as fh:
        fh.write(json.dumps(index, indent=1, sort_keys=True) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("what", choices=("campaign", "pretest"))
    ap.add_argument("master_seed", type=int)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    runs = campaign(a.master_seed, a.n) if a.what == "campaign" else pretest(a.master_seed)
    write(runs, a.out, a.master_seed, a.what)
    print(f"{a.what}: {len(runs)} runs -> {a.out}")


if __name__ == "__main__":
    main()
