"""S117 probe: one line per run (idx, mode, kind, key factors, outcome) + counts. Usage: python3 summary.py > summary.txt"""
import glob, json, os, collections
here = os.path.dirname(os.path.abspath(__file__))
cnt = collections.Counter()
for d in sorted(glob.glob(os.path.join(here, "run_*"))):
    try:
        g = json.load(open(os.path.join(d, "g3_draw.json")))["draw"]
    except (OSError, ValueError):
        continue
    f = g["factors"]
    done = os.path.join(d, "g3_done.json")
    out = json.load(open(done)) if os.path.exists(done) else {"outcome": "running"}
    o = out.get("outcome")
    if g["mode"] == "acro" and o != "ok":
        o = o + "(scenario-invalid)"
    cnt[(g["mode"], o)] += 1
    flags = [k for k in ("thrust_sag", "saturation", "weak_motor", "tel_loss", "tel_frozen") if f[k].get("on")]
    print(f'{g["run_index"]:3d} {g["mode"]:10s} {g["kind"]:10s} m{f["mass_scale"]["value"]:.2f} tau{f["tau_scale"]["value"]:.2f} '
          f'd{f["loop_delay"]["total_ms"]:.1f} w{f["wind"]["steady_ms"]:.1f}/{f["wind"]["gust_peak_total_ms"]:.1f} '
          f'{",".join(flags) or "-"} | {o} {str(out.get("error", ""))[:90]}')
for k, v in sorted(cnt.items()):
    print("COUNT", k, v)
