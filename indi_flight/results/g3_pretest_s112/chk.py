"""Per-run S112 checks. usage: chk.py RUN_DIR CSV_DIR (CSV_DIR = ulog2csv output)."""
import sys, json, csv, glob, os
import numpy as np
run, S = sys.argv[1], sys.argv[2]
def F(a, m, f):
    for n in (f"esc_{m}__{f}", f"esc{m}{f}", f"esc_{m}_{f}"):
        if n in a.dtype.names: return a[n]
    raise KeyError((m, f))
def L(n): return np.genfromtxt(f"{S}/flight_{n}_0.csv", delimiter=",", names=True)
r = json.load(open(f"{run}/run.json")); d = json.load(open(f"{run}/g3_draw.json"))
ov = d["build"]["overrides"]
print("exit", r["exit_status"], r["error"], "events", [(e["name"], e["t_us"]/1e6, e["dur_s"]) for e in r["events"]])
inj = r["disturbance"]["injector"] if r.get("disturbance") else None
print("injector", inj)
e = L("esc_status"); t = e["timestamp"]/1e6
print("esc rows", len(t), "t range", t[0], t[-1], "median dt", np.median(np.diff(t)))
el = ov.get("erpm_loss"); mf = ov.get("motor_fault")
anchor = [x for x in r["events"] if x["name"] == (el or {}).get("start", "traj")]
if el:
    m = el["motor"]; a = anchor[0]["t_us"]/1e6
    ts = F(e,m,"timestamp")/1e6
    rpm = F(e,m,"esc_rpm")
    print("erpm_loss drawn on", a+el["start_offset_s"], "dur", el["duration_s"], "run.json on/off", r["erpm_loss"]["on_us"]/1e6, r["erpm_loss"]["off_us"]/1e6)
    # frames of motor m: where its own timestamp advances
    ch = np.flatnonzero(np.diff(ts) > 0)+1
    tt = ts[ch]; dtm = np.diff(tt)
    big = np.flatnonzero(dtm > 3*np.median(dtm))
    print("motor", m, "frame median dt", np.median(dtm), "gaps >3x:", [(round(tt[i],3), round(tt[i+1],3), round(dtm[i],3)) for i in big][:8])
    z = (rpm == 0); print("rpm==0 frames", int(z.sum()))
    # other motors stay present
    for k in range(4):
        tk = F(e,k,"timestamp")/1e6; c = np.flatnonzero(np.diff(tk) > 0)+1; dk = np.diff(tk[c])
        print(" motor", k, "max frame gap", round(dk.max(), 4), "at", round(tk[c][np.argmax(dk)], 3))
if mf:
    for f in (mf if isinstance(mf, list) else [mf]):
        t0 = [x for x in r["events"] if x["name"] == f["segment"]][0]["t_us"]/1e6
        ao = L("actuator_outputs"); to = ao["timestamp"]/1e6
        for m in ([f["motor"]] if "motor" in f else f["motors"]):
            o = ao[f"output{m}"]
            pre = o[(to > t0-3) & (to < t0-0.2)]; post = o[(to > t0+0.5) & (to < t0+8)]
            ts_ = F(e,m,"timestamp")/1e6; rp = F(e,m,"esc_rpm")
            pr = rp[(t > t0-3) & (t < t0-0.2)]; po = rp[(t > t0+0.5) & (t < t0+8)]
            print("fault", f, "seg start", t0, "out max pre/post", pre.max(), post.max(), "rpm mean pre/post", pr.mean(), po.mean(), "rpm max pre/post", pr.max(), po.max())
    print("run.json motor_fault", json.dumps(r["motor_fault"])[:400])
sa = L("sim_schedule_applied")
print("sched applied rows", len(sa), "max |timestamp - t_sched| s", np.abs(sa["timestamp"]-sa["t_sched_us"]).max()/1e6, "anchor", set(sa["anchor_us"].tolist()))
if el:
    m = el["motor"]; ec = F(e,m,"esc_errorcount"); tm = F(e,m,"timestamp")/1e6
    # per-ms-window error fraction: errorcount increments per frame; loss = ~100 % of frames
    sel = t > 50; tt = t[sel]; de = np.diff(ec[sel]) > 0; tt = tt[1:]
    w = 0.1; edges = np.arange(tt[0], tt[-1], w); frac = np.array([de[(tt >= a_) & (tt < a_+w)].mean() for a_ in edges])
    hi = np.flatnonzero(frac > 0.8)
    print("motor", m, "overall err frac", de.mean(), "windows(0.1s) with >80% error frames:", len(hi))
    if len(hi):
        # contiguous
        st = [hi[0]]; en = []
        for a_, b_ in zip(hi[:-1], hi[1:]):
            if b_ != a_+1: en.append(a_); st.append(b_)
        en.append(hi[-1])
        for a_, b_ in zip(st, en):
            # refine at frame level: first/last frame with err in the run of consecutive-error frames
            lo, hi_t = edges[a_]-0.1, edges[b_]+w+0.1
            ids = np.flatnonzero(de & (tt >= lo) & (tt < hi_t)); 
            print("  loss window frames (first err frame, last err frame, len):", round(tt[ids[0]],4), round(tt[ids[-1]],4), round(tt[ids[-1]]-tt[ids[0]],4))
    for k in range(4):
        if k != m: 
            dk = np.diff(F(e,k,"esc_errorcount")[sel]) > 0; print(" other motor", k, "err frac", round(dk.mean(),4), "max frac 0.1s window", max(dk[(tt>=a_)&(tt<a_+w)].mean() for a_ in edges))
    print("drawn dropout prob", d["draw"]["factors"]["tel_dropout"]["prob"], "overall", d["draw"]["factors"]["tel_dropout"]["on"])
