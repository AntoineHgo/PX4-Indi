import sys; sys.path.insert(0,"indi_flight/bench/tests"); sys.path.insert(0,"indi_flight/bench")
import test_g3_checks as T, g3_checks as G, numpy as np
kw=dict(line_hz=60.0, line_amp=0.0004*np.sqrt(2), cmd_noise=2e-5)
G.CMD_LINE_RMS=0.0
print("chat_lowrms, RMS clause removed -> item2 pass:", T.make(**kw)["item2_oscillation"]["pass"], "(expect False = break caught)")
G.CMD_LINE_RMS=5e-4; G.NAV_SKIP_S=1e6
r=T.make(osc_hz=30.0, osc_dps=8.0, osc_from=70.0, osc_until=73.0, nav_changes=[60.0])
print("burst_later, skip everything -> item2 pass:", r["item2_oscillation"]["pass"], "(expect True = break caught)")
