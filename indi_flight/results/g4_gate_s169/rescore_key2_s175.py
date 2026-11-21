"""Re-score the 18 g4_gate_s169 runs with key2 (Q14 A + Q15 A); prints a markdown table."""
import sys, os
sys.path.insert(0, "indi_flight/bench")
import numpy as np
import g3_checks_key2 as K
base = "indi_flight/results/g4_gate_s169"
print("| run | chatter peak Hz | ratio | line RMS (0-1) | chatter | item 2 | item 2 detail (max flagged-window rms dps p/q/r) | nav changes (n) | skipped windows (start s, p/q/r) |")
print("|---|---|---|---|---|---|---|---|---|")
for prof in ("hover", "cruise"):
    for q in ("quiet", "typ", "harsh"):
        for s in (1, 2, 3):
            n = f"{prof}_{q}_s{s}"; kw, _ = K.load_run(os.path.join(base, n)); r = K.analyse(**kw)
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
