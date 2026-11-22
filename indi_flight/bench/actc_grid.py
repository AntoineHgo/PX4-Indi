#!/usr/bin/env python3
"""ACT_TC identification error grid (design/actc_ident_s208.md "SITL error measurement", GATES 6c).

One identification flight per cell on quad5in (MC_INDI_ID_OK 0, params-only, firmware multisine injector as in
results/ident_m3a_s123/pos0), then bench/ident_actc.py on the log. Writes <out>/GRID.tsv and <out>/<cell>/run.json.
Plant: --model-variant tau_up=k,tau_down=k (multiples of the stock 0.033 s), --dly-act MS, param SIM_GZ_ERPM_LAT (NOT effective, see params_text).
Resumable: a cell with run.json status "done" is skipped. Cell id: t<tau_slow factor>_a<asym><d|u>_d<ms>f<frames>_s<seed>.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
TAU0 = 0.033
RPM_MAX = 2700 * 60 / 6.283185307  # SIM_GZ_EC_MAX1 2700 rad/s in rpm; the logs carry no rpm_max param; only scales the fitted gain
BASE_PARAMS = os.path.join(REPO, "indi_flight/results/ident_m3a_s123/inj_pos0.params")  # G1/G2Y, RATE_CTL_TYPE 1, POS_EN 0, injector
FIELDS = ["cell", "tau_slow", "asym", "dir", "dly_ms", "frames", "seed", "true_up", "true_down", "true_mean", "true_slow",
          "est_up", "est_down", "est_sym", "est_delay_ms", "pass", "flags", "sym_over_slow", "sym_over_mean", "residual", "status"]


def cell(tau, asym, direction, dly, fr, seed):
    return dict(tau=tau, asym=asym, dir=direction if asym > 1 else "-", dly=dly, frames=fr, seed=seed)


def grid():
    g = []
    for tau in (0.5, 1, 2, 3):
        for asym, d in ((1, "d"), (3, "d"), (3, "u")):
            for dly, fr in ((0, 0), (10, 3)):
                g.append(cell(tau, asym, d, dly, fr, 1))
    for tau in (0.5, 3):
        for dly, fr in ((0, 0), (10, 3)):
            g.append(cell(tau, 3, "d", dly, fr, 2))
    g += [cell(1, 3, "d", 0, 3, 1), cell(1, 3, "d", 10, 0, 1)]
    return g


def cid(c):
    return f"t{c['tau']}_a{c['asym']}{c['dir'] if c['asym'] > 1 else ''}_d{c['dly']}f{c['frames']}_s{c['seed']}"


def truth(c):
    slow = c["tau"] * TAU0
    fast = slow / c["asym"]
    up, dn = (fast, slow) if c["dir"] == "d" else (slow, fast) if c["dir"] == "u" else (slow, slow)
    return up, dn


def params_text(c, axis):
    t = open(BASE_PARAMS).read().rstrip("\n").splitlines()
    t = [l for l in t if not l.startswith(("MC_INDI_INJ_AX", "#"))]
    # WARNING (S209 pre-test): gz_bridge reads SIM_GZ_ERPM_LAT only at construction, a params file is applied after boot, so this
    # line has NO effect (estimated delay unchanged, 1.75 ms at 3 frames vs 1.82 at 0). Only a scenario "sim_params" entry
    # (PX4_PARAM_ env at boot) works; run_scenario has no CLI for it. Frames are therefore not applied by this driver.
    t += [f"MC_INDI_INJ_AX {axis}", "MC_INDI_ID_OK 0", f"SIM_GZ_ERPM_LAT {c['frames']}"]
    return "\n".join(t) + "\n"


def commands(c, out, axis, speed, tmo):
    up, dn = truth(c)
    d = os.path.join(out, cid(c))
    rel = lambda p: os.path.relpath(p, REPO)
    argv = ["python3", "indi_flight/bench/run_scenario.py", "--scenario", "hover", "--controller", "indi_m3a", "--model", "quad5in",
            "--seed", str(c["seed"]), "--sim-seed", str(c["seed"]), "--speed", str(speed), "--sim", "v2",
            "--params", rel(os.path.join(d, "inj.params")), "--out", rel(d),
            "--model-variant", f"tau_up={up / TAU0:g},tau_down={dn / TAU0:g}"]
    if c["dly"]:
        argv += ["--dly-act", str(c["dly"])]
    run = ["indi_project/docker/run.sh", "-n", "actcgrid_" + cid(c).replace(".", "p"), "-t", str(tmo), "--"] + argv
    ident = ["python3", "indi_flight/bench/ident_actc.py", rel(os.path.join(d, "flight.ulg")), "--json", rel(os.path.join(d, "ident.json")), "--rpm-max", f"{RPM_MAX:.0f}"]
    return d, run, ident


def fly(c, out, a):
    d, run, ident = commands(c, out, a.axis, a.speed, a.timeout)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "inj.params"), "w").write(params_text(c, a.axis))
    up, dn = truth(c)
    rec = dict(cell=cid(c), spec=c, true=dict(tau_up=up, tau_down=dn), run_cmd=run, ident_cmd=ident + [f"--t0={a.t0}", f"--t1={a.t1}"],
               status="started", t_start=time.time())
    try:
        p = subprocess.run(run, cwd=REPO, capture_output=True, text=True, timeout=a.timeout + 60)
        rec["run_rc"] = p.returncode
        open(os.path.join(d, "runner.out"), "w").write(p.stdout[-20000:] + p.stderr[-5000:])
    except subprocess.TimeoutExpired:
        rec["status"] = "timeout"
        subprocess.run(["docker", "rm", "-f", run[2]], capture_output=True)
    rec["wall_s"] = time.time() - rec["t_start"]
    if rec["status"] != "timeout":
        if not os.path.exists(os.path.join(d, "flight.ulg")):
            rec["status"] = "no_log"
        else:
            p = subprocess.run(ident + [f"--t0={a.t0}", f"--t1={a.t1}"], cwd=REPO, capture_output=True, text=True)
            rec["ident_rc"], rec["ident_out"] = p.returncode, p.stdout[-2000:]
            rec["status"] = "done" if os.path.exists(os.path.join(d, "ident.json")) else "ident_failed"
    json.dump(rec, open(os.path.join(d, "run.json"), "w"), indent=1)
    return rec


def row(c, out):
    up, dn = truth(c)
    mean, slow = (up + dn) / 2, max(up, dn)
    r = dict(cell=cid(c), tau_slow=c["tau"], asym=c["asym"], dir=c["dir"], dly_ms=c["dly"], frames=c["frames"], seed=c["seed"],
             true_up=up, true_down=dn, true_mean=mean, true_slow=slow, status="missing")
    d = os.path.join(out, cid(c))
    try:
        r["status"] = json.load(open(os.path.join(d, "run.json")))["status"]
        m = json.load(open(os.path.join(d, "ident.json")))["median"]
        r.update(est_up=m["tau_up"], est_down=m["tau_down"], est_sym=m["tau_sym"], est_delay_ms=m["delay_ms"], residual=m["residual"],
                 sym_over_slow=m["tau_sym"] / slow, sym_over_mean=m["tau_sym"] / mean, **{"pass": int(m["pass"])})
        flags = sorted({f for x in json.load(open(os.path.join(d, "ident.json")))["motors"] for f in x["flags"]})
        r["flags"] = ",".join(flags)
    except (OSError, KeyError, ValueError):
        pass
    return r


def write_tsv(cells, out):
    with open(os.path.join(out, "GRID.tsv"), "w") as f:
        f.write("\t".join(FIELDS) + "\n")
        for c in cells:
            r = row(c, out)
            f.write("\t".join("" if r.get(k) is None else (f"{r[k]:.5g}" if isinstance(r[k], float) else str(r[k])) for k in FIELDS) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cells", default="all", help="'all', 'pretest', comma list of cell ids, or index range like 0-5 / 3,7 (see --list)")
    ap.add_argument("--list", action="store_true", help="print the 30 cells and exit")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=420, help="wall-clock timeout per flight, s (container -t and subprocess)")
    ap.add_argument("--speed", type=float, default=4.0)
    ap.add_argument("--axis", type=int, default=1, choices=(1, 2), help="injector axis, 1 roll (as pos0), 2 pitch")
    ap.add_argument("--t0", type=float, default=24.0, help="ident window start, log s (injection starts ~20.6)")
    ap.add_argument("--t1", type=float, default=76.0)
    a = ap.parse_args()
    allc = grid()
    if a.list:
        for i, c in enumerate(allc):
            up, dn = truth(c)
            print(i, cid(c), f"up {1e3 * up:.1f} down {1e3 * dn:.1f} ms")
        return 0
    if a.cells == "all":
        sel = allc
    elif a.cells == "pretest":
        sel = [cell(1, 1, "-", 0, 0, 1), cell(3, 3, "d", 10, 3, 1)]
    else:
        idx = []
        for tok in a.cells.split(","):
            if tok.isdigit():
                idx.append(int(tok))
            elif "-" in tok and all(x.isdigit() for x in tok.split("-")):
                lo, hi = map(int, tok.split("-"))
                idx += range(lo, hi + 1)
            else:
                idx += [i for i, c in enumerate(allc) if cid(c) == tok]
        sel = [allc[i] for i in idx]
    out = os.path.abspath(a.out)
    for c in sel:
        d, run, ident = commands(c, out, a.axis, a.speed, a.timeout)
        if a.dry_run:
            print(cid(c), "\n  ", " ".join(run), "\n  ", " ".join(ident), f"--t0={a.t0} --t1={a.t1}")
            continue
        try:
            if json.load(open(os.path.join(d, "run.json")))["status"] == "done":
                print("skip", cid(c))
                continue
        except (OSError, ValueError, KeyError):
            pass
        rec = fly(c, out, a)
        print(cid(c), rec["status"], f"{rec['wall_s']:.0f} s", rec.get("ident_out", "").strip().splitlines()[-1:] or "", flush=True)
        write_tsv(allc, out)
    if not a.dry_run:
        write_tsv(allc, out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