if el:
    # exact: runs of consecutive error frames of the lost motor (random drop at p<=0.3 never makes a run > ~20 frames)
    z = np.concatenate([[0], de.astype(int), [0]]); ix = np.flatnonzero(np.diff(z))
    runs = [(ix[i], ix[i+1]) for i in range(0, len(ix), 2)]
    big = [(tt[a_], tt[b_-1], b_-a_) for a_, b_ in runs if b_-a_ > 40]
    print("RUNS of >40 consecutive error frames:", [(round(a_,4), round(b_,4), n_) for a_, b_, n_ in big])
    a0 = [x for x in r["events"] if x["name"] == el["start"]][0]["t_us"]/1e6
    for a_, b_, n_ in big:
        print("  measured on-start - (anchor+offset) =", round(a_-(a0+el["start_offset_s"]),4), "s ; measured duration", round(b_-a_+0.00125,4), "vs drawn", el["duration_s"], "; frame period 0.00125")
if mf:
    R = np.array([F(e,k,"esc_rpm") for k in range(4)])
    for f in (mf if isinstance(mf, list) else [mf]):
        t0 = [x for x in r["events"] if x["name"] == f["segment"]][0]["t_us"]/1e6
        for a_, b_, l in ((t0-3, t0-0.2, "pre"), (t0+0.5, t0+17, "post")):
            s = (t > a_) & (t < b_); print("rpm", l, "mean/motor", R[:, s].mean(1).round(0), "max/motor", R[:, s].max(1))
        print("flight rpm max/motor (t>50)", R[:, t > 50].max(1)); break
    for k, v in sorted((q, v) for q, v in r.get("motor_fault", {}).items() if q in ("applied", "applied_all", "omega_ratio", "event_us", "event_done_us")): print("  run.json", k, v)
    pu = L("parameter_update")["timestamp"]/1e6; print("parameter_update times near events", [round(x, 4) for x in pu if x > 50])
if mf:
    ao = L("actuator_outputs"); to = ao["timestamp"]/1e6
    for f in (mf if isinstance(mf, list) else [mf]):
        t0 = [x for x in r["events"] if x["name"] == f["segment"]][0]["t_us"]/1e6; break
    for a_, b_, l in ((t0-3, t0-0.2, "pre"), (t0+0.5, t0+17, "post")):
        s = (t > a_) & (t < b_); so = (to > a_) & (to < b_)
        print("ratio rpm/output", l, [round(R[k, s].mean()/ao[f"output{k}"][so].mean(), 3) for k in range(4)], "output mean", [round(ao[f"output{k}"][so].mean(), 1) for k in range(4)])
if mf:
    am = L("actuator_motors"); ta = am["timestamp"]/1e6
    for a_, b_, l in ((t0-3, t0-0.2, "pre"), (t0+0.5, t0+17, "post")):
        s = (ta > a_) & (ta < b_)
        print("actuator_motors (normalised u) mean", l, [round(float(am[f"control{k}"][s].mean()), 4) for k in range(4)], "max", [round(float(am[f"control{k}"][s].max()), 3) for k in range(4)])
import math
dc = list(csv.DictReader(open(f"{run}/disturbance.csv")))
w = ov.get("wind")
if w and dc:
    ts_ = np.array([float(x["sim_time_s"]) for x in dc]); fx = np.array([float(x["fx"]) for x in dc]); fy = np.array([float(x["fy"]) for x in dc])
    on = r["disturbance"]["onset_us"]/1e6
    s = (ts_ > on+4) & (ts_ < on+9)   # steady plateau (2 s ramp then 10 s hold)
    mx, my = fx[s].mean(), fy[s].mean()
    print("WIND drawn dir_deg", w["dir_deg"], "steady", w["steady"], "peak", w["peak"], "| measured force dir_deg", round(math.degrees(math.atan2(my, mx)) % 360, 2), "|F| steady", round(math.hypot(mx, my), 4), "N; max |F|", round(float(np.hypot(fx, fy).max()), 4), "; expected 0.5*rho*CdA*w^2 = |F|/w^2 =", round(math.hypot(mx, my)/w["steady"]**2, 5), "; peak ratio", round(float(np.hypot(fx, fy).max())/math.hypot(mx, my), 3), "vs (peak/steady)^2", round((w["peak"]/w["steady"])**2, 3))
