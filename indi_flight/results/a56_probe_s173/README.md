# A-56 discriminating probe (S173): is the INDI outer loop's measured-acceleration path the cause?

Probe (not gate evidence). Firmware aa4fd2654a (D-JFF-OFFB), freeze params `g5_freeze_s157/params.params` with one
change per config, harsh hover (`--vib-acc 27 --vib-gyr 0 --imu-noise-scale 4.0`), matched GNSS 110 ms, seeds 1-3,
serial. No truth-acceleration substitution hook exists in mc_indi_pos_control (the "truth hook inst 1" of RC173 is
the true rotor speed, esc_status inst 1), so the outer loop was removed instead (pos0) and its accel filter tightened
(lpf4). Fly: `sh indi_flight/results/a56_probe_s173/fly.sh`; score (Docker): `analyse.sh` (same computation as
g4_jffoffb_s172; g3_checks rc 1 = FAIL verdict, driven by the chatter clause in every run).

| config | change | item 2 sustained (axis, freq, window) | flagged windows p/q (s1, s2, s3) |
|---|---|---|---|
| baseline (g4_jffoffb_s172) | none | s3: p 2.0 Hz, ~93.5 s | - |
| pos0 | MC_INDI_POS_EN 0 (stock mc_pos_control, INDI rate loop) | s3: q 2.0 Hz, window 81 | 3/2, 0/3, 1/3 |
| lpf4 | MC_INDI_POS_LPF 4.0 (was 10) | s3: q 2.0 Hz, window 82 | 3/0, 3/2, 0/3 |

lpf4 descent q std (deg/s): 2.5, 5.9, 14.5 (baseline 1.9, 13.9, 0.4). pos0 descent q std not computed (omega_offb.py
needs indi_rate_feedforward, absent without the INDI position module). Item 1 (LOC) PASS 6/6.

Reading: the 2 Hz oscillation near AUTO_LAND entry persists with the stock position controller, at the same seed and
flight time. The INDI outer loop (its measured-acceleration path, D-GAP blend, rate FF) is NOT the cause. PID (stock
rate + stock pos) does not show it (A-56 row). Remaining INDI element in the pos0 stack: the INDI rate loop (with the
stock attitude loop). Next: the decision underneath is the inner loop's low-frequency behaviour (RC173 branch "both
oscillate -> G2 cells at 2 Hz": read the freeze G2 attitude/rate loop data at 1.5-3 Hz).
