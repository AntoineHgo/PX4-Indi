# Item 3 decomposition, draw 262 (C3: sat 0.351 all motors, wind 1.66 m/s steady from 164.9 deg, sag)
Error = truth xy minus trajectory_setpoint median over window (g3_checks.load, same as scorer). Windows differ per log
(own chain_key1): s4 54.422, INDI s1 60.231, PID s1 60.711 (+3 s). Script: scratchpad it3.py.
Weak motor 2 thrust 0.990 (negligible, saturation scale 0.351 dominates). Gust onset 58.12/58.91/58.83 s = after window.
Steady wind present, gust not. Max actuator_motors in window 0.52 (no motor >= 0.99, no saturation); no sat flag read.

| log | window mean err (x,y) / mag m | fluct RMS m | total RMS m | max tilt deg | pre-10 s mean mag / fluct RMS |
|---|---|---|---|---|---|
| INDI s4 | (-0.007,+0.095) / 0.096 | 0.302 | 0.317 | 8.7 | 0.555 / 4.31 (transient) |
| INDI s1 | (+0.028,+0.123) / 0.126 | 0.282 | 0.308 | 8.5 | 0.530 / 4.29 (transient) |
| PID s1 | (+0.101,+0.055) / 0.115 | 0.076 | 0.138 | 3.6 | 0.595 / 3.74 (transient) |

Pre-window is the lemniscate-to-hold arrival (tilt 40-47 deg), not a hold: no steady state to compare there.
|e| in 0.5 s bins from 3 s before window start (INDI s4): 5.45 4.62 3.06 1.45 | window: 0.63 0.70 0.58 0.34 0.15 0.18
(INDI s1 near identical; PID s1: 0.59 | 0.15 0.17 0.19 0.16 0.12 0.07). Last 1.5 s of window RMS: INDI s4 0.185, s1 0.126, PID 0.083.
Post-window (0.7 s): INDI 0.04-0.07, PID 0.03.

Conclusion: mechanism class is slow convergence (settling tail of the arrival transient), not a steady offset and not wind
rejection: mean offsets are 0.10-0.13 m for all three (INDI not worse), the INDI excess is all in the fluctuating part, which is
the |e| decay 0.6 -> 0.15 m taking ~2 s for INDI vs ~0.5 s for PID. The window opens ~0.5 s after |e| passes 0.6 m, so it
catches INDI's tail; speed 1 vs 4 changes little (0.308 vs 0.317), so it is not a time-scale/sampling artefact.
Unverified: the INDI saturation flag was not read (only actuator_motors); wind-induced fluctuation is not excluded but the error
is monotone decaying, so I judge it small; the cause of INDI's slower final approach (position/velocity loop gains vs actuator lag
at 0.351 thrust scale) was not examined; one draw only.
