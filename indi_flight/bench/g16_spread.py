"""Same-seed spread of metrics.json numeric leaves over r1..r5 per scenario (host python, stdlib only)."""
import glob, json, math, os, sys, statistics
ROOT = os.environ.get("G16_ROOT", "/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/results/det_g16")
SKIP = {"seed", "speed"}
def leaves(x, p=""):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from leaves(v, p + "." + k if p else k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from leaves(v, "%s[%d]" % (p, i))
    elif isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x):
        yield p, float(x)
result = {}
for sc in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, sc)
    if not os.path.isdir(d):
        continue
    runs = sorted(glob.glob(os.path.join(d, "r[0-9]")))
    per = {}
    used = []
    for r in runs:
        mp = os.path.join(r, "metrics.json")
        if not os.path.exists(mp):
            continue
        used.append(os.path.basename(r))
        for p, v in leaves(json.load(open(mp))):
            if p.split(".")[0] in SKIP:
                continue
            per.setdefault(p, {})[os.path.basename(r)] = v
    n = len(used)
    rows = {}
    for p, vals in per.items():
        if len(vals) != n or n == 0:
            continue  # leaf not present in every run
        v = [vals[k] for k in used]
        mean = statistics.fmean(v)
        mn, mx = min(v), max(v)
        spread = mx - mn
        rel = spread / abs(mean) if mean != 0 else float("nan")
        rows[p] = dict(mean=mean, min=mn, max=mx, spread=spread, rel=rel, ill=abs(mean) < 1e-3, n=n, vals=v)
    result[sc] = dict(runs=used, rows=rows)
json.dump(result, open(os.environ.get("G16_SPREAD_OUT", os.path.join(ROOT, "spread.json")), "w"), indent=1)
def fmt(x):
    return "nan" if x != x else "%.4g" % x
if __name__ == "__main__" and "--table" in sys.argv:
    sc = sys.argv[sys.argv.index("--table") + 1]
    res = result[sc]
    print("| leaf | mean | min | max | abs spread | rel spread | ILL |")
    print("|---|---|---|---|---|---|---|")
    for p, r in res["rows"].items():
        print("| %s | %s | %s | %s | %s | %s | %s |" % (p, fmt(r["mean"]), fmt(r["min"]), fmt(r["max"]),
              fmt(r["spread"]), fmt(r["rel"]), "ILL" if r["ill"] else ""))
else:
    for sc, res in result.items():
        print(sc, "runs:", res["runs"], "leaves:", len(res["rows"]), "ILL:", sum(r["ill"] for r in res["rows"].values()))
