# CAUSE_S191: the INDI "2.0 Hz q line" on G3 pre-test runs 02, 05, 19 (logs + scorer code only, nothing flown)
Tools (new, tests in bench/tests): `bench/g3_line_trace_s191.py` (Hann-weighted LS amplitude/phase per signal on native samples), `bench/g3_win_detail_s191.py` (per-window detector table, key 1 and 2; needs scipy, run in px4-indi-sim). Logged rates: truth/gyro 800 Hz, attitude 267, local_position/setpoint/indi_pos_status 88.9 (no signal used above half its rate, no hold).
Clocks: key 1 = seconds since ulog start; key 2 = absolute (start + 13.3..13.9 s). Times below are since ulog start.

## 1. Draw factors (g3_draw.json, all 20 read; unc = true GNSS latency minus compensated ekf delay)
| run | lat/ekf ms | unc ms | mass | pitch I | tau up/dn | sag | wind st/peak m/s | vib x | note |
|---|---|---|---|---|---|---|---|---|---|
| 02 | 226/131 | +95 | 1.11 | 1.02 | .56/1.31 | .94 | 4.7/8.4 | 3.2 | |
| 05 | 186/102 | +84 | 1.19 | 1.22 | .77/1.41 | .83 | 2.1/3.3 | 4.2 | |
| 19 | 207/207 | 0 | 0.79 | 1.26 | .50/1.06 | none | 1.3/4.1 | 1.8 | |
| 03 | 168/148 | +20 | 0.75 | 1.02 | 2.43/2.79 | none | 2.2/3.8 | 1.2 | slowest motors of 20 |
| 15 pass | median | 0 | 1.05 | 1.09 | .57/1.08 | | 1.1/4.6 | 2.0 | ranges: unc -98..+59 |
- 02 and 05 are the two most under-compensated draws of 20 (unc +95, +84 ms); the largest in the 15 passing runs is +59 ms (run 10, stabilized mode), the rest are <= +37 or negative. This is the only factor where both sit at the extreme; mass, inertia, tau, wind, vibration, delay are not shared (02 wind peak 8.4 vs 05 3.3; loop delay 1.25 vs 0 ms).
- 19 is matched (unc 0): nothing shared with 02/05. Its flag is not the same event (see 2). 03: slow motors (tau 2.4-2.8x), unc +20: different mechanism likely (UNVERIFIED, not searched).
- 02/05 also have thrust sag (0.94, 0.83) and wind; 3 other sag+wind runs pass, so sag alone does not separate them.

## 2. Which loop oscillates (02, 05 logs, window 50-58 s, nav_state 14 offboard from 38.2 s; no nav change in 41-60 s)
- The line is NOT at 2.0 Hz. Both scorers search 2-40 Hz; the true q energy is 1.4-1.5 Hz (peak 1.45-1.5 Hz, plus 0.75 Hz and 2.0-2.6 Hz sidelobes) so argmax lands on the band floor, 2.0 Hz. Detector rms (+-2 bins) integrates 1.5-2.5 Hz. Reported "2.0 Hz" = band edge, not a measured frequency.
- Amplitudes at 1.45 Hz (LS, Hann): q 12.2 dps (02), 8.5 dps (05); pitch 1.31/0.96 deg (pitch lags q by 90 deg, i.e. q = d pitch/dt); pitch setpoint q_d 1.48/1.05 deg (phase -12/-19 deg vs q, i.e. leads pitch by ~79/69 deg); roll 0.6/0.3 deg.
- Outer loop: a_c (accel setpoint) 0.077/0.060 m/s2; vx 0.022/0.020 m/s; x 2.0/3.2 mm; trajectory_setpoint at 1.45 Hz 1.1/0.9 mm (reference is clean). But a_f (measured accel via R*f_b LPF) 0.235/0.182 m/s2, t_c 0.272/0.204 (= g*tilt: 9.81*1.31 deg = 0.22). a_f and t_c oscillate 3x more than a_c, a_c is the small residual, a_f phase +122/+121 deg vs q.
- So position/velocity/acceleration SETPOINTS are steady (mm, cm/s); the oscillation is the acceleration-feedback (a_f -> t_c -> q_d -> attitude/rate) loop of the INDI position stage, with position/velocity errors only 2-3 mm and 2 cm/s. Not an outer position-loop limit cycle. Earlier AF_TRACE_S189 showed a_f depends on stage-rate sampling; whether that sampling shapes this 1.45 Hz mode is UNVERIFIED.
- 19: key 1 flags 66.9-68.9 s only: q has a 59.5 dps single pulse at 69-70 s (nav_state 18 land at 69.5 s) and is <=1.1 dps before. A landing-switch transient, not an oscillation (peak 1.0-1.25 Hz wide, 3 windows 8.8/20/15.7 dps wide-band rms).

