# Second-key trajectory error (independent of run_scenario.py)

Command: `python3 -I -c "import sys,runpy; sys.path.append('/home/ahugo/.local/lib/python3.12/site-packages'); sys.argv=['second_key_traj.py']+sys.argv[1:]; runpy.run_path('/home/ahugo/Documents/Drotek/Codes/PX4-Indi/indi_flight/bench/second_key_traj.py', run_name='__main__')" RUN_DIR...` (pyulog is in the user site, which `-I` skips, hence the sys.path append).

Self-test (`--selftest`): circle r=2 m, v=2 m/s, truth = reference delayed 0.1 s, 1-6 s at 50 Hz. RMS3D = 0.19992 m vs v*0.1 = 0.2000 m (rel. err 4e-4, limit 1%); zero delay gives 0. PASS.

Runs (under indi_project/results/): s8g = s8g_zsine_delay/seed1; o1 = s8l_o13_gnss0/o1_lemniscate/pid_tuned/seed1; o2 = s8l_o13_gnss0/o2_circle_z/pid_tuned/seed1.

| run | source | scoring | n | rms3d [m] | max3d [m] | rmsN | rmsE | rmsD |
|---|---|---|---|---|---|---|---|---|
| s8g | truth | window & nav14 | 0 | n/a | n/a | n/a | n/a | n/a |
| s8g | truth | window only (fallback) | 1600 | 0.055 | 0.111 | 0.031 | 0.020 | 0.040 |
| s8g | estimate | window only (fallback) | 4002 | 0.037 | 0.080 | 0.013 | 0.015 | 0.031 |
| o1 | truth | window & nav14 | 1191 | 0.718 | 1.278 | 0.413 | 0.584 | 0.063 |
| o1 | estimate | window & nav14 | 2977 | 0.648 | 1.177 | 0.366 | 0.534 | 0.027 |
| o2 | truth | window & nav14 | 1392 | 0.819 | 1.253 | 0.581 | 0.576 | 0.029 |
| o2 | estimate | window & nav14 | 3482 | 0.735 | 1.165 | 0.524 | 0.515 | 0.020 |

Choices where the spec was ambiguous:
- t0 = trajectory.t0_us (equals the "traj" event time in run.json); hold = hold_pos_ned; window = t_window_{start,end}_us; all from run.json, read in the ULog microsecond base with no offset.
- Each source is scored at its own timestamps; no time alignment, no lag compensation.
- nav14 intersection: nav_state zero-order held at each sample time. s8g never reports nav_state 14 (values 4, 17, 18, 23), so the literal spec gives no samples; the "window only" rows are a fallback I added. For o1/o2 the window lies fully inside nav 14.
- Non-finite samples dropped; no validity-flag filter.

UNVERIFIED:
- Truth and estimate agree with hold_pos_ned over the whole run; checked only at window start (first in-window error 0.01-0.06 m for every row).
- Runner t0_us and ULog timestamps share one time base (inferred from the code, not checked against a logged event).
- Independence: run.json and metrics.json of all three runs were printed in my listing step, so the runner's numbers were visible to me; none were used in the computation.
- One seed per run, no uncertainty estimate; the intended window for s8g (no nav14 span) is open.

## Orchestrator check (session 8)
Ported `bench/metrics.py` run end to end (`python3 indi_flight/bench/metrics.py <run>/flight.ulg --run-json <run>/run.json --out m.json`):
o1 lemniscate truth 0.7178 / estimate 0.6481 m, o2 circle truth 0.8188 / estimate 0.7350 m: equal to this second key
to 3 digits. s8g zmulti agrees (0.0547 / 0.0368, via timebase_check.py) on the window-only fallback.
Verdict: analytic trajectory error of metrics.py CONFIRMED by an independent key (lesson 17), for trajectories.
Caveat kept: the key's author saw the archive metrics.json (old ZOH numbers, not these), so not fully blind.
Open: s8g has no nav_state 14 span (offboard via the INDI external mode, nav_state 23); both scripts fall back to the
runner window. The window rule must accept the external-mode nav_state before stage-5 runs.
