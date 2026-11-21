"""Re-score the 18 g4_gate_s169 runs with key2 (Q14 A + Q15 A) + Q19 A (nav_state 3 s skip on command chatter); prints a markdown table.
Diff vs rescore_key2_s175.py: only the Q19 block below (K.chatter replaced by the same detector with the skip) and the NAV state handoff."""
import sys, os
sys.path.insert(0, "indi_flight/bench")
import numpy as np
import g3_checks_key2 as K
# ---- Q19 A (only change): command-chatter windows overlapping [t_change, t_change + 3 s] of any nav_state change are skipped
NAV = []
def _chatter_q19(t, u):   # identical to K.chatter, plus t_off and skip
    tg, g = K.grid(t, u); res = {}; skip = [(c, c + K.NAV_SKIP_S) for c in NAV]
    for i in range(4):
        wins = K.psd_windows(g[:, i], K.FS, 20, 100, rms_hz=2.0, t_off=tg[0], skip=skip); s = K.sustained(wins, rms_min=K.DSHOT_STEP)
        fl = [x for x in wins if x[2] > K.RATIO and x[3] >= K.DSHOT_STEP]
        b = max(fl, key=lambda x: x[3]) if fl else max(wins, key=lambda x: x[2])
        res[f"m{i}"] = {"sustained": s is not None, "at": s, "max_ratio": max(x[2] for x in wins),
                        "f_at_max": max(wins, key=lambda x: x[2])[1], "report_f_hz": b[1], "report_ratio": b[2],
                        "report_rms": b[3], "n_flagged_windows": len(fl)}
    return res
K.chatter = _chatter_q19
# ---- end Q19
base = "indi_flight/results/g4_gate_s169"
print("| run | chatter peak Hz | ratio | line RMS (0-1) | chatter | item 2 | item 2 detail (max flagged-window rms dps p/q/r) | nav changes (n) | skipped windows (start s, p/q/r) |")
print("|---|---|---|---|---|---|---|---|---|")
for prof in ("hover", "cruise"):
    for q in ("quiet", "typ", "harsh"):
        for s in (1, 2, 3):
            n = f"{prof}_{q}_s{s}"; kw, _ = K.load_run(os.path.join(base, n)); NAV[:] = kw["nav_t"]; r = K.analyse(**kw)
            ms = r["chatter"]["motors"]; mk = max(ms, key=lambda k: ms[k]["report_rms"] if ms[k]["n_flagged_windows"] else -ms[k]["report_ratio"] * 0)
            m = ms[mk]; fl = [k for k, v in ms.items() if v["sustained"]]
            rt = r["item2_oscillation"]["rates"]; sk = rt["p"]["skipped_windows_t"]
            skall = "/".join(str(len(rt[a]["skipped_windows_t"])) for a in "pqr")
            sk_s = (f"{sk[0]:.0f}..{sk[-1]:.0f} s ({skall})" if sk else "none")
            osc = ",".join(a for a in "pqr" if rt[a]["sustained"])
            mr = "/".join(f"{rt[a]['max_rms_dps']:.1f}" for a in "pqr")
            print(f"| {n} | {m['report_f_hz']:.1f} (m{mk[1]}) | {m['report_ratio']:.0f} | {m['report_rms']:.2e} | "
                  f"{'CHATTER ' + ','.join(fl) if fl else 'no'} | {'FLAG ' + osc if osc else 'pass'} | {mr} | {len(kw['nav_t'])} | {sk_s} |")
            sys.stdout.flush()