## 3. PID reference (g3_pretest_s187/pid_refs, same draw)
- 02 and 05 flown, no key-1/key-2 item-2 line. At 1.45 Hz (50-58 s): q 0.41/0.48 dps vs INDI 12.2/8.5 dps (x30, x18); a_sp 0.002/0.004 m/s2. 19 was NOT flown in pid_refs (pid_refs has runs 0,2,3,5,8,9,10,13,16,17), contrary to the briefing; INDI 19 passed in S188 (README).
- 03: PID q 2.5 Hz key 1 only (3 windows at t=46; key 2 none), INDI q 2.0 Hz both keys. Same axis, lines 2.0 vs 2.5 Hz; INDI's is again at the band floor. Spectrum 45-55 s: INDI q 1.2-3.5 Hz rms 10.9 dps, PID 0.9 dps, so INDI is much larger than PID's 03 line.
- 08: PID p 11.0 Hz (key 1 51 windows, key 2 p at 7.0 s, rms 205 dps); INDI q 10.75 Hz. Same frequency, DIFFERENT axis (p vs q).

## 4. Key 1 vs key 2
- 19: pure scope/skip difference. Key 1 scores to airborne end 75.4 s with skipped_windows 0 (g3_checks has NAV_SKIP only when --skip-nav-change is passed) and includes the landing pulse at 69.5 s: 3 flagged windows rms 6.8, 10.1, 6.0 dps vs 5 limit (min margin +20 %). Key 2 stops at t_land (span end 69.5 s) and skips windows overlapping 3 s after nav changes, so the pulse is excluded. Not a threshold-edge case.
- 02 item 2: threshold-edge. Same signal, windows offset by ~0.3 s. Key 1 windows 47.1 FLAG (5.3), 50.1 rms 4.9 (limit 5.0, -2 %), 51.1/52.1 FLAG (13.9/14.3), 53.1 peak jumps to 2.75 Hz rms 2.6, 54.1/55.1 FLAG (5.7/5.4), 56.1 rms 5.0 (-0 %, not flagged): never 3 consecutive, so no line. Key 2 windows 49.4-55.4 all flagged (5.2, 7.3, 15.7, 11.7, 6.8, 5.5, 5.2): 7 consecutive. A real ~1.5 Hz oscillation of 5-15 dps rms sitting at the 5 dps limit; verdict depends on window phase.
- 05: both keys flag (key 1 8 windows, rms 5.2-12.8). 

## Most likely cause
A lightly damped ~1.45 Hz mode of the INDI position-stage acceleration-feedback loop (a_f -> thrust vector -> attitude), excited during the lemniscate in 02 and 05, both of which carry the largest uncompensated GNSS latency of the batch (+95, +84 ms; 02 also the largest wind). Evidence: oscillation location in the loop = shown on log (a_f/t_c/q_d/q oscillate, setpoints and position error do not; PID same draw shows 18-30x less); "2.0 Hz" being the 2-Hz band floor = shown on log; link to the GNSS mismatch = consistent only (only shared extreme factor, n=2, no factor-isolating re-fly). 19 is a landing-transient artefact of key 1's scope, not this mode (shown on log). Unverified: that the uncompensated latency (rather than sag/wind/vibration) is causal; no run-with-matched-compensation test was made; item 3 PID values not checked.
