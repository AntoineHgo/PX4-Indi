# S76: rate-loop margins vs rate blend (D-RATE-BLD precondition 1)

Roll-axis M3a loop-gain injection (torque-setpoint break, D-G2-BREAK), `hover_long`, quad5in, 800 Hz, seed 1,
speed 4, firmware at `head.txt` (built by `fly.sh`). Params: S57 measured-path config
(`results/stage3_s57/roll_m3a_meas800/meas800.params`) + `MC_INDI_ACT_BLD` tb. Resume: `bash fly.sh` from repo root.
Analysis: `bench/m3a_csv.py` + `bench/m3a_margins_pretest.py csv 1 60 10 800` (18/18 bins accepted in each flight).

| tb [s] | PM [deg] | f_c [Hz] | GM [dB] | f_180 [Hz] | DM [ms] | Ms [dB] |
|---|---|---|---|---|---|---|
| 1.0 | 68.5 | 4.15 | 15.7 | 23.6 | 45.9 | 2.35 |
| 0.3 | 68.4 | 4.18 | 16.0 | 23.8 | 45.5 | 2.33 |
| 0.1 | 68.2 | 4.37 | 16.0 | 23.7 | 43.3 | 2.32 |
| S57 ref (no blend) | 77.5 | 3.08 | 16.6 | 25.0 | 69.8 | - |

G2 thresholds (GM >= 6 dB, PM >= 45 deg, DM >= 2 periods + telemetry latency) met at every tb, with wide margin.
The blend constant has no measurable effect on the rate-loop margin: its corner (0.16-1.6 Hz) sits below the 4 Hz
crossover. The stage-1 0.1 s crash is therefore not explained by a rate-loop margin at hover on this airframe;
candidate causes remain outside this test (x500 plant, model mismatch, telemetry edges settled in D-RATE-BLD-EDGE).

Caveats. (a) `bld*_gate.md` FAIL "rate RMS axis 0 0.135" is a set-up artefact: the gate window (airborne +15 s,
30 s long) overlaps the injection (DLY 20 s); y/z RMS 0.0024/0.0006 rad/s. S57 ran the gate on a pre-injection
window. (b) One seed, roll only, 800 Hz only; 400 Hz and the D-GAP velocity-break items are still to fly.
(c) PM 68 vs 77 deg and f_c 4.1 vs 3.1 Hz against S57 with the same params apart from tb: logged as A-34.
