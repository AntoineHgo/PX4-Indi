#!/usr/bin/env python3
"""S186 knob sweep for g3_osc_margins: which single quantity restores attitude PM >= 30 deg at the worst corner. Analysis only."""
import numpy as np
import g3_osc_margins as G

TM = [0.5, 1, 2, 3, 6, 9]
ES = [0.5, 0.75, 1, 1.5, 2]


def box_att(over, tm_max=3):
    """min att PM and min rate PM over e in ES, tau mult in TM<=tm_max, 10 ms, 2 frames; and the corner e=2/tau=tm_max."""
    worst_a, worst_r, arg = 999, 999, None
    for e in ES:
        for t in TM:
            if t > tm_max:
                continue
            c = G.cfg(e * over.get("gs", 1.0), G.TAU0 * t, 10.0, 2, **{k: v for k, v in over.items() if k != "gs"})
            m = G.margins(c)
            if m["rate"]["pm"] <= 0:  # rate loop itself unstable (fast-motor high-f corner): att PM meaningless, counted in worst_r
                worst_r = min(worst_r, m["rate"]["pm"])
                continue
            if m["att"]["pm"] < worst_a:
                worst_a, arg = m["att"]["pm"], (e, t)
            worst_r = min(worst_r, m["rate"]["pm"])
    return worst_a, arg, worst_r


def nominal(over):
    gs = over.get("gs", 1.0)
    m = G.margins(G.cfg(1.0 * gs, G.TAU0, 0.0, 0, **{k: v for k, v in over.items() if k != "gs"}))
    return "rate PM %.0f fc %.1f Hz | att PM %.0f fc %.2f Hz" % (m["rate"]["pm"], m["rate"]["fc"], m["att"]["pm"], m["att"]["fc"])


print("grid att PM, delay 10ms, 2 frames, tau (rotor, down) mult up to 9")
for e in ES:
    print(e, [round(G.margins(G.cfg(e, G.TAU0 * t, 10.0, 2))["att"]["pm"]) for t in TM])
print("baseline", box_att({}), nominal({}))
print("baseline tau<=9", box_att({}, 9))
for name, vals in (("att_p", [8, 6, 5, 4.5, 4, 3, 2.5, 2]), ("K", [20, 15, 12, 10, 8]), ("act_tc", [0.033, 0.02, 0.01, 0.005]),
                   ("gs", [1, 0.8, 0.6, 0.5])):
    for v in vals:
        o = {name: v}
        a, arg, r = box_att(o)
        a9, arg9, _ = box_att(o, 9)
        print(name, v, "box<=3x: att PM %.0f at e/tau %s, rate PM(ex fast corner) %.0f | box<=9x att %.0f %s | nominal %s" % (
            a, arg, r, a9, arg9, nominal(o)))
