"""S180 item 3 on cruise_typ_s1: freeze-7 INDI, GP (XY_P 1.2) INDI, PID reference. Same keyed call as rescore_s175.py (window = last 10 s of the 'traj' event on the run.json clock). Docker, repo root."""
import json, subprocess, sys, numpy as np
sys.path.insert(0, "indi_flight/bench"); import g3_checks as k1
R = "indi_flight/results"; OUT = f"{R}/g55_gain_probe_s179/pid_ref_s180"
runs = {"freeze7 INDI": f"{R}/freeze7_s177/g4/cruise_typ_s1", "GP INDI": f"{R}/g55_gain_probe_s179/score/cruise_typ_s1", "PID ref": f"{R}/g4_gate_s169/pid_cruise_typ_s1"}
for k, d in runs.items():
    e = {x["name"]: x for x in json.load(open(f"{d}/run.json"))["events"]}["traj"]; end = e["t_us"]*1e-6 + e["dur_s"]
    oj = f"{OUT}/item3_{k.split()[0]}_{k.split()[1]}.json"
    subprocess.run(["python3", "indi_flight/bench/g3_checks.py", f"{d}/flight.ulg", "--t0", str(end-10), "--t1", str(end), "--skip-nav-change", "--json", oj], capture_output=True, text=True)
    j = json.load(open(oj)); i = j["item3_steady_state"]
    tt, pos, q, w, tm, cmd, ref, src, t_land, navc = k1.load(f"{d}/flight.ulg", end-10, end)
    h = -pos[:, 2]; h -= h[0]; m = (tt >= end-10) & (tt <= end)
    print(f"{k}: window {end-10:.1f}-{end:.1f} ref_z(NED) {ref[2]:.3f} horiz {i['horizontal_rms_m']['value']:.3f} alt_mean {i['altitude_mean_m']['value']:.3f} pass {i['pass']} item1 {j['item1_loc']['pass']}")
    print(f"   nav changes (log s) {[round(x,1) for x in navc]} t_land {t_land}; truth h in window mean {h[m].mean():.2f} min {h[m].min():.2f} max {h[m].max():.2f}; setpoint z {-ref[2]:.2f}")
    print(f"   h at t=30,40,50,55,60,65,70,75: {[round(float(np.interp(t, tt, h)),2) for t in (30,40,50,55,60,65,70,75)]}")
