# G5.5 horizontal-speed limit, independent computation (KEY2)

Method:
1. Reference position = `traj_pos(traj, traj_phase(traj, t))` at t = k/1000 s over the "traj" segment (0 to `_traj_dur(traj)`), horizontal (x, y) only.
2. Horizontal speed by central differences (dt = 1 ms, interior samples); v_rms = sqrt(mean(speed^2)) over the segment.
3. H_lim = max(0.5, 0.125 * v_rms). Script: /tmp/g55_key2/limit_key2.py (not in repo).

Functions used:
- `_traj_dur` at bench/scenarios.py:42 (duration; asserted equal to the "traj" segment length).
- `traj_phase` at bench/run_scenario.py:567 (ramp_s smoothstep phase).
- `traj_pos` at bench/run_scenario.py:585 (analytic position; the reference function is in run_scenario.py, not scenarios.py).

| scenario | traj duration s | v_rms m/s | H_lim m |
|---|---|---|---|
| o1_lemniscate | 17.8096 | 3.7112 | 0.5000 |
| o2_circle_z | 21.8496 | 4.5481 | 0.5685 |
| o6_zsine_mass | 18.0000 | 0.0000 | 0.5000 |

Notes: peak speeds check out (O1 6.000 m/s, O2 5.000 m/s, as documented in scenarios.py). O6 is a pure vertical multisine, so its horizontal speed is zero and H_lim falls to the 0.5 m floor.
