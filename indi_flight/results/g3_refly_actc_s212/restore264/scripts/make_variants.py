#!/usr/bin/env python3
"""Per-factor restoration copies of the S212 samples dir: only run_024.json (draw 264) differs, one factor to nominal.
Usage: make_variants.py <samples_src> <out_root> [NAME...].  Nominal values = the factor's own "nominal" field in the draw
(g3_sample.py decode), g1: e=1 (controller G1 = plant G1, k = 1/I_scale), inertia: 1, ACT_TC: 0.033 (ACTC_NOMINAL_S)."""
import copy, json, os, shutil, sys
src, out = sys.argv[1:3]
d0 = json.load(open(os.path.join(src, "run_024.json")))
assert d0["source_run"] == 264


def r6(x):
    return round(x, 6)


def v_sat(d):
    d["factors"]["saturation"].update(on=False, scale=1.0)
    d["hooks"]["timed"] = [t for t in d["hooks"]["timed"] if t["hook"] != "SIM_GZ_THR_SC"]


def v_weak(d):
    d["factors"]["weak_motor"].update(on=False, scale=1.0)
    d["hooks"]["timed"] = [t for t in d["hooks"]["timed"] if not t["hook"].startswith("SIM_GZ_EC_MAX")]


def _mv(d, **kw):
    d["hooks"]["model_variant"].update(kw)


def _set_actc(d, val):
    f = d["factors"]
    tm = (f["tau_up"]["value"] + f["tau_down"]["value"]) / 2
    d["actc"] = {"actc_ratio": r6(val / (tm * 0.033)), "tau_mean": r6(tm), "mc_indi_act_tc": val}


def v_tau(d):  # plant motor tau up/down -> 1; ACT_TC param kept at the drawn value
    f = d["factors"]
    keep = d["actc"]["mc_indi_act_tc"]
    for k in ("tau_up", "tau_down", "tau_scale"):
        f[k]["value"] = 1.0
    f["tau_asym"].update(value=1.0, drawn_ratio=1.0)
    _mv(d, tau=1.0, tau_up=1.0, tau_down=1.0)
    _set_actc(d, keep)


def v_actc(d):  # controller ACT_TC -> 0.033 (nominal); plant as drawn
    _set_actc(d, 0.033)


def v_delay(d):
    d["factors"]["loop_delay"].update(act_ms=0.0, imu_ms=0.0, total_ms=0.0, steps=0)
    d["hooks"]["run_scenario_args"].update({"--dly-act": 0.0, "--dly-imu": 0.0})


def v_tel(d):
    d["factors"]["tel_latency"]["frames"] = 0
    d["hooks"]["px4_params"]["SIM_GZ_ERPM_LAT"] = 0


def _g1(d, mult):
    g = d["factors"]["g1_ctrl_mult"]
    for ax in ("roll", "pitch", "yaw"):
        g[ax] = r6(mult[ax])
    for ax, nm in (("roll", "MC_INDI_G1_R"), ("pitch", "MC_INDI_G1_P"), ("yaw", "MC_INDI_G1_Y")):
        d["hooks"]["px4_params"][nm]["x_nominal"] = r6(mult[ax])


def v_g1(d):  # e = 1 with the drawn inertia: k = 1/I_scale
    s = d["factors"]["g1_ctrl_mult"]["i_scale"]
    for k in ("g1_err", "g1_ratio"):
        for ax in ("roll", "pitch", "yaw"):
            d["factors"][k][ax] = 1.0
    _g1(d, {ax: 1.0 / s[ax] for ax in s})


def v_inertia(d):  # plant inertia nominal, drawn e kept: k = e
    f = d["factors"]
    e = dict(f["g1_err"])
    for ax in ("ixx", "iyy", "izz"):
        f["inertia_scale"][ax] = 1.0
    for ax in f["g1_ctrl_mult"]["i_scale"]:
        f["g1_ctrl_mult"]["i_scale"][ax] = 1.0
    _g1(d, {ax: e[ax] for ax in ("roll", "pitch", "yaw")})
    _mv(d, ixx=1.0, iyy=1.0, izz=1.0)


def v_mass(d):
    d["factors"]["mass_scale"]["value"] = 1.0
    _mv(d, mass=1.0)   # saturation scale 0.351 (= 0.27 x 1.3) is left as drawn


def v_vib(d):
    d["factors"]["vibration"].update(acc_ms2=1.0, gyr_rads=0.05, mult=1.0)
    d["hooks"]["run_scenario_args"].update({"--vib-acc": 1.0, "--vib-gyr": 0.05})


def v_wind(d):
    d["factors"]["wind"].update(steady_ms=0.0, gust_amp_ms=0.0, gust_peak_total_ms=0.0)
    d["hooks"]["disturbance"].update(steady_ms=0.0, gust_amp_ms=0.0)


def v_gnss(d):
    d["factors"]["gnss"].update(latency_ms=0, ekf_delay_ms=0, mismatch_offset_ms=0, matched=True)
    d["hooks"]["run_scenario_args"].update({"--gps-dly": 0, "--gnss-delay": 0})


def v_joint(d):  # every factor nominal EXCEPT saturation and weak_motor (kept as drawn)
    for fn in (v_tau, v_actc, v_delay, v_tel, v_inertia, v_g1, v_mass, v_vib, v_wind, v_gnss):
        fn(d)


V = dict(sat=v_sat, weak=v_weak, tau=v_tau, actc=v_actc, delay=v_delay, tel=v_tel, g1=v_g1, inertia=v_inertia,
         mass=v_mass, vib=v_vib, wind=v_wind, gnss=v_gnss, joint=v_joint)
for name, fn in V.items():
    if sys.argv[3:] and name not in sys.argv[3:]:
        continue
    dst = os.path.join(out, "samples_" + name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    d = copy.deepcopy(d0)
    fn(d)
    json.dump(d, open(os.path.join(dst, "run_024.json"), "w"), indent=1, sort_keys=True)
    ix = json.load(open(os.path.join(dst, "index.json")))
    ix["runs"][24]["mc_indi_act_tc"] = d["actc"]["mc_indi_act_tc"]
    json.dump(ix, open(os.path.join(dst, "index.json"), "w"), indent=1, sort_keys=True)
    print(name, "ok")
