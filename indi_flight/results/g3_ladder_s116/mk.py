import json, sys
sys.path.insert(0, "/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/bench")
import scenario_overrides as so
out = "/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/g3_ladder_s116"
try:
    import scenarios as S
    sc = S.SCENARIOS["stick_zsine_o6"]
except Exception as e:
    print("scenarios import failed:", repr(e)[:200]); sc = None
ov = {
 "3_sag07": {"thrust_sag": {"scale": 0.7}},
 "4_wind5": {"wind": {"steady": 5, "peak": 7, "dir_deg": 45}, "disturbance": "gust_x", "dist_segment": "stick"},
 "5_erpmloss": {"erpm_loss": {"motor": 0, "start": "stick", "start_offset_s": 5.0, "duration_s": 2.0}},
 "6_weak08": {"motor_fault": {"segment": "stick", "motor": 1, "thrust_scale": 0.8}},
 "7_sat": {"motor_fault": {"segment": "stick", "motor": 1, "thrust_scale": 0.35}},
}
for k, v in ov.items():
    name = k.split("_",1)[1] if False else None
for name, v in {"sag07": ov["3_sag07"], "wind5": ov["4_wind5"], "erpmloss": ov["5_erpmloss"], "weak08": ov["6_weak08"], "sat": ov["7_sat"]}.items():
    try:
        if sc is not None:
            merged = dict(sc); merged.update(v)
            so.validate(merged, v)
        print(name, "validate OK")
    except Exception as e:
        print(name, "REJECT", repr(e)[:200])
    json.dump(v, open(f"{out}/{name}.json", "w"), indent=1)
